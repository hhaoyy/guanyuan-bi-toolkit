# CLI-first lineage workflow

Use the official component documentation installed with the user's `guancli`; command syntax and output fields can change by version. The companion `guanyuan-cli` skill covers installation, profile resolution and private configuration. This workflow is read-only.

## 1. Resolve the dashboard

From a supplied page URL, extract or resolve the page ID without treating other URL fragments as resource IDs. Otherwise search by name and disambiguate using path and metadata.

Typical commands:

```bash
guancli page search <keyword>
guancli page get <page_id>
guancli url page <page_id>
```

Use the selected profile consistently. Request full page detail rather than a brief view because the analysis needs card definitions, calculations, selector settings, interactions, data queries and lineage. Save structured output privately when the installed version supports JSON output. Do not paste large raw responses into the final report.

## 2. Build the page map

Start from `page get` and inventory all tabs/pages, cards and selectors before chasing individual datasets. Extract:

- Card IDs, type/subtype, dataset IDs, dimensions, measures, aggregation and sort.
- Card formulas and query/model definitions.
- Selector type, bound field, configured default/dynamic value, automatic linkage and explicit target mappings.
- Card-to-card linkage, click actions, drill paths and other interaction targets exposed by the current version.

Use `guancli card get <card_id>` only when the page output omits details needed for a specific card. Do not assume visually adjacent cards are linked.

## 3. Expand datasets and upstream resources

Deduplicate dataset IDs from the page before querying them. Use full dataset detail because brief mode may omit calculation formulas and lineage.

```bash
guancli ds get <dataset_id>
guancli ds get <dataset_id> --assoc
guancli etl get <etl_id>
```

For each referenced field, distinguish:

1. Card aggregation or card formula.
2. Dataset calculated field and its formula/dependencies.
3. Dataset source mapping or SQL projection.
4. ETL node logic and SQL.
5. Warehouse or external-source logic outside the visible evidence.

Follow association and lineage output only as far as required by the user's question. If a source is hidden by permissions, mark the exact dataset/field boundary as `partial`; do not replace missing evidence with a name-based guess.

## 4. Reconstruct filtering and linkage

Represent each selector as a directed mapping:

```text
selector → source field → target card → target field → default/dynamic context
```

Record whether a target comes from explicit mappings or automatic same-name matching. Dynamic parameters and selectors are different mechanisms. Tree/combined selectors and complex-report child mappings may not be fully reducible to ordinary field filters; preserve their native configuration and mark any unresolved mapping.

To validate a value or first-open behavior, use the installed command syntax for card preview and state the page context explicitly. Common patterns include:

```bash
guancli card preview <card_id> --page-id <page_id> --with-default-filters
guancli card preview <card_id> --page-id <page_id> --filter "<field> <operator> <value>"
guancli ds preview <dataset_id> --limit 20
```

Do not apply default filters merely because they exist when the question concerns the card's raw definition. Preview proves returned data under a stated context; it does not by itself prove the selector-link configuration.

## 5. Consolidate once

Build one normalized report from the collected resource details instead of asking the user for a HAR of the same state. Include resource URLs when helpful. Separate:

- Current configuration observed through CLI.
- Formula meaning supported by expressions.
- Business meaning supplied by the user or documentation.
- Numerical validation from preview.
- Missing upstream or permission evidence.

Use HAR only for named gaps that CLI cannot expose. If live resources change during analysis, record the observation time and re-read affected objects before concluding.
