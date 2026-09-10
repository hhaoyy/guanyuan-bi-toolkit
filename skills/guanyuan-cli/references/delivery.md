# Dataset-to-dashboard delivery

## 1. Establish the handoff

Accept the requested behavior, HTML/CSS/JS, and a result-set contract. The contract specifies each dataset's logical role, grain, field names/types, units, aggregation, ordering, refresh needs and consumer modules. Keep logical roles separate from environment-specific IDs. Build an ordered mapping from roles to actual dataset IDs and projected fields in the private project.

Do not invent business definitions from sample visuals. Existing suitable datasets can be reused. SQL drafts need validation in the authorized data environment; CLI installation does not grant database write access. Load the user's database tools when upstream preparation is necessary.

## 2. Prepare datasets

Read `guands` documentation for connection discovery, directories, dataset creation/editing and preview. Resolve the intended connection and location, then create or update only what the task requires. Check returned schema, field identity, grain and representative results against the contract. Schema changes may require explicit structure and card-binding updates; refreshing rows alone is insufficient. Read back any requested refresh schedule and its enabled state.

Record IDs immediately after creation. On partial failure, reuse the recorded resources after verifying state instead of creating duplicates.

## 3. Build HTML as a custom chart

Use installed `guanvis` CustomChartBuilder documentation and its SDK example for the exact DSL supported by that version. The relevant documented pattern is a custom chart with SDK subtype, HTML/CSS/JS content loaded from a common file basename, and ordered data views attached to the chart. SDK DOM rendering uses `renderChart(data, clickFunc, config)` plus `new GDPlugin().init(renderChart)`. Pure ECharts mode uses a different entrypoint; do not mix the two.

- Create the source project through documented initialization commands. Use generated resource IDs for new pages/cards; retain IDs for updates.
- Bind each data view to the mapped dataset and actual fields. Choose aggregation and sort from the contract; do not aggregate ratios or collapse rows unintentionally. Ensure the projected names match the HTML adapter.
- Keep the data-view order aligned with the adapter. Do not treat raw dataset preview as proof of the card's final query shape.
- Load platform HTML/CSS/JS only. Exclude mock data, preview bootstraps and synthetic demo controls from publication. Reuse the platform container and scope CSS to it.
- Add requested page filters and field links. A frontend dropdown filters its received rows; it does not automatically become a server-side page selector. Verify the requested behavior and data range explicitly.
- Put the page in the resolved target directory through the supported builder or command option.

## 4. Publish and accept

Run `guanvis preview <project>` and, when supported, `guanvis publish <project> --dry-run`. Structural preview does not render platform HTML. Inspect the intended page IDs and changes before publishing. For an authorized same-ID replacement, use the installed version's documented overwrite mechanism and preserve its backup behavior.

After publishing, read back page/card IDs, subtype, dataset bindings, projected fields and selectors. Open the actual page with an available browser tool and inspect rendering, data, filters, empty states and rerender behavior. A supported CLI screenshot can provide visual evidence; if screenshot export is unavailable, use the browser. If no platform viewing tool is available, give the page link and mark visual acceptance pending instead of claiming completion.

Compare displayed values with the authorized data contract checks. Report the actual saved page URL, completed changes and any unresolved behavior. A post-publish error can happen after a successful write: inspect saved state and repair only the failed step. Do not blindly republish.

## 5. Update the same dashboard

Reuse the preserved source when it matches the online state. If the page changed elsewhere or source is unavailable, checkout the current version and compare an unedited diff before editing. Check the custom component subtype: SDK/ECHARTS_LITE content editing is different from plugin-market or complex-report resources. Do not force an unsupported subtype through the HTML API.

Keep page/card IDs and unaffected layout, bindings and selectors. Investigate unexplained checkout differences before overwriting unrelated content. Validate changed data contracts, republish the intended same-ID resources and repeat affected platform checks. Backups and rollback support depend on the actual tool and server; do not promise automatic rollback without verifying it.

## Evidence boundary

The public toolkit ships workflow guidance and synthetic local tests. It does not certify a particular tenant's HTML publication or server compatibility. Live first-publication and same-ID-update acceptance must be recorded in the user's private project, never uploaded as public test fixtures.
