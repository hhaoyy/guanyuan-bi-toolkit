---
name: guanyuan-metric-lineage
description: Parse local Guanyuan HAR captures into card, metric, selector, dataset and direct-source inventories, with evidence levels and capture gaps.
---

# Guanyuan Metric Lineage

Resolve scripts relative to this skill directory. Parse only local captures the user is authorized to inspect. Do not upload input or generated reports.

```bash
python3 scripts/analyze_guanyuan_logs.py INPUT.har --output-root OUTPUT
```

Use `--merge` only for captures of the same dashboard. It concatenates entries and selects the largest page-config response; it does not reconcile conflicting configurations. Different dashboards must remain separate analyses.

Inspect `INDEX.md`, `combined_field_lineage.csv` and each `docs/coverage_report.md`. A successful process alone is insufficient: verify field rows and explain missing evidence.

- `confirmed_guanyuan`: dataset binding table or SQL is present.
- `partial`: dataset identified but source absent.
- `missing`: field has no dataset identifier.

Keep card formulas, dataset formulas, simple aggregations and upstream fields distinct. Direct `FROM/JOIN` references are clues, not complete transitive lineage. Do not infer business definitions from names or `SUM(field)`.

For missing page config, recapture after refresh with response bodies. For formulas, inspect card editing state. For dataset source gaps, inspect its source configuration; the parser currently expects source information inside page `dsInfos`. For missing warehouse logic, trace authorized ETL code rather than repeatedly capturing HAR.

Report counts, evidence boundaries and precise next steps. Never print authentication values. Outputs may contain business data, SQL and identifiers; keep them within the same authorized boundary as inputs. Public bug reports must use newly constructed synthetic examples.
