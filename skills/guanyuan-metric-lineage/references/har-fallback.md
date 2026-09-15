# HAR fallback

HAR parsing remains useful for offline work, historical request evidence and configuration not exposed by the available CLI/server combination. It is a fallback or supplement, not a mandatory prerequisite.

Resolve scripts relative to the skill directory:

```bash
python3 scripts/analyze_guanyuan_logs.py INPUT.har --output-root OUTPUT
```

Use `--merge` only for captures of the same dashboard. It concatenates entries and selects the largest page-config response; it does not reconcile conflicting configurations. Different dashboards remain separate analyses.

Inspect `INDEX.md`, `combined_field_lineage.csv` and each `docs/coverage_report.md`. A successful process is insufficient: verify field rows and explain missing evidence.

Parser evidence levels map as follows:

- `confirmed_guanyuan` in legacy parser output becomes `confirmed_har` in the consolidated report: a captured dataset binding table or SQL is present.
- `partial`: dataset identified but source absent.
- `missing`: field has no dataset identifier.

Keep card formulas, dataset formulas, aggregations and upstream fields distinct. The parser expects supported page configuration in response bodies. For a missing item, first decide whether a focused `guancli page/card/ds/etl get` can supply it. Recapture only when CLI cannot, offline evidence is required, or the user explicitly wants capture-based analysis.

When recapture is necessary:

1. Preserve response bodies and record capture time/environment privately.
2. Visit only the page or editor needed for the named gap.
3. For card formulas, capture card editing state; for dataset source gaps, capture its source configuration.
4. Do not repeatedly capture HAR for warehouse transformations; use authorized ETL/code lineage tools.

Do not upload HAR or generated reports. They may contain credentials, SQL, field values, resource IDs and internal URLs. The parser uses simple SQL reference extraction and does not prove full transitive lineage; validate complex SQL separately.
