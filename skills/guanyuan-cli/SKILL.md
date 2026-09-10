---
name: guanyuan-cli
description: Install and use official Guandata CLI tools to inspect resources, configure datasets, create or update dashboards, and verify publication. Use with the HTML BI skill for automated HTML dashboard delivery.
---

# Guanyuan CLI

Operate the user's Guanyuan environment through official CLI components. This community skill orchestrates the tools; it does not bundle vendor binaries, credentials, or tenant defaults.

## Setup and routing

Read [setup.md](references/setup.md) for installation, version discovery and authentication. Use existing tools when suitable; install missing dependencies from verified official sources. Run `python3 <this-skill>/scripts/doctor.py` to check local component startup without logging in or changing BI resources. A successful check does not prove server compatibility.

| Work | Component |
| --- | --- |
| Inspect pages, cards, fields and data | `guancli` |
| Data sources, datasets, schema, refresh and schedules | `guands` |
| Native or custom charts, selectors, page layout and publication | `guanvis` |
| ETL development and execution | `guanetl` |
| Workflow operations | `guanwf` |
| Metric platform operations | `guanmetric` |

Read the installed component's official skill and relevant command help before operating it. Load only components required by the task. For HTML design or adaptation, use `guanyuan-html-bi-generic` when available; the CLI workflow can also accept already prepared HTML/CSS/JS and a data contract.

## Environment and resource identity

Read [configuration.md](references/configuration.md). Resolve settings from the explicit request, then private project configuration, then private user configuration. No built-in tenant, directory, country or preferred data source exists. Match the authenticated instance to the target before writes; resolve real directory and connection IDs instead of guessing from names. Dataset and page directories are separate trees.

Preserve resource IDs, bindings, connections and location when editing existing resources unless the user requested a change. For new resources, resolve location and source from the task and configuration; ask only for unresolved choices. Installing the skill does not authorize future production operations. Existing task authorization covers the requested operations without repeated generic confirmations.

## Execution and completion

Follow [delivery.md](references/delivery.md) for dataset preparation, HTML binding, publishing and subsequent updates. Use supported preview/dry-run/plan commands to inspect intended changes. Keep source projects and resource mappings in a private project directory outside this public toolkit. Never modify generated snapshots or manually reconstruct vendor resource archives.

If a command fails after a possible write, inspect the target before retrying. Report partial completion and stop dependent writes when state cannot be established. A local preview, accepted upload, or HTTP success alone is not platform acceptance. Verify stored configuration, real data and visible behavior. Keep production evidence private; public examples and bug reproductions must be newly synthesized.
