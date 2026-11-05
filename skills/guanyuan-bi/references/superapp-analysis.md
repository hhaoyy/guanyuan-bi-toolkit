# Optional live analysis through SuperApp

Use when users want optional AI explanations, refreshable analysis or clickable investigations in a Guanyuan application. This is a generic integration contract, not a preconfigured production service. Keep standalone local dashboards available.

## Supported platform boundary

The official GuanCLI 1.0.72 package documents SuperApp creation/publishing and API Gateway request forwarding. The gateway supports POST, server-side Secret references, logged-in user/group and caller-host restrictions, and returns a `gatewayPath` from the actual route configuration. This does not prove that SuperApp embeds an MCP client or that any BI tenant has a compatible AI endpoint.

Reference: [official CLI package](https://www.npmjs.com/package/@guandata/guancli/v/1.0.72), [request forwarding docs](https://docs.guandata.com/product/bi/api-gateway). Read the installed version's `references/gateway.md` and `app publish` help for the actual environment.

Recommended flow:

```text
SuperApp UI: scope / analysis mode / refresh / investigation
  → same-origin Guanyuan API Gateway (authenticated route)
  → private analysis service (authenticate + authorize + load fresh aggregate data)
  → deterministic diagnosis and optional configured MCP analysis tool
  → evidence-linked explanation + typed investigation result
```

MCP exposes tools; it is not itself a model or an authorization system. Users choose and adapt their own approved AI/MCP service. No external AI service is configured or required for the public demo.

## Reusable code

This skill ships `assets/superapp/client.js` and `service.cjs`. The deterministic engine is supplied by the companion HTML skill at `assets/templates/engine.js`; resolve its installed location and pass it explicitly into the service. The engine is not duplicated or fetched automatically.

- `client.controller`: invalidates old results on scope/data changes, aborts previous requests, ignores late responses, supports request timeout, manual refresh and opt-in periodic refresh (minimum 10 seconds; example 30). Hidden pages skip polling. Call `setContext` when filters, periods, source or data revision change; call `dispose` on unmount. Auto-refresh is polling, not streaming or guaranteed real-time delivery. Refresh failure clears old conclusions rather than presenting them as fresh.
- `client.gatewayTransport`: POST JSON to the verified same-origin `/api/gateway/routes/<routeCode>` with browser session credentials. No third-party URLs or secrets. This application contract requires JSON; non-JSON/empty responses are incompatible and do not trigger a direct-call fallback.
- `service.createService`: inject authenticated host adapters; reconstruct trusted data on the server; compute evidence; optionally call an AI provider. It does not start a server, define login, or infer tenant permissions.
- `service.mcpProvider`: accepts an already initialized official MCP SDK client and a fixed, operator-selected read-only analysis tool name. It calls `client.callTool` with scoped aggregate evidence, timeout and cancellation. No browser-selected tool names, arbitrary SQL or write actions. The host implements initialization, session lifecycle, tool contract verification and approved credentials. SDK dependency belongs to the user's private service, not the frontend.

## Request and response

Request fields: `schemaVersion: 1`, `requestId`, `template` (one of the four catalog keys), `sourceRef` (private logical source, not SQL), `window` (server-resolved period identifier), `scope` (group or null), `mode` (`local` or `ai`), optional `action` from the template's action list. Do not trust identity, data rows, capability flags or tool names from the request body. Service projection ignores extra browser fields.

The response echoes request identity and scope, and supplies `revision`, `observedAt`, `generatedAt`, `mode`, `analysis`, optional `investigation`, optional `ai`. Local investigation outputs include `units` (column-to-unit mapping) and `nextStep`; render both with the result. Display `needs_data` actions disabled with prerequisites. Daily investigation becomes ready only after adapter availability and scope authorization checks. Analysis includes exact computed `evidence`, distinct template `insights`, and allowlisted `actions`. AI tool output must be `{summary: string, evidenceIds: string[]}` referencing existing evidence IDs. The service strips other fields and rejects unknown references. Display text escaped, never as HTML. Valid references do not establish semantic correctness or causation; label AI explanations as such. AI explanations must not automatically become executable commands.

Provider input is `{evidence: {template, scope, periods, revision, evidence}}` in MCP tool arguments. The provider receives only server-approved aggregate evidence, not raw rows or authentication material. If its actual schema differs, adapt server-side after inspecting the tool contract. `isError`, invalid JSON, missing references, denial and timeout fail visibly. Do not silently replace a failed AI request with a “successful AI” deterministic result.

## Host adapters that users must supply

1. `authenticate(transportContext)` validates trusted gateway-to-service credentials and verified user identity. Never trust a browser-provided user header. If signed identity propagation is unavailable, limit service data to the explicitly approved shared audience; do not use an admin credential as a universal proxy.
2. `authorize(principal, request)` resolves source, window, group, tenant and row/column access. Return `{allowed, allowAI}`; `allowAI` is a separate model-data-use decision. Recheck daily investigation authorization separately.
3. `loadSnapshot(principal, request, {signal})` fetches only permitted data and returns `{rows, context, revision, observedAt}`. Resolve periods and verify freshness, completeness, cohort and metric definitions before setting context flags. Use an immutable revision consistent with rows; implement snapshot limits and deadlines in this adapter. Browser flags cannot establish fitness.
4. Optional `provider` invokes an approved analysis endpoint or configured MCP analysis tool. Restrict tool privileges and egress at the host; disable write-capable tools. Manage cancellation and provider budget.
5. Optional `investigateDaily(principal, request, snapshot, {signal})` fetches bounded same-scope daily aggregates with current authorization, freshness and matching snapshot checks; returns a typed `complete`, `needs_data` or `not_evaluable` result. Without it the action honestly reports required evidence.

The host HTTP layer must enforce route authentication, Origin/CSRF protections as applicable, size/rate/concurrency limits, timeouts, redacted errors, no-store responses and tenant isolation. No result cache is shipped; any cache must include identity/authorization scope, filters, source revision and analysis version.

## Deploy via the user's existing tooling

Use the CLI skill for version matching. Inspect `guancli gateway search/get` and use the returned enabled POST route and required inputs, not a guessed route. Configure the private analysis service outside the static application; a SuperApp upload does not deploy Node code. Keep Secrets server-side. Do not create a broad-access route just to make the demo work.

Create the actual SuperApp using the installed `guancli app create` template, copy the frontend components into that scaffold and use its supported build. The repository demo is a loopback HTML/Node reference, not a platform-ready `dist` archive. Publish only after target/app/route scope is established; preserve existing online settings unless their replacement is authorized. Static files never include provider keys, tenant config or the demo authentication stub.

Accept: authenticated same-scope requests; unauthorized source/group rejected; new data revision reflected; stale concurrent responses suppressed; AI unavailable state visible; valid citations rendered; invalid citations rejected; investigation returns actual calculations or a specific evidence gap. Record production verification separately from synthetic tests. Our public validation uses synthetic snapshots and stub MCP responses only.
