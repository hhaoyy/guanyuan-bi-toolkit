# Select a template by the decision

Use the installable `assets/templates/engine.js`, `view.js` and `theme.css` in this skill. The repository's `examples/template-gallery/index.html` provides four layouts, three themes and a synthetic drill-down example. These are original MIT starter templates, not imported third-party dashboard packages or certified production charts.

| Template | Question | Required measures | Additional conditions |
| --- | --- | --- | --- |
| overview | Overall performance and contribution | orders, sales | Additive orders/sales; average = total sales / total orders |
| funnel | Stage conversion and loss | visitors, leads, orders | Same nested cohort, unique users per stage, mature observation window; `orders` represents converted users here, not repeat purchases |
| channels | Channel scale versus efficiency | visitors, orders, sales | Exclusive/deduplicated attribution; orders here represent converted users for conversion rates |
| monitor | Groups beyond a specified change threshold | sales | User-confirmed relative-change threshold, not a statistical anomaly detector |

Shared input: one row per `period` (`baseline` or `current`) and `group`; both periods must be present per group. Numbers must be finite and nonnegative. Missing group-period rows are unknown, never zero. These starters do not support negative net revenue or multi-currency sums without redesigning the contract. A growing/new group with no baseline needs a separate analysis, not fabricated zeros.

Context: `currentLabel`, `baselineLabel`, `qualityConfirmed`; funnel also `cohortConfirmed`; monitor also `threshold` as a positive fraction. These flags represent completed caller checks, not checks the engine can infer. Verify full comparable windows, refresh watermark, population, metric definitions and additive grain before setting them. The example declares synthetic inputs only.

## Recommend, preview, then bind

Recommend two appropriate layouts with their required fields and trade-offs. Prefer business (light), compact (dense) or dark (presentation) theme according to audience; theme changes never change calculations. Respect an explicit user design. Do not make a funnel from unrelated event counts just to match a template.

Copy required assets into the user's private project, adapt field mapping and wording, and show a synthetic preview before platform publication. Build an explicit name-based adapter from the confirmed Guanyuan column data to the row contract; reject duplicate columns, unequal lengths and missing fields. Do not reuse the older coffee example's fixed schema for these templates.

For SDK integration, include engine and view JavaScript in the platform script, load scoped theme CSS, and use `renderChart`/`GDPlugin` registration from the HTML skill. On every render create a fresh view from current data/context. The gallery's UI controls and synthetic bootstrap are local preview only. `BITemplateView.mount(container, kind, rows, context, scope, theme)` replaces the current markup; its drill-down handler belongs to that container and must be replaced/cleared on rerender. It filters the received aggregate result only; page selectors and server-side queries still require CLI configuration. No external CDN/model service is required.

An agent can extend descriptive results with the unified skill's evidence-backed analysis workflow when data use is authorized. Never label the deterministic demo as a live AI model. AI narratives need their own scope/timestamp handling. Compare metrics and findings after each scope change, test empty/invalid inputs, and verify the actual platform rendering before marking delivery complete.

## Executable diagnosis

`analyze` now returns template-specific `insights`, numeric `evidence` and `actions`. `investigate(kind, rows, context, scope, actionId)` executes the selected local investigation: order/average decomposition, sequential funnel-stage effects, channel volume/conversion decomposition, or threshold priority. Effects are order-dependent arithmetic, not causal attribution. Zero denominators return `not_evaluable`; absent daily data returns `needs_data`. The view offers buttons and updates findings per scope.

For AI-selected explanations and live server refresh, use `guanyuan-bi` → `references/superapp-analysis.md`. Keep this local engine as a reproducible evidence layer; do not put credentials or MCP sessions into custom-chart HTML.
