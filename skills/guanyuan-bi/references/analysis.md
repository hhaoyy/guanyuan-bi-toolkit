# Evidence-backed proactive analysis

## Establish scope without a questionnaire

Use the business question, existing page/filter definitions and supplied materials first. Confirm only unresolved metric definitions, period/cohort, population, currency/time zone and authorized data access that materially change the answer. Recommend comparisons and dimensions instead of asking users to design the whole analysis. A dashboard refresh inside BI does not automatically refresh an AI-written narrative.

## Data boundary

BI access control and model data processing are separate boundaries. Before reading data into AI context, establish the allowed scope from user/project policy. Prefer minimum aggregate results and metadata, never raw personal records by default. If model access to business values is not permitted, deliver query/analysis plans or approved data-side deterministic checks; do not send the data to the model. Do not put model API credentials or external model requests in published HTML.

## Check fitness before conclusions

Check refresh time against the expected watermark, full comparable windows, equal duration or a justified normalization, same filters/time zone/currency, unique grain, missing values and denominators. For funnels establish cohort membership, stage order and observation maturity; separate independent event counts are not automatically a funnel. For channel comparisons establish attribution and deduplication. Missing data, incomplete current periods or changing population must not become a fabricated decline or zero.

If evidence is insufficient, report the precise gap and continue supported analysis. Thresholds and baselines come from the user/contract; do not silently introduce business alarm rules.

## Analyze in layers

1. **What changed?** Absolute values and differences, rates only when the denominator is valid, period/filter labels and timestamps. With zero baseline, percentage change is undefined.
2. **Where?** Compare dimensions at consistent grain. Rank signed contributions to an additive total change and include offsetting increases. Do not use the largest percentage swing alone. Ratio changes require numerator/denominator analysis; never sum ratios.
3. **What could explain it?** Separate observed decomposition from hypotheses. State alternate explanations and missing evidence; do not turn correlation into cause.
4. **What next?** Recommend a concrete dimension, field or comparison to verify. Within the authorized read scope, continue bounded follow-up queries that answer the question; do not scan every dataset. Stop when answered, evidence is insufficient, or access is unavailable. Publishing, schedule changes and notifications remain separate actions.

## Output contract

Each important finding has: metric; current/baseline values and periods; filters/population; absolute and relative change where defined; evidence source and observed time; confidence boundary; hypothesis (optional); next verification. Say “no material change under the specified rule” or “not evaluable” when appropriate instead of manufacturing insights. Order findings by impact and actionability, normally no more than three primary findings.

The bundled template engine demonstrates deterministic descriptive analysis, not a model service. Its `qualityConfirmed` flag must be set only after the caller actually verifies data fitness. Static findings displayed in a dashboard need explicit analysis timestamps and must be regenerated or invalidated when scope/data change. For truly recurring analysis, separately design a scheduler, authorized computation environment and delivery policy.

## Acceptance scenarios

Use synthetic cases covering a decline with offsetting groups, zero baseline, incomplete periods, missing fields, a non-nested funnel, mixed populations and a stable period. A useful response identifies gaps without a confident unsupported cause. Verify that selecting a group updates both metrics and findings, that conclusions match the arithmetic, and that the report distinguishes suggested investigation from completed investigation.
