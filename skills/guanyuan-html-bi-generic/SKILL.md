---
name: guanyuan-html-bi-generic
description: Design and adapt dynamic HTML BI dashboards for Guanyuan, and coordinate dataset binding, publication and same-ID updates through the companion CLI skill when platform delivery is requested.
---

# Guanyuan HTML BI

Identify whether the requested output is a static report or a dynamic dashboard. For dynamic dashboards, establish each dataset's grain, fields, units, scope semantics, update cadence and module consumers before implementing business calculations. Reuse confirmed requirements; ask only when missing information changes the result.

Keep complex business logic in the data layer. The frontend may adapt data, aggregate genuinely additive measures and render views. Never sum non-additive scope results or average ratios without considering denominators.

Treat SQL projection, dataset order, field definitions and frontend adapters as one versioned contract. A data refresh does not necessarily update schema or card bindings.

The conventional entrypoint is:

```javascript
function renderChart(data, clickFunc, config) {
  const container = document.getElementById('container');
  if (!container) return;
  // Validate and adapt the confirmed input shape, then render.
}
new GDPlugin().init(renderChart);
```

Verify that this interface exists in the user's platform version. Keep dataset identity explicit; validate names and equal column lengths. Do not silently turn missing or invalid numbers into zero. Escape data-derived markup. Handle empty data and scope changes, and replace stale event handlers on rerender.

Deliver a local preview, platform CSS/JavaScript and a dataset contract. Preserve the user's requested layout. Validate totals, units, trends and each required scope with authorized data in its permitted environment. Distinguish synthetic preview tests from platform acceptance.

Keep project-specific knowledge outside reusable skill code. Public examples must be generated from scratch; never publish production HAR, exports, SQL, screenshots or identifiers.

## Automated delivery

For platform dataset setup, publication or online updates, read [CLI delivery](references/cli-delivery.md) and use the companion `guanyuan-cli` skill. Continue from HTML design through platform acceptance within the requested scope; a code bundle alone is not a completed publishing task. For local preview only, no CLI installation or login is needed. Preserve the standalone preview workflow and existing data-contract checks.
