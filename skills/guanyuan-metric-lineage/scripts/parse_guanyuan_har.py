#!/usr/bin/env python3
"""Extract Guanyuan dashboard configuration from a HAR file.

This parser intentionally ignores request/response headers, cookies, and auth
tokens. It only reads JSON response bodies that contain page/card/dataset config.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


IGNORED_CARD_NAMES: set[str] = set()


def as_text(value: Any, max_len: int = 240) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def md_cell(value: Any, max_len: int = 180) -> str:
    text = as_text(value, max_len=max_len)
    return text.replace("|", "\\|")


def field_label(field: dict[str, Any]) -> str:
    name = field.get("alias") or field.get("name") or field.get("fdId") or ""
    raw = field.get("name")
    if field.get("alias") and raw and raw != field.get("alias"):
        return f"{field.get('alias')} ({raw})"
    return str(name)


def field_expr(field: dict[str, Any]) -> str:
    formula = field.get("formula")
    if formula:
        return as_text(formula, 500)
    aggr = field.get("aggrType")
    name = field.get("name") or field.get("alias") or field.get("fdId")
    if aggr and aggr != "NUL":
        return f"{aggr}({name})"
    return str(name or "")


def dataset_source_info(dataset: dict[str, Any]) -> dict[str, Any]:
    config = dataset.get("config") if isinstance(dataset.get("config"), dict) else {}
    table_query = config.get("tableQuery") if isinstance(config.get("tableQuery"), dict) else {}
    realtime = config.get("realTimeUpdateSetting") if isinstance(config.get("realTimeUpdateSetting"), dict) else {}
    incremental = (
        config.get("guanIndexIncrementalUpdateSetting")
        if isinstance(config.get("guanIndexIncrementalUpdateSetting"), dict)
        else {}
    )
    return {
        "connection_id": dataset.get("cnId"),
        "account_id": dataset.get("acId"),
        "storage_id": dataset.get("storageId"),
        "source_type": config.get("sourceType"),
        "storage_type": config.get("storageType"),
        "query_type": table_query.get("queryType"),
        "source_table": table_query.get("table"),
        "source_query": table_query.get("query"),
        "pre_sql": table_query.get("preSql"),
        "is_basic_select_form": table_query.get("isBasicSelectForm"),
        "has_escape": table_query.get("hasEscape"),
        "enable_schedule": config.get("enableSchedule"),
        "task_id": config.get("taskId"),
        "last_execution": config.get("lastExecution"),
        "datasource_modify_time": config.get("datasourceModifyTime"),
        "realtime_update_enabled": realtime.get("enabled"),
        "incremental_update_enabled": incremental.get("enabled"),
        "dynamic_parameters": config.get("dynamicParameters"),
    }


def extract_sql_tables(sql: Any) -> list[str]:
    """Extract directly referenced FROM/JOIN tables without claiming full SQL lineage."""
    if not sql:
        return []
    text = re.sub(r"/\*.*?\*/", " ", str(sql), flags=re.S)
    text = re.sub(r"--[^\n]*", " ", text)
    matches = re.findall(
        r"\b(?:from|join)\s+([`\"\[]?[A-Za-z_][\w$]*(?:\.[`\"\[]?[A-Za-z_][\w$]*){0,2})",
        text,
        flags=re.I,
    )
    tables: list[str] = []
    for match in matches:
        table = match.replace("`", "").replace('"', "").replace("[", "").replace("]", "")
        if table.lower() not in {"select", "unnest"} and table not in tables:
            tables.append(table)
    return tables


def zone(card: dict[str, Any]) -> dict[str, Any]:
    content = card.get("content") if isinstance(card.get("content"), dict) else {}
    meta = content.get("meta") if isinstance(content.get("meta"), dict) else {}
    chart_main = meta.get("chartMain") if isinstance(meta.get("chartMain"), dict) else {}
    return chart_main.get("zoneData") if isinstance(chart_main.get("zoneData"), dict) else {}


def load_har(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return json.load(fh)


def find_page_config(har: dict[str, Any]) -> tuple[dict[str, Any], str]:
    candidates: list[tuple[int, dict[str, Any], str]] = []
    for entry in har.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = request.get("url", "")
        path = urlparse(url).path
        text = response.get("content", {}).get("text") or ""
        if not text.strip().startswith("{"):
            continue
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("cards"), list) and isinstance(obj.get("dsInfos"), list):
            candidates.append((len(text), obj, path))
    if not candidates:
        raise SystemExit("No Guanyuan page config found in HAR responses.")
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, page, path = candidates[0]
    return page, path


def collect_runtime_requests(
    har: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
]:
    selector_data: dict[str, dict[str, Any]] = {}
    field_value_data: dict[str, dict[str, Any]] = {}
    dynamic_params: dict[str, dict[str, Any]] = {}
    custom_requests: list[dict[str, Any]] = []
    custom_edits: list[dict[str, Any]] = []
    for entry in har.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        response = entry.get("response", {})
        path = urlparse(request.get("url", "")).path
        response_text = response.get("content", {}).get("text") or ""
        request_text = (request.get("postData") or {}).get("text") or ""

        if "/api/selector/" in path and path.endswith("/data"):
            selector_id = path.split("/")[3]
            values: list[str] = []
            count = ""
            try:
                obj = json.loads(response_text) if response_text.strip().startswith("{") else {}
                payload = obj.get("response") if isinstance(obj, dict) else {}
                result = payload.get("result") if isinstance(payload, dict) else []
                count = payload.get("count", "")
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "value" in item:
                            values.append(as_text(item.get("value"), 120))
                        else:
                            values.append(as_text(item, 120))
            except json.JSONDecodeError:
                pass
            selector_data[selector_id] = {
                "selector_id": selector_id,
                "option_count": count if count != "" else len(values),
                "options": values,
                "request_path": path,
            }

        if path == "/api/ds-info/columns/values-with-display":
            try:
                req_obj = json.loads(request_text) if request_text.strip().startswith("{") else {}
                resp_obj = json.loads(response_text) if response_text.strip().startswith("{") else {}
            except json.JSONDecodeError:
                req_obj = {}
                resp_obj = {}
            field_query = req_obj.get("fieldQuery") if isinstance(req_obj.get("fieldQuery"), dict) else {}
            field_name = field_query.get("name")
            if field_name:
                payload = resp_obj.get("response") if isinstance(resp_obj, dict) else {}
                result = payload.get("result") if isinstance(payload, dict) else []
                values = []
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "value" in item:
                            values.append(as_text(item.get("value"), 120))
                        else:
                            values.append(as_text(item, 120))
                field_value_data[field_name] = {
                    "field_name": field_name,
                    "dataset_id": req_obj.get("dsId") or field_query.get("dsId"),
                    "field_id": field_query.get("fdId"),
                    "field_type": field_query.get("fdType"),
                    "meta_type": field_query.get("metaType"),
                    "formula": field_query.get("formula"),
                    "calculation_type": field_query.get("calculationType"),
                    "option_count": payload.get("count", len(values)) if isinstance(payload, dict) else len(values),
                    "options": values,
                    "request_path": path,
                }

        if path == "/api/dynamic-parameter/query":
            try:
                obj = json.loads(response_text) if response_text.strip().startswith("{") else {}
            except json.JSONDecodeError:
                obj = {}
            response_items = obj.get("response") if isinstance(obj, dict) else []
            if isinstance(response_items, list):
                for item in response_items:
                    if isinstance(item, dict) and item.get("name"):
                        dynamic_params[item["name"]] = {
                            "name": item.get("name"),
                            "dp_id": item.get("dpId"),
                            "value_type": item.get("valueType"),
                            "default_value": item.get("defaultValue"),
                            "multiple": item.get("multiple"),
                            "options": [as_text(v, 120) for v in (item.get("optionValue") or [])],
                            "request_path": path,
                        }

        if "/api/complex-report-pro/" in path and path.endswith("/data"):
            card_id = path.split("/")[3]
            request_json: Any = {}
            try:
                request_json = json.loads(request_text) if request_text.strip().startswith("{") else {}
            except json.JSONDecodeError:
                request_json = {}
            custom_requests.append(
                {
                    "card_id": card_id,
                    "request_path": path,
                    "response_mime": response.get("content", {}).get("mimeType", ""),
                    "response_text_chars": len(response_text),
                    "response_size": response.get("content", {}).get("size", ""),
                    "request_name": request_json.get("name") if isinstance(request_json, dict) else "",
                    "child_filters": request_json.get("childFilters") if isinstance(request_json, dict) else {},
                    "dynamic_params": request_json.get("dynamicParams") if isinstance(request_json, dict) else [],
                    "request_body": request_json,
                }
            )

        if path.startswith("/api/card/") and path.endswith("/edit") and response_text.strip().startswith("{"):
            try:
                obj = json.loads(response_text)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("cdType") == "CUSTOM":
                custom_edits.append(
                    {
                        "card_id": obj.get("cdId"),
                        "card_name": obj.get("name"),
                        "content": obj.get("content") if isinstance(obj.get("content"), dict) else {},
                        "children": obj.get("children") if isinstance(obj.get("children"), list) else [],
                        "request_path": path,
                    }
                )
    return selector_data, custom_requests, field_value_data, dynamic_params, custom_edits


def collect_formulas(obj: Any, path: str = "$") -> list[dict[str, str]]:
    formulas: list[dict[str, str]] = []
    if isinstance(obj, dict):
        formula = obj.get("formula")
        if formula:
            formulas.append(
                {
                    "path": path,
                    "name": as_text(obj.get("alias") or obj.get("name") or obj.get("fdId"), 120),
                    "formula": as_text(formula, 1000),
                    "meta_type": as_text(obj.get("metaType"), 80),
                    "fd_type": as_text(obj.get("fdType"), 80),
                }
            )
        for key, value in obj.items():
            formulas.extend(collect_formulas(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            formulas.extend(collect_formulas(value, f"{path}[{index}]"))
    return formulas


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Guanyuan HAR dashboard config.")
    parser.add_argument("har", type=Path, help="Path to HAR file")
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument("--out-dir", type=Path, default=Path("raw/guanyuan/extracted"))
    parser.add_argument("--source-label", help="Display label for merged or renamed HAR input.")
    parser.add_argument(
        "--ignore-card",
        action="append",
        default=[],
        help="Exact card name to exclude. Repeat the option to exclude multiple cards.",
    )
    args = parser.parse_args()

    har = load_har(args.har)
    page, page_api_path = find_page_config(har)
    selector_runtime, custom_runtime, field_value_runtime, dynamic_params, custom_edit_runtime = collect_runtime_requests(har)

    docs_dir = args.docs_dir
    out_dir = args.out_dir
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    ignored_card_names = IGNORED_CARD_NAMES | set(args.ignore_card)
    cards = [
        card
        for card in (page.get("cards") or [])
        if isinstance(card, dict) and card.get("name") not in ignored_card_names
    ]
    datasets = page.get("dsInfos") or []
    dataset_by_id = {ds.get("dsId"): ds for ds in datasets if isinstance(ds, dict)}
    card_by_id = {card.get("cdId"): card for card in cards if isinstance(card, dict)}

    card_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    filter_rows: list[dict[str, Any]] = []
    custom_runtime_rows: list[dict[str, Any]] = []
    custom_edit_rows: list[dict[str, Any]] = []
    dataset_rows: list[dict[str, Any]] = []
    column_rows: list[dict[str, Any]] = []
    field_rows: list[dict[str, Any]] = []
    formulas = collect_formulas(page)
    unique_formulas = sorted({item["formula"] for item in formulas})

    for index, card in enumerate(cards, start=1):
        content = card.get("content") if isinstance(card.get("content"), dict) else {}
        settings = card.get("settings") if isinstance(card.get("settings"), dict) else {}
        zdata = zone(card)
        ds_id = content.get("dsId") or card.get("dsId")
        ds_name = (dataset_by_id.get(ds_id) or {}).get("name", "")
        row_fields = zdata.get("row") or []
        col_fields = zdata.get("column") or []
        metric_fields = zdata.get("metric") or []
        filter_fields = zdata.get("filters") or []
        sorting_fields = zdata.get("sorting") or []
        card_rows.append(
            {
                "index": index,
                "card_id": card.get("cdId"),
                "card_name": card.get("name"),
                "card_type": card.get("cdType"),
                "chart_type": content.get("chartType", ""),
                "dataset_id": ds_id,
                "dataset_name": ds_name,
                "row_fields": "; ".join(field_label(item) for item in row_fields if isinstance(item, dict)),
                "column_fields": "; ".join(field_label(item) for item in col_fields if isinstance(item, dict)),
                "metric_fields": "; ".join(field_label(item) for item in metric_fields if isinstance(item, dict)),
                "filter_count": len(filter_fields),
                "sort_count": len(sorting_fields),
                "show_title": settings.get("showTitle", ""),
            }
        )
        field_groups = [
            ("row_dimension", row_fields),
            ("column_dimension", col_fields),
            ("metric", metric_fields),
            ("card_filter", filter_fields),
            ("sorting", sorting_fields),
        ]
        for field_role, fields in field_groups:
            for field in fields:
                if not isinstance(field, dict):
                    continue
                field_rows.append(
                    {
                        "dashboard_name": page.get("name"),
                        "dashboard_id": page.get("pgId"),
                        "card_id": card.get("cdId"),
                        "card_name": card.get("name"),
                        "card_type": card.get("cdType"),
                        "chart_type": content.get("chartType", ""),
                        "field_role": field_role,
                        "field_id": field.get("fdId"),
                        "field_name": field.get("alias") or field.get("name") or field.get("fdId"),
                        "source_field": field.get("name"),
                        "dataset_id": ds_id,
                        "dataset_name": ds_name,
                        "aggr_type": field.get("aggrType"),
                        "calculation_type": field.get("calculationType"),
                        "card_formula": str(field.get("formula") or ""),
                        "expression": field_expr(field),
                    }
                )
        for metric in metric_fields:
            if not isinstance(metric, dict):
                continue
            metric_rows.append(
                {
                    "card_id": card.get("cdId"),
                    "card_name": card.get("name"),
                    "dataset_id": ds_id,
                    "dataset_name": ds_name,
                    "metric_name": metric.get("alias") or metric.get("name") or metric.get("fdId"),
                    "source_field": metric.get("name"),
                    "meta_type": metric.get("metaType"),
                    "fd_type": metric.get("fdType"),
                    "aggr_type": metric.get("aggrType"),
                    "calculation_type": metric.get("calculationType"),
                    "is_aggregated": metric.get("isAggregated"),
                    "formula": str(metric.get("formula") or ""),
                    "expression": field_expr(metric),
                }
            )
        if card.get("cdType") == "SELECTOR":
            as_filter = settings.get("asFilter") if isinstance(settings.get("asFilter"), dict) else {}
            mappings = as_filter.get("columnMappings") or []
            runtime = selector_runtime.get(card.get("cdId"), {})
            field_runtime = field_value_runtime.get(card.get("name"), {})
            dynamic_runtime = dynamic_params.get(card.get("name"), {})
            options = runtime.get("options") or []
            if not options and field_runtime.get("options"):
                options = field_runtime.get("options") or []
            if not options and dynamic_runtime.get("options"):
                options = dynamic_runtime.get("options") or []
            runtime_option_count = runtime.get("option_count", "")
            option_count = runtime_option_count
            if option_count == "" and field_runtime.get("option_count", "") != "":
                option_count = field_runtime.get("option_count", "")
            if option_count == "" and dynamic_runtime.get("options"):
                option_count = len(dynamic_runtime.get("options") or [])
            inferred_source_field = field_runtime.get("field_name") or (
                f"DYNAMIC_PARAMS.{dynamic_runtime.get('name')}" if dynamic_runtime else ""
            )
            inferred_source_dataset_id = field_runtime.get("dataset_id", "")
            inferred_source_dataset_name = (dataset_by_id.get(inferred_source_dataset_id) or {}).get("name", "")
            inferred_formula = field_runtime.get("formula", "")
            if not mappings:
                filter_rows.append(
                    {
                        "selector_id": card.get("cdId"),
                        "selector_name": card.get("name"),
                        "source_field": inferred_source_field,
                        "source_dataset_id": inferred_source_dataset_id,
                        "source_dataset_name": inferred_source_dataset_name,
                        "target_count": len(as_filter.get("targetCdIds") or []),
                        "target_cards": "; ".join(
                            as_text((card_by_id.get(cid) or {}).get("name"), 80)
                            for cid in (as_filter.get("targetCdIds") or [])
                        ),
                        "target_fields": "",
                        "auto_link": as_filter.get("autoLink", ""),
                        "option_count": option_count,
                        "options_sample": "; ".join(options[:30]),
                        "selector_data_path": runtime.get("request_path", ""),
                        "source_formula": as_text(inferred_formula, 1000),
                        "dynamic_default": dynamic_runtime.get("default_value", ""),
                    }
                )
            for mapping in mappings:
                source = mapping.get("sourceField") if isinstance(mapping.get("sourceField"), dict) else {}
                targets = mapping.get("targetFields") or []
                source_ds = dataset_by_id.get(source.get("dsId")) or {}
                filter_rows.append(
                    {
                        "selector_id": card.get("cdId"),
                        "selector_name": card.get("name"),
                        "source_field": source.get("name"),
                        "source_dataset_id": source.get("dsId", ""),
                        "source_dataset_name": source_ds.get("name", ""),
                        "target_count": len(targets),
                        "target_cards": "; ".join(
                            as_text((card_by_id.get(target.get("cdId")) or {}).get("name"), 80)
                            for target in targets
                            if isinstance(target, dict)
                        ),
                        "target_fields": "; ".join(
                            f"{target.get('name')}@{(dataset_by_id.get(target.get('dsId')) or {}).get('name', target.get('dsId', ''))}"
                            for target in targets
                            if isinstance(target, dict)
                        ),
                        "auto_link": as_filter.get("autoLink", ""),
                        "option_count": option_count,
                        "options_sample": "; ".join(options[:30]),
                        "selector_data_path": runtime.get("request_path", ""),
                        "source_formula": as_text(inferred_formula or source.get("formula"), 1000),
                        "dynamic_default": dynamic_runtime.get("default_value", ""),
                    }
                )

    for item in custom_runtime:
        card = card_by_id.get(item.get("card_id")) or {}
        custom_runtime_rows.append(
            {
                "card_id": item.get("card_id"),
                "card_name": card.get("name") or item.get("request_name"),
                "request_path": item.get("request_path"),
                "response_mime": item.get("response_mime"),
                "response_text_chars": item.get("response_text_chars"),
                "response_size": item.get("response_size"),
                "child_filters": as_text(item.get("child_filters"), 2000),
                "dynamic_params": as_text(item.get("dynamic_params"), 1000),
            }
        )

    for item in custom_edit_runtime:
        for child_index, child in enumerate(item.get("children") or [], start=1):
            content = child.get("content") if isinstance(child.get("content"), dict) else {}
            ds_id = content.get("dsId") or child.get("dsId")
            ds_info = child.get("dsInfo") if isinstance(child.get("dsInfo"), dict) else {}
            ds_name = (dataset_by_id.get(ds_id) or {}).get("name") or ds_info.get("name", "")
            zdata = zone(child)
            row_fields = zdata.get("row") or []
            col_fields = zdata.get("column") or []
            metric_fields = zdata.get("metric") or []
            filter_fields = zdata.get("filters") or []
            custom_edit_rows.append(
                {
                    "custom_card_id": item.get("card_id"),
                    "custom_card_name": item.get("card_name"),
                    "child_index": child_index,
                    "child_card_id": child.get("cdId"),
                    "child_card_name": child.get("name"),
                    "chart_type": content.get("chartType", ""),
                    "dataset_id": ds_id,
                    "dataset_name": ds_name,
                    "row_fields": "; ".join(field_label(field) for field in row_fields if isinstance(field, dict)),
                    "column_fields": "; ".join(field_label(field) for field in col_fields if isinstance(field, dict)),
                    "metric_fields": "; ".join(field_label(field) for field in metric_fields if isinstance(field, dict)),
                    "metric_expressions": "; ".join(
                        f"{field_label(field)}={field_expr(field)}" for field in metric_fields if isinstance(field, dict)
                    ),
                    "filters": as_text(filter_fields, 2000),
                    "edit_path": item.get("request_path"),
                }
            )
            child_field_groups = [
                ("custom_row_dimension", row_fields),
                ("custom_column_dimension", col_fields),
                ("custom_metric", metric_fields),
                ("custom_card_filter", filter_fields),
            ]
            for field_role, fields in child_field_groups:
                for field in fields:
                    if not isinstance(field, dict):
                        continue
                    field_rows.append(
                        {
                            "dashboard_name": page.get("name"),
                            "dashboard_id": page.get("pgId"),
                            "card_id": child.get("cdId") or item.get("card_id"),
                            "card_name": f"{item.get('card_name')} / {child.get('name')}",
                            "card_type": "CUSTOM_CHILD",
                            "chart_type": content.get("chartType", ""),
                            "field_role": field_role,
                            "field_id": field.get("fdId"),
                            "field_name": field.get("alias") or field.get("name") or field.get("fdId"),
                            "source_field": field.get("name"),
                            "dataset_id": ds_id,
                            "dataset_name": ds_name,
                            "aggr_type": field.get("aggrType"),
                            "calculation_type": field.get("calculationType"),
                            "card_formula": str(field.get("formula") or ""),
                            "expression": field_expr(field),
                        }
                    )

    card_usage_by_dataset = Counter(row["dataset_id"] for row in card_rows if row.get("dataset_id"))
    metric_usage_by_dataset = Counter(row["dataset_id"] for row in metric_rows if row.get("dataset_id"))
    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue
        columns = dataset.get("columns") or []
        formula_columns = [col for col in columns if isinstance(col, dict) and col.get("formula")]
        source_info = dataset_source_info(dataset)
        dataset_rows.append(
            {
                "dataset_id": dataset.get("dsId"),
                "dataset_name": dataset.get("name"),
                "display_type": dataset.get("displayType"),
                "column_count": len(columns),
                "formula_column_count": len(formula_columns),
                "row_count": dataset.get("rowCount"),
                "card_usage_count": card_usage_by_dataset.get(dataset.get("dsId"), 0),
                "metric_usage_count": metric_usage_by_dataset.get(dataset.get("dsId"), 0),
                "dir_path": as_text(dataset.get("dirPath"), 300),
                "description": as_text(dataset.get("description"), 300),
                "connection_id": source_info.get("connection_id"),
                "account_id": source_info.get("account_id"),
                "source_type": source_info.get("source_type"),
                "storage_type": source_info.get("storage_type"),
                "query_type": source_info.get("query_type"),
                "source_table": source_info.get("source_table"),
                "source_query": str(source_info.get("source_query") or ""),
                "is_basic_select_form": source_info.get("is_basic_select_form"),
                "enable_schedule": source_info.get("enable_schedule"),
                "task_id": source_info.get("task_id"),
                "last_execution": source_info.get("last_execution"),
                "datasource_modify_time": source_info.get("datasource_modify_time"),
                "realtime_update_enabled": source_info.get("realtime_update_enabled"),
                "incremental_update_enabled": source_info.get("incremental_update_enabled"),
                "dynamic_parameters": as_text(source_info.get("dynamic_parameters"), 1000),
            }
        )
        for column in columns:
            if not isinstance(column, dict):
                continue
            column_rows.append(
                {
                    "dataset_id": dataset.get("dsId"),
                    "dataset_name": dataset.get("name"),
                    "field_id": column.get("fdId"),
                    "field_name": column.get("name"),
                    "field_type": column.get("fdType"),
                    "meta_type": column.get("metaType"),
                    "calculation_type": column.get("calculationType"),
                    "is_aggregated": column.get("isAggregated"),
                    "formula": str(column.get("formula") or ""),
                    "annotation": as_text(column.get("annotation"), 500),
                }
            )

    dataset_row_by_id = {row.get("dataset_id"): row for row in dataset_rows}
    column_by_id = {
        (row.get("dataset_id"), row.get("field_id")): row
        for row in column_rows
        if row.get("field_id")
    }
    column_by_name = {
        (row.get("dataset_id"), row.get("field_name")): row
        for row in column_rows
        if row.get("field_name")
    }
    for row in field_rows:
        dataset_row = dataset_row_by_id.get(row.get("dataset_id"), {})
        dataset_column = (
            column_by_id.get((row.get("dataset_id"), row.get("field_id")))
            or column_by_name.get((row.get("dataset_id"), row.get("source_field")))
            or {}
        )
        dataset_formula = dataset_column.get("formula", "")
        card_formula = row.get("card_formula", "")
        expression = row.get("expression", "")
        if card_formula:
            calculation_layer = "guanyuan_card"
            calculation_logic = card_formula
        elif dataset_formula:
            calculation_layer = "guanyuan_dataset"
            calculation_logic = dataset_formula
        elif row.get("aggr_type") and row.get("aggr_type") != "NUL":
            calculation_layer = "guanyuan_aggregation"
            calculation_logic = expression
        else:
            calculation_layer = "warehouse_or_source_field"
            calculation_logic = expression or row.get("source_field", "")

        source_table = dataset_row.get("source_table", "")
        source_sql = dataset_row.get("source_query", "")
        upstream_tables = extract_sql_tables(source_sql)
        if source_table and source_table not in upstream_tables:
            upstream_tables.insert(0, source_table)

        if not row.get("dataset_id"):
            evidence_level = "missing"
            evidence_note = "Card field has no dataset identifier in the captured configuration."
        elif source_table or source_sql:
            evidence_level = "confirmed_guanyuan"
            evidence_note = "Dataset source table or SQL was captured from Guanyuan configuration."
        else:
            evidence_level = "partial"
            evidence_note = "Field and dataset are captured, but the dataset source table or SQL is absent."

        requires_warehouse_trace = calculation_layer == "warehouse_or_source_field"
        if calculation_layer == "guanyuan_aggregation" and re.fullmatch(
            r"(?i)(sum|count|min|max|avg)\([^()]+\)", str(calculation_logic).strip()
        ):
            requires_warehouse_trace = True

        row.update(
            {
                "dataset_formula": dataset_formula,
                "calculation_layer": calculation_layer,
                "calculation_logic": calculation_logic,
                "source_type": dataset_row.get("source_type", ""),
                "query_type": dataset_row.get("query_type", ""),
                "source_table": source_table,
                "source_sql": source_sql,
                "upstream_tables": "; ".join(upstream_tables),
                "evidence_level": evidence_level,
                "evidence_note": evidence_note,
                "requires_warehouse_trace": str(requires_warehouse_trace).lower(),
            }
        )
    deduplicated_fields: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in field_rows:
        key = (
            row.get("dashboard_id"),
            row.get("card_id"),
            row.get("card_name"),
            row.get("field_role"),
            row.get("field_id"),
            row.get("field_name"),
            row.get("source_field"),
            row.get("dataset_id"),
            row.get("calculation_logic"),
        )
        deduplicated_fields.setdefault(key, row)
    field_rows = list(deduplicated_fields.values())

    write_csv(
        out_dir / "card_inventory.csv",
        card_rows,
        [
            "index",
            "card_id",
            "card_name",
            "card_type",
            "chart_type",
            "dataset_id",
            "dataset_name",
            "row_fields",
            "column_fields",
            "metric_fields",
            "filter_count",
            "sort_count",
            "show_title",
        ],
    )
    write_csv(
        out_dir / "filter_inventory.csv",
        filter_rows,
        [
            "selector_id",
            "selector_name",
            "source_field",
            "source_dataset_id",
            "source_dataset_name",
            "target_count",
            "target_cards",
            "target_fields",
            "auto_link",
            "option_count",
            "options_sample",
            "selector_data_path",
            "source_formula",
            "dynamic_default",
        ],
    )
    write_csv(
        out_dir / "custom_runtime_requests.csv",
        custom_runtime_rows,
        [
            "card_id",
            "card_name",
            "request_path",
            "response_mime",
            "response_text_chars",
            "response_size",
            "child_filters",
            "dynamic_params",
        ],
    )
    write_csv(
        out_dir / "custom_edit_children.csv",
        custom_edit_rows,
        [
            "custom_card_id",
            "custom_card_name",
            "child_index",
            "child_card_id",
            "child_card_name",
            "chart_type",
            "dataset_id",
            "dataset_name",
            "row_fields",
            "column_fields",
            "metric_fields",
            "metric_expressions",
            "filters",
            "edit_path",
        ],
    )
    write_csv(
        out_dir / "dataset_inventory.csv",
        dataset_rows,
        [
            "dataset_id",
            "dataset_name",
            "display_type",
            "column_count",
            "formula_column_count",
            "row_count",
            "card_usage_count",
            "metric_usage_count",
            "dir_path",
            "description",
            "connection_id",
            "account_id",
            "source_type",
            "storage_type",
            "query_type",
            "source_table",
            "source_query",
            "is_basic_select_form",
            "enable_schedule",
            "task_id",
            "last_execution",
            "datasource_modify_time",
            "realtime_update_enabled",
            "incremental_update_enabled",
            "dynamic_parameters",
        ],
    )
    write_csv(
        out_dir / "dataset_columns.csv",
        column_rows,
        [
            "dataset_id",
            "dataset_name",
            "field_id",
            "field_name",
            "field_type",
            "meta_type",
            "calculation_type",
            "is_aggregated",
            "formula",
            "annotation",
        ],
    )
    write_csv(
        out_dir / "metric_inventory.csv",
        metric_rows,
        [
            "card_id",
            "card_name",
            "dataset_id",
            "dataset_name",
            "metric_name",
            "source_field",
            "meta_type",
            "fd_type",
            "aggr_type",
            "calculation_type",
            "is_aggregated",
            "formula",
            "expression",
        ],
    )
    write_csv(
        out_dir / "field_lineage.csv",
        field_rows,
        [
            "dashboard_name",
            "dashboard_id",
            "card_id",
            "card_name",
            "card_type",
            "chart_type",
            "field_role",
            "field_id",
            "field_name",
            "source_field",
            "dataset_id",
            "dataset_name",
            "aggr_type",
            "calculation_type",
            "card_formula",
            "dataset_formula",
            "expression",
            "calculation_layer",
            "calculation_logic",
            "source_type",
            "query_type",
            "source_table",
            "source_sql",
            "upstream_tables",
            "evidence_level",
            "evidence_note",
            "requires_warehouse_trace",
        ],
    )

    summary = {
        "har_file": args.source_label or args.har.name,
        "page_api_path": page_api_path,
        "page_id": page.get("pgId"),
        "page_name": page.get("name"),
        "card_count": len(cards),
        "selector_count": sum(1 for card in cards if card.get("cdType") == "SELECTOR"),
        "dataset_count": len(datasets),
        "row_zone_item_count": sum(
            len(zone(card).get("row") or []) for card in cards if isinstance(card, dict)
        ),
        "column_zone_item_count": sum(
            len(zone(card).get("column") or []) for card in cards if isinstance(card, dict)
        ),
        "metric_zone_item_count": len(metric_rows),
        "card_filter_item_count": sum(
            len(zone(card).get("filters") or []) for card in cards if isinstance(card, dict)
        ),
        "formula_occurrence_count": len(formulas),
        "unique_formula_count": len(unique_formulas),
        "field_lineage_count": len(field_rows),
        "confirmed_source_field_count": sum(
            1 for row in field_rows if row.get("evidence_level") == "confirmed_guanyuan"
        ),
        "warehouse_trace_required_count": sum(
            1 for row in field_rows if row.get("requires_warehouse_trace") == "true"
        ),
        "ignored_cards": sorted(ignored_card_names),
    }
    (out_dir / "page_config_summary.json").write_text(
        json.dumps({"summary": summary, "unique_formulas": unique_formulas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    chart_type_counts = Counter(row["chart_type"] or row["card_type"] for row in card_rows)
    dataset_usage = defaultdict(list)
    for row in card_rows:
        if row.get("dataset_name"):
            dataset_usage[row["dataset_name"]].append(row["card_name"])

    (docs_dir / "dashboard_inventory.md").write_text(
        render_dashboard_inventory(page, summary, card_rows, chart_type_counts),
        encoding="utf-8",
    )
    (docs_dir / "filter_inventory.md").write_text(
        render_filter_inventory(page, summary, filter_rows),
        encoding="utf-8",
    )
    (docs_dir / "custom_card_runtime.md").write_text(
        render_custom_card_runtime(page, summary, custom_runtime_rows),
        encoding="utf-8",
    )
    (docs_dir / "custom_card_edit_inventory.md").write_text(
        render_custom_card_edit_inventory(page, summary, custom_edit_rows),
        encoding="utf-8",
    )
    (docs_dir / "dataset_mapping.md").write_text(
        render_dataset_mapping(page, summary, dataset_rows, column_rows, dataset_usage),
        encoding="utf-8",
    )
    (docs_dir / "dataset_source_mapping.md").write_text(
        render_dataset_source_mapping(page, summary, dataset_rows),
        encoding="utf-8",
    )
    (docs_dir / "metrics_dictionary.md").write_text(
        render_metrics_dictionary(page, summary, metric_rows, formulas),
        encoding="utf-8",
    )
    (docs_dir / "metric_lineage.md").write_text(
        render_metric_lineage(summary, field_rows),
        encoding="utf-8",
    )
    (docs_dir / "coverage_report.md").write_text(
        render_coverage_report(summary, field_rows, dataset_rows, custom_runtime_rows, custom_edit_rows),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def render_dashboard_inventory(
    page: dict[str, Any],
    summary: dict[str, Any],
    card_rows: list[dict[str, Any]],
    chart_type_counts: Counter,
) -> str:
    lines = [
        "# 观远看板资产清单",
        "",
        "## 解析摘要",
        "",
        f"- HAR 文件：`{summary['har_file']}`",
        f"- 看板名称：`{summary['page_name']}`",
        f"- 看板 ID：`{summary['page_id']}`",
        f"- 看板配置接口：`{summary['page_api_path']}`",
        f"- 卡片数：`{summary['card_count']}`",
        f"- 筛选器卡片数：`{summary['selector_count']}`",
        f"- 数据集数：`{summary['dataset_count']}`",
        f"- 指标字段项：`{summary['metric_zone_item_count']}`",
        f"- 行维度字段项：`{summary['row_zone_item_count']}`",
        f"- 列维度字段项：`{summary['column_zone_item_count']}`",
        f"- 卡片内过滤条件项：`{summary['card_filter_item_count']}`",
        f"- 公式出现次数：`{summary['formula_occurrence_count']}`",
        f"- 去重公式数：`{summary['unique_formula_count']}`",
        "",
        "## 图表类型分布",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ]
    for chart_type, count in chart_type_counts.most_common():
        lines.append(f"| `{md_cell(chart_type)}` | {count} |")
    lines += [
        "",
        "## 卡片清单",
        "",
        "| # | 卡片名称 | 卡片类型 | 图表类型 | 数据集 | 行维度 | 列维度 | 指标 | 过滤数 |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in card_rows:
        lines.append(
            "| {index} | {card_name} | `{card_type}` | `{chart_type}` | {dataset_name} | {row_fields} | {column_fields} | {metric_fields} | {filter_count} |".format(
                index=row["index"],
                card_name=md_cell(row["card_name"]),
                card_type=md_cell(row["card_type"]),
                chart_type=md_cell(row["chart_type"]),
                dataset_name=md_cell(row["dataset_name"]),
                row_fields=md_cell(row["row_fields"], 220),
                column_fields=md_cell(row["column_fields"], 160),
                metric_fields=md_cell(row["metric_fields"], 260),
                filter_count=row["filter_count"],
            )
        )
    lines += [
        "",
        "## 解析说明",
        "",
        "- 本文件来自 HAR 中的观远页面配置接口，不包含请求头、Cookie 或 token。",
        "- 卡片业务含义仍需结合人工标注确认。",
        "- 卡片中的公式只代表观远层配置，若字段来自数仓结果表，仍需继续追 SQL 血缘。",
    ]
    return "\n".join(lines) + "\n"


def render_filter_inventory(page: dict[str, Any], summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# 观远筛选器清单",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 筛选器记录数：`{len(rows)}`",
        "",
        "| 筛选器 | 源字段 | 源数据集 | 目标数 | 目标卡片 | 目标字段 | 可选值数 | 可选值样例 | 来源公式/默认值 | 自动关联 |",
        "| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        source_note = row.get("source_formula") or (
            f"default={row.get('dynamic_default')}" if row.get("dynamic_default") else ""
        )
        lines.append(
            "| {selector_name} | `{source_field}` | {source_dataset_name} | {target_count} | {target_cards} | {target_fields} | {option_count} | {options_sample} | {source_note} | `{auto_link}` |".format(
                selector_name=md_cell(row["selector_name"]),
                source_field=md_cell(row["source_field"]),
                source_dataset_name=md_cell(row["source_dataset_name"]),
                target_count=row["target_count"],
                target_cards=md_cell(row["target_cards"], 320),
                target_fields=md_cell(row["target_fields"], 320),
                option_count=md_cell(row.get("option_count")),
                options_sample=md_cell(row.get("options_sample"), 320),
                source_note=md_cell(source_note, 420),
                auto_link=md_cell(row["auto_link"]),
            )
        )
    lines += [
        "",
        "## 待人工确认",
        "",
        "- `target_count = 0` 表示未捕获显式联动目标，不能据此判定没有联动；需要补采配置并核验。",
        "- 筛选器的业务解释、时间语义和联动行为需要另行核验。",
    ]
    return "\n".join(lines) + "\n"


def render_custom_card_edit_inventory(
    page: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# 观远自定义卡片编辑页清单",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 捕获到编辑页子卡片：`{len(rows)}`",
        "",
        "| 自定义卡片 | 子卡片 | 图表类型 | 数据集 | 行维度 | 列维度 | 指标 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {custom_card_name} | {child_card_name} | `{chart_type}` | {dataset_name} | {row_fields} | {column_fields} | {metric_fields} |".format(
                custom_card_name=md_cell(row.get("custom_card_name")),
                child_card_name=md_cell(row.get("child_card_name")),
                chart_type=md_cell(row.get("chart_type")),
                dataset_name=md_cell(row.get("dataset_name")),
                row_fields=md_cell(row.get("row_fields"), 260),
                column_fields=md_cell(row.get("column_fields"), 180),
                metric_fields=md_cell(row.get("metric_fields"), 420),
            )
        )
    lines += [
        "",
        "## 指标表达式",
        "",
    ]
    for row in rows:
        lines += [
            f"### {row.get('custom_card_name')} / {row.get('child_card_name')}",
            "",
            f"- 数据集：`{row.get('dataset_name')}`",
            f"- 编辑接口：`{row.get('edit_path')}`",
            "",
            "```text",
            as_text(row.get("metric_expressions"), 5000),
            "```",
            "",
            "过滤条件：",
            "",
            "```json",
            as_text(row.get("filters"), 5000),
            "```",
            "",
        ]
    lines += [
        "## 说明",
        "",
        "- 这里解析的是 Excel/复杂报表编辑页内嵌的子卡片配置。",
        "- 这些子卡片的指标公式可以进入指标字典；实际 Excel 输出值仍需单独导出文件或依赖卡片数据接口。",
    ]
    return "\n".join(lines) + "\n"


def render_custom_card_runtime(
    page: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# 观远自定义卡片运行态请求",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 捕获到的自定义卡片运行请求：`{len(rows)}`",
        "",
        "| 卡片 | 请求路径 | 响应类型 | 响应文本字符数 | 响应大小 | 子筛选/联动条件 |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {card_name} | `{request_path}` | `{response_mime}` | {response_text_chars} | {response_size} | {child_filters} |".format(
                card_name=md_cell(row.get("card_name")),
                request_path=md_cell(row.get("request_path")),
                response_mime=md_cell(row.get("response_mime")),
                response_text_chars=row.get("response_text_chars"),
                response_size=row.get("response_size"),
                child_filters=md_cell(row.get("child_filters"), 600),
            )
        )
    lines += [
        "",
        "## 说明",
        "",
        "- 若响应为 Excel 等二进制格式且 HAR 未保存可解析正文，则不能直接提取表格内容。",
        "- 请求体里的 `childFilters` 可以说明自定义卡片受哪些筛选器影响。",
        "- 如需解析自定义卡片实际结果，需要单独下载对应 Excel 或在页面里导出数据文件。",
    ]
    return "\n".join(lines) + "\n"


def render_dataset_mapping(
    page: dict[str, Any],
    summary: dict[str, Any],
    dataset_rows: list[dict[str, Any]],
    column_rows: list[dict[str, Any]],
    dataset_usage: dict[str, list[str]],
) -> str:
    lines = [
        "# 观远数据集映射清单",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 数据集数：`{len(dataset_rows)}`",
        "",
        "## 数据集总览",
        "",
        "| 数据集 | 字段数 | 公式字段数 | 行数 | 使用卡片数 | 指标引用数 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in dataset_rows:
        lines.append(
            "| {dataset_name} | {column_count} | {formula_column_count} | {row_count} | {card_usage_count} | {metric_usage_count} |".format(
                dataset_name=md_cell(row["dataset_name"]),
                column_count=row["column_count"],
                formula_column_count=row["formula_column_count"],
                row_count=row["row_count"],
                card_usage_count=row["card_usage_count"],
                metric_usage_count=row["metric_usage_count"],
            )
        )
    lines += [
        "",
        "## 数据源映射摘要",
        "",
        "| 数据集 | 连接 | 来源类型 | 查询类型 | 绑定表 | 最近修改时间 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in dataset_rows:
        lines.append(
            "| {dataset_name} | `{connection_id}` | `{source_type}` | `{query_type}` | `{source_table}` | `{datasource_modify_time}` |".format(
                dataset_name=md_cell(row.get("dataset_name")),
                connection_id=md_cell(row.get("connection_id")),
                source_type=md_cell(row.get("source_type")),
                query_type=md_cell(row.get("query_type")),
                source_table=md_cell(row.get("source_table")),
                datasource_modify_time=md_cell(row.get("datasource_modify_time")),
            )
        )
    lines += ["", "## 数据集使用卡片", ""]
    for dataset_name, card_names in sorted(dataset_usage.items()):
        lines.append(f"### {dataset_name}")
        lines.append("")
        for card_name in card_names:
            lines.append(f"- {card_name}")
        lines.append("")
    lines += [
        "## 数据集字段与公式字段",
        "",
        "| 数据集 | 字段名 | 类型 | 元类型 | 计算类型 | 公式 | 注释 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in column_rows:
        if row.get("formula") or row.get("annotation"):
            lines.append(
                "| {dataset_name} | `{field_name}` | `{field_type}` | `{meta_type}` | `{calculation_type}` | {formula} | {annotation} |".format(
                    dataset_name=md_cell(row["dataset_name"]),
                    field_name=md_cell(row["field_name"]),
                    field_type=md_cell(row["field_type"]),
                    meta_type=md_cell(row["meta_type"]),
                    calculation_type=md_cell(row["calculation_type"]),
                    formula=md_cell(row["formula"], 500),
                    annotation=md_cell(row["annotation"], 260),
                )
            )
    lines += [
        "",
        "## 解析说明",
        "",
        "- 本文件只能说明观远数据集层的字段配置，不能替代数仓 DDL 和 ETL SQL 血缘。",
        "- `row_count = 0` 可能是权限、缓存、抽取模式或 HAR 状态导致，不直接代表数据集无数据。",
    ]
    return "\n".join(lines) + "\n"


def render_dataset_source_mapping(
    page: dict[str, Any],
    summary: dict[str, Any],
    dataset_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# 观远数据集源表与 SQL 映射",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        "",
        "## 源表/SQL 总览",
        "",
        "| 数据集 | 连接 | 来源类型 | 查询类型 | 绑定表 | 调度 | 任务 ID | 最近修改时间 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in dataset_rows:
        lines.append(
            "| {dataset_name} | `{connection_id}` | `{source_type}` | `{query_type}` | `{source_table}` | `{enable_schedule}` | `{task_id}` | `{datasource_modify_time}` |".format(
                dataset_name=md_cell(row.get("dataset_name")),
                connection_id=md_cell(row.get("connection_id")),
                source_type=md_cell(row.get("source_type")),
                query_type=md_cell(row.get("query_type")),
                source_table=md_cell(row.get("source_table")),
                enable_schedule=md_cell(row.get("enable_schedule")),
                task_id=md_cell(row.get("task_id")),
                datasource_modify_time=md_cell(row.get("datasource_modify_time")),
            )
        )
    lines += ["", "## 数据集 SQL / 查询", ""]
    for row in dataset_rows:
        lines += [
            f"### {row.get('dataset_name')}",
            "",
            f"- 数据集 ID：`{row.get('dataset_id')}`",
            f"- 来源类型：`{row.get('source_type')}`",
            f"- 查询类型：`{row.get('query_type')}`",
            f"- 绑定表：`{row.get('source_table') or ''}`",
            f"- 连接：`{row.get('connection_id')}`",
            f"- 最近修改时间：`{row.get('datasource_modify_time')}`",
            "",
            "```sql",
            as_text(row.get("source_query"), 10000),
            "```",
            "",
        ]
    lines += [
        "## 说明",
        "",
        "- `queryType = table` 通常表示观远数据集直接绑定一张表，后续需要到本地代码或数仓中继续追这张表的加工逻辑。",
        "- `queryType = query` 表示观远数据集自身配置了 SQL，这部分 SQL 已在本文件中抽出，但仍需追 SQL 中引用的上游表。",
        "- 本文件只反映观远数据集层配置，不等于完整数仓血缘。",
    ]
    return "\n".join(lines) + "\n"


def render_metrics_dictionary(
    page: dict[str, Any],
    summary: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    formulas: list[dict[str, str]],
) -> str:
    unique_formula_rows: dict[str, dict[str, str]] = {}
    for item in formulas:
        unique_formula_rows.setdefault(item["formula"], item)

    lines = [
        "# 观远指标字典",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 卡片指标项：`{len(metric_rows)}`",
        f"- 去重公式数：`{len(unique_formula_rows)}`",
        "",
        "## 卡片指标清单",
        "",
        "| 卡片 | 数据集 | 指标 | 源字段 | 聚合 | 计算类型 | 表达式/公式 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in metric_rows:
        lines.append(
            "| {card_name} | {dataset_name} | {metric_name} | `{source_field}` | `{aggr_type}` | `{calculation_type}` | {expression} |".format(
                card_name=md_cell(row["card_name"]),
                dataset_name=md_cell(row["dataset_name"]),
                metric_name=md_cell(row["metric_name"]),
                source_field=md_cell(row["source_field"]),
                aggr_type=md_cell(row["aggr_type"]),
                calculation_type=md_cell(row["calculation_type"]),
                expression=md_cell(row["formula"] or row["expression"], 520),
            )
        )
    lines += [
        "",
        "## 去重公式清单",
        "",
        "| 指标/字段名 | 元类型 | 字段类型 | 公式 |",
        "| --- | --- | --- | --- |",
    ]
    for formula, item in sorted(unique_formula_rows.items(), key=lambda kv: (kv[1].get("name", ""), kv[0])):
        lines.append(
            "| {name} | `{meta_type}` | `{fd_type}` | {formula} |".format(
                name=md_cell(item.get("name")),
                meta_type=md_cell(item.get("meta_type")),
                fd_type=md_cell(item.get("fd_type")),
                formula=md_cell(formula, 700),
            )
        )
    lines += [
        "",
        "## 待人工确认",
        "",
        "- 这里的公式是观远层表达式，不等于完整业务口径。",
        "- 没有公式、只有字段名或聚合方式的指标，需要继续追数据集绑定表和上游 SQL。",
        "- 指标的业务解释、观察窗口、归因口径、金额单位需要在后续知识库标注中补齐。",
    ]
    return "\n".join(lines) + "\n"


def render_metric_lineage(summary: dict[str, Any], field_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# 观远字段与指标血缘",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 字段引用数：`{len(field_rows)}`",
        "",
        "## 字段明细",
        "",
        "| 卡片 | 字段角色 | 字段名 | 源字段 | 计算层 | 计算逻辑 | 数据集 | 底层表/直接上游 | 证据 | 需追数仓 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in field_rows:
        lines.append(
            "| {card_name} | `{field_role}` | {field_name} | `{source_field}` | `{calculation_layer}` | {calculation_logic} | {dataset_name} | {upstream_tables} | `{evidence_level}` | `{requires_warehouse_trace}` |".format(
                card_name=md_cell(row.get("card_name"), 180),
                field_role=md_cell(row.get("field_role")),
                field_name=md_cell(row.get("field_name")),
                source_field=md_cell(row.get("source_field")),
                calculation_layer=md_cell(row.get("calculation_layer")),
                calculation_logic=md_cell(row.get("calculation_logic"), 520),
                dataset_name=md_cell(row.get("dataset_name")),
                upstream_tables=md_cell(row.get("upstream_tables"), 320),
                evidence_level=md_cell(row.get("evidence_level")),
                requires_warehouse_trace=md_cell(row.get("requires_warehouse_trace")),
            )
        )
    lines += [
        "",
        "## 证据解释",
        "",
        "- `confirmed_guanyuan`：HAR 中存在数据集绑定表或数据集 SQL，已确认到观远数据集层。",
        "- `partial`：已确认卡片字段和数据集，但 HAR 未包含数据集绑定表或 SQL。",
        "- `missing`：当前网络记录中未拿到该字段的数据集标识。",
        "- `requires_warehouse_trace=true`：观远只做字段读取或简单聚合，完整业务计算必须继续追底层 ETL。",
        "- SQL 上游表来自 `FROM/JOIN` 静态抽取，只表示直接引用，不替代 SQL 解析器或数仓血缘审计。",
        "",
        "完整源 SQL 和全部机器字段见 `data/field_lineage.csv`。",
    ]
    return "\n".join(lines) + "\n"


def render_coverage_report(
    summary: dict[str, Any],
    field_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    custom_runtime_rows: list[dict[str, Any]],
    custom_edit_rows: list[dict[str, Any]],
) -> str:
    dataset_gaps = [
        row
        for row in dataset_rows
        if not row.get("source_table") and not row.get("source_query")
    ]
    missing_fields = [row for row in field_rows if row.get("evidence_level") == "missing"]
    partial_fields = [row for row in field_rows if row.get("evidence_level") == "partial"]
    runtime_custom_ids = {row.get("card_id") for row in custom_runtime_rows}
    edit_custom_ids = {row.get("custom_card_id") for row in custom_edit_rows}
    custom_edit_gaps = sorted(str(value) for value in runtime_custom_ids - edit_custom_ids if value)
    confirmed = summary.get("confirmed_source_field_count", 0)
    total = summary.get("field_lineage_count", 0)
    coverage_rate = confirmed / total if total else 0

    lines = [
        "# HAR 解析覆盖与补采报告",
        "",
        f"- 来源 HAR：`{summary['har_file']}`",
        f"- 看板：`{summary['page_name']}`",
        f"- 卡片：`{summary['card_count']}`",
        f"- 筛选器：`{summary['selector_count']}`",
        f"- 数据集：`{summary['dataset_count']}`",
        f"- 字段引用：`{total}`",
        f"- 已确认到观远源表/SQL：`{confirmed}`（`{coverage_rate:.1%}`）",
        f"- 需要继续追数仓 ETL：`{summary.get('warehouse_trace_required_count', 0)}`",
        "",
        "## 缺口判定",
        "",
        f"- 无数据集标识的字段引用：`{len(missing_fields)}`",
        f"- 有数据集但无绑定表/SQL 的字段引用：`{len(partial_fields)}`",
        f"- 无绑定表/SQL 的数据集：`{len(dataset_gaps)}`",
        f"- 捕获运行态但未捕获编辑态的自定义卡片：`{len(custom_edit_gaps)}`",
        "",
    ]
    if dataset_gaps:
        lines += [
            "### 需补数据集编辑态",
            "",
            "| 数据集 | 数据集 ID | 来源类型 |",
            "| --- | --- | --- |",
        ]
        for row in dataset_gaps:
            lines.append(
                f"| {md_cell(row.get('dataset_name'))} | `{md_cell(row.get('dataset_id'))}` | `{md_cell(row.get('source_type'))}` |"
            )
        lines.append("")
    if custom_edit_gaps:
        lines += [
            "### 需补自定义卡片编辑态",
            "",
        ]
        lines.extend(f"- `{card_id}`" for card_id in custom_edit_gaps)
        lines.append("")
    lines += [
        "## 是否需要重新采集",
        "",
        "- 若数据集缺少绑定表或 SQL：进入对应数据集编辑页，打开数据源/SQL 配置并等待加载后再导出 HAR。",
        "- 若自定义卡片缺少内部指标：进入卡片编辑页，等待内部子卡片全部加载后再导出 HAR。",
        "- 若筛选器缺少来源或联动目标：依次展开筛选器并各切换一次选项；必要时进入筛选器编辑页。",
        "- 若只缺数仓字段的完整业务逻辑：无需继续抓 HAR，应使用源表名去 ETL 代码库追加工 SQL。",
        "",
        "## 边界",
        "",
        "- HAR 能确认观远页面、卡片、筛选器、字段、计算字段、数据集和观远数据源配置。",
        "- HAR 不能自动证明底层字段业务定义、去重主键、时间口径和上游 ETL 公式；这些必须由代码血缘或业务标注补齐。",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
