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

Choose the visual structure by the reading task: overview uses a focal KPI with period bars and a composition ring; funnel uses stage flow and transition rates; channels uses a comparison workbench; monitor uses a threshold summary and status cards. These are starting structures, not mandatory business categories. If two use cases need the same structure, reuse it instead of creating cosmetic variants. Recommend alternatives only when the hierarchy or chart choice meaningfully differs; include required fields and trade-offs. Prefer business (light), compact (dense) or dark (presentation) theme according to audience; theme changes never change calculations. Respect an explicit user design. Do not make a funnel from unrelated event counts just to match a template.

Copy required assets into the user's private project, adapt field mapping and wording, and show a synthetic preview before platform publication. Build an explicit name-based adapter from the confirmed Guanyuan column data to the row contract; reject duplicate columns, unequal lengths and missing fields. Do not reuse the older coffee example's fixed schema for these templates.

For SDK integration, include engine and view JavaScript in the platform script, load scoped theme CSS, and use `renderChart`/`GDPlugin` registration from the HTML skill. On every render create a fresh view from current data/context. The gallery's UI controls and synthetic bootstrap are local preview only. `BITemplateView.mount(container, kind, rows, context, scope, theme)` replaces the current markup; its drill-down handler belongs to that container and must be replaced/cleared on rerender. It filters the received aggregate result only; page selectors and server-side queries still require CLI configuration. No external CDN/model service is required.

An agent can extend descriptive results with the unified skill's evidence-backed analysis workflow when data use is authorized. Never label the deterministic demo as a live AI model. AI narratives need their own scope/timestamp handling. Compare metrics and findings after each scope change, test empty/invalid inputs, and verify the actual platform rendering before marking delivery complete.

## Executable diagnosis

`analyze` now returns template-specific `insights`, numeric `evidence` and `actions`. `investigate(kind, rows, context, scope, actionId)` executes the selected local investigation: order/average decomposition, sequential funnel-stage effects, channel volume/conversion decomposition, or threshold priority. Effects are order-dependent arithmetic, not causal attribution. Zero denominators return `not_evaluable`; absent daily data returns `needs_data`. The view keeps findings and diagnostic actions inside a collapsed “进一步分析” section. The initial view prioritizes charts and metrics; expanding the section exposes prerequisites before any action. Findings update per scope.

For AI-selected explanations and live server refresh, use `guanyuan-bi` → `references/superapp-analysis.md`. Keep this local engine as a reproducible evidence layer; do not put credentials or MCP sessions into custom-chart HTML.

Investigation results render in a separate full-width region with column units and a data-dependent next step. Missing monetary units remain explicitly unconfirmed; do not invent a currency. `needs_data` actions display their prerequisites before interaction and are disabled. The private service enables daily investigation only when a configured adapter is authorized for the current scope. Changing scope or data clears the previous investigation result.

## Layout review

Use real browser screenshots of the rendered page. Check desktop and narrow layouts, dense/empty data, chart labels and units, and available chart area. Avoid a long narrative sidebar that leaves the chart column mostly empty. Do not invent daily points or decorative trends when only two aggregate periods exist. Group comparisons must retain their exact values in accessible text or tables. The included layouts use original CSS/SVG, inspired by the hierarchy of [Tabler](https://preview.tabler.io/), the comparisons of [Tremor](https://dashboard.tremor.so/overview) and [Grafana design guidance](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/). No third-party template code is bundled.
