---
name: guanyuan-metric-lineage
description: Analyze Guanyuan dashboard metrics, formulas, selectors, interactions and upstream lineage. Prefer live read-only guancli evidence; use local HAR parsing only when CLI access or coverage is insufficient.
---

# Guanyuan Metric Lineage

Explain how a dashboard calculates, filters and connects its data. Keep formulas, aggregations, selector rules, card interactions, dataset calculations and upstream transformations as distinct layers. Do not infer business definitions from labels or simple expressions.

## Choose the evidence path

When `guancli` is available and the user permits access to the target environment, read [CLI-first workflow](references/cli-first.md) and start there. A dashboard URL or page ID is enough to begin after resolving an authenticated profile. Do not require the user to record a HAR first.

Use [HAR fallback](references/har-fallback.md) when the user explicitly supplies captures, wants offline analysis, cannot use CLI, lacks a needed CLI permission, or the installed client/server does not expose part of the configuration. Collect only the missing evidence instead of restarting the entire analysis from HAR. CLI reflects current platform state; HAR reflects the state and requests at capture time. Preserve that distinction when combining them.

If upstream logic continues into ETL, dataset SQL or warehouse code, use the corresponding authorized query tools. Direct `FROM`/`JOIN` references are clues, not complete transitive lineage.

## Output

Produce a concise dashboard overview plus machine-readable tables where useful:

- Cards and metrics: page/tab, card ID, display type, dataset, dimensions, measures, aggregations, card calculations and unresolved business definitions.
- Filters and interactions: selector ID/type, source field, default or dynamic value, target cards/fields, automatic versus explicit linkage, and card-to-card actions.
- Dataset lineage: dataset calculation formulas, source or SQL evidence, upstream datasets/ETL, refresh context when relevant, and gaps requiring another tool or permission.
- Evidence: source (`guancli`, `HAR`, upstream tool), observed time or capture time, evidence level, and the exact unresolved item.

Use `confirmed_cli`, `confirmed_har`, `partial` and `missing` as evidence levels. “Confirmed” means the platform configuration or captured response was observed; it does not prove the business definition or numerical correctness. Validate requested values separately with card/dataset preview and state which filter context was applied.

Keep authentication, outputs, SQL, IDs and reports in the user's authorized private workspace. Never upload live output to this public toolkit. Public bug reports and tests must use newly constructed synthetic examples.

## CLI version changes

When using the companion `guanyuan-cli`, run its version-adaptation workflow before platform operations. Use matching installed documentation and refresh affected private capability records after upgrades or downgrades. If the companion is unavailable, inspect the selected CLI version and matching official docs directly; do not assume latest syntax. Preserve local preview or offline HAR workflows when platform capabilities are unavailable.

## From definitions to business analysis

When the user asks what changed or what to investigate, hand the observed formulas, filter context and evidence gaps to `guanyuan-bi` when available. Numerical analysis requires authorized aggregate data and comparable periods; lineage alone does not establish trends or causes. Keep configuration-only requests scoped.
