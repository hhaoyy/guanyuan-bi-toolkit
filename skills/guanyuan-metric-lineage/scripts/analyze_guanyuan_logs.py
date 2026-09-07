#!/usr/bin/env python3
"""Analyze one or more Guanyuan HAR files and build a combined output index."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug or "guanyuan-dashboard"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def merge_hars(paths: list[Path]) -> Path:
    merged_log: dict[str, Any] = {"version": "1.2", "creator": {"name": "guanyuan-metric-lineage", "version": "1"}}
    merged_entries: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            har = json.load(handle)
        log = har.get("log") if isinstance(har.get("log"), dict) else {}
        entries = log.get("entries")
        if not isinstance(entries, list):
            raise SystemExit(f"Invalid HAR: {path} has no log.entries list.")
        if not merged_log.get("pages") and isinstance(log.get("pages"), list):
            merged_log["pages"] = log["pages"]
        merged_entries.extend(entry for entry in entries if isinstance(entry, dict))
    merged_log["entries"] = merged_entries
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".har",
        prefix="guanyuan-merged-",
        encoding="utf-8",
        delete=False,
    )
    with handle:
        json.dump({"log": merged_log}, handle, ensure_ascii=False)
    return Path(handle.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Guanyuan network logs.")
    parser.add_argument("har", nargs="+", type=Path, help="One or more HAR files")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--ignore-card", action="append", default=[])
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge all HAR entries before parsing. Use for runtime/edit captures of the same dashboard.",
    )
    args = parser.parse_args()

    parser_script = Path(__file__).with_name("parse_guanyuan_har.py")
    args.output_root.mkdir(parents=True, exist_ok=True)
    combined_rows: list[dict[str, str]] = []
    analyses: list[dict[str, Any]] = []
    used_slugs: set[str] = set()
    merged_temp = None

    if args.merge:
        merged_temp = merge_hars(args.har)
        source_label = "+".join(path.name for path in args.har)
        jobs = [(merged_temp, source_label, slugify(f"{args.har[0].stem}-merged"))]
    else:
        jobs = [(path, path.name, slugify(path.stem)) for path in args.har]

    for index, (har_path, source_label, base_slug) in enumerate(jobs, start=1):
        slug = base_slug
        if slug in used_slugs:
            slug = f"{slug}-{index}"
        used_slugs.add(slug)
        result_root = args.output_root / slug
        docs_dir = result_root / "docs"
        data_dir = result_root / "data"
        command = [
            sys.executable,
            str(parser_script),
            str(har_path),
            "--docs-dir",
            str(docs_dir),
            "--out-dir",
            str(data_dir),
            "--source-label",
            source_label,
        ]
        for card_name in args.ignore_card:
            command.extend(["--ignore-card", card_name])
        completed = subprocess.run(command, check=True, text=True, capture_output=True)
        summary = json.loads(completed.stdout)
        rows = read_csv(data_dir / "field_lineage.csv")
        for row in rows:
            row["analysis_slug"] = slug
            row["har_file"] = source_label
        combined_rows.extend(rows)
        analyses.append(
            {
                "slug": slug,
                "har_file": source_label,
                "page_name": summary.get("page_name"),
                "card_count": summary.get("card_count"),
                "field_count": summary.get("field_lineage_count"),
                "confirmed_count": summary.get("confirmed_source_field_count"),
                "warehouse_trace_count": summary.get("warehouse_trace_required_count"),
            }
        )

    if merged_temp:
        merged_temp.unlink(missing_ok=True)

    write_csv(args.output_root / "combined_field_lineage.csv", combined_rows)
    lines = [
        "# 观远指标与血缘解析索引",
        "",
        "| 看板 | HAR | 卡片数 | 字段引用 | 已确认源表/SQL | 需追数仓 | 结果目录 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in analyses:
        lines.append(
            "| {page_name} | `{har_file}` | {card_count} | {field_count} | {confirmed_count} | {warehouse_trace_count} | `./{slug}/` |".format(
                **item
            )
        )
    lines += [
        "",
        "跨 HAR 合并明细：`combined_field_lineage.csv`。",
        "每个看板目录内包含 `docs/` 人工报告和 `data/` 结构化结果。",
    ]
    (args.output_root / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"analyses": analyses, "output_root": str(args.output_root)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
