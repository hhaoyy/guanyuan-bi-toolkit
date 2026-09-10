# Automated platform delivery

Use the companion `guanyuan-cli` skill for a request to connect data, publish, or modify an online dashboard. If absent, install `skills/guanyuan-cli` from https://github.com/hhaoyy/guanyuan-bi-toolkit using the current agent's skill installation mechanism, preserving the full folder. If installation is unavailable, read the same repository skill and references directly. Do not claim that copying a skill also installed or authenticated the vendor CLI.

Keep the HTML skill as the user's entrypoint. Hand the CLI workflow:

- Requested instance and target location, or private configuration to resolve them.
- Platform HTML/CSS/JS without mock loaders or local-only controls.
- Ordered dataset roles, fields, grain, units, aggregation and sort contract.
- Required filters and whether they operate on loaded rows or query platform data.
- Existing resource IDs and source project when updating, plus intended changes.

Follow the companion's setup and delivery references to prepare datasets, bind SDK data views, publish and inspect the actual page. Resolve resources before writing environment-specific bindings. Keep business SQL, settings, generated projects, IDs and evidence in the user's private project.

The full acceptance cycle includes first publication and a later same-ID update when validating the integration itself. For routine tasks test only the requested changes. Local synthetic preview proves frontend behavior; it does not prove the tenant's SDK support, actual query shape or publication. When credentials or platform access are missing, finish the independent preview and contract and clearly state which online step remains blocked.
