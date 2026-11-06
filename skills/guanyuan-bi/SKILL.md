---
name: guanyuan-bi
description: Help users build, improve or analyze Guanyuan dashboards from a business question, field description or existing dashboard link. Recommend layouts and evidence-backed analysis, then route to HTML, CLI or lineage skills as needed.
---

# Guanyuan BI assistant

Start from the user's question, available fields or existing dashboard link. Reuse known context. Ask only for missing business definitions, comparison scope or access decisions that affect the result; do not make users select technical skills or fill out a full data contract before helping.

## Choose the work

- Business question / new dashboard: infer candidate metrics and dimensions from available evidence, explain unconfirmed definitions, then use `guanyuan-html-bi-generic` to choose or adapt a suitable layout, offering alternatives when they meaningfully differ. Reuse a requested design without forcing selection. If the user requests native Guanyuan charts, preserve that choice and use the CLI route rather than forcing HTML.
- Existing dashboard link: use `guanyuan-metric-lineage` to understand calculations and filters, then inspect authorized aggregate results for analysis. Configuration alone is not numerical evidence.
- Prepared HTML / platform edits: route to `guanyuan-cli` for version adaptation and platform delivery. Existing task authorization applies; do not repeat approvals or require the user to transfer context between skills.
- Analysis only: follow [analysis workflow](references/analysis.md); no publishing or visual redesign is necessary.

Resolve companion skills by their installed names, not hardcoded sibling paths. If one is absent, continue independent work and identify the missing capability; use the repository's installation instructions when installation is requested. Do not claim platform completion from a local preview.

## Proactive analysis

For dashboard building or analysis requests, read [analysis workflow](references/analysis.md). Propose relevant comparisons, check data fitness, identify supported changes and suggest the next useful investigation. For a narrow cosmetic fix, do not expand into business analysis unless requested. Preserve user priorities.

Return useful findings before implementation details: what changed, evidence and scope, what remains unknown, and a concrete next investigation. Distinguish facts from hypotheses; a contribution decomposition is not causal proof. Validate arithmetic with code or authorized query results. A chart caption or generated narrative is not evidence.

## Optional SuperApp analysis

For selectable AI explanations, refreshable conclusions or executable investigations, read [SuperApp analysis integration](references/superapp-analysis.md). Prefer the authenticated gateway/service architecture; users configure their own approved AI or MCP service. Reuse the supplied client/service interfaces and template-specific diagnostic actions. Do not mistake MCP for a model, deploy the demo authentication stub, or label local rule results as AI.

## Finish

For a dashboard, deliver the chosen layout and theme, field mapping, preview, relevant findings and platform acceptance status. For analysis, deliver findings plus traceable evidence without modifying the dashboard unless asked. Store project decisions and evidence privately for subsequent edits. This skill runs within a user task; it does not create an unattended monitoring service or notifications.
