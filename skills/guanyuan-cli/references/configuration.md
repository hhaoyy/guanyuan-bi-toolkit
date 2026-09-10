# Private configuration

This is a configuration contract read by the agent, not a file automatically consumed by official CLI commands. Translate resolved values into the installed CLI's supported profile, directory and connection options. Never pass this JSON to the vendor as an API payload.

Look for project settings at `local/guanyuan.json` within the user's business project, then user settings at `~/.config/guanyuan-bi-toolkit/settings.json`, unless the user supplies another path. Both are private; project `local/` is ignored by this repository. Precedence is per field: explicit task value > project value > user value. An explicit null clears an inherited preference. Credentials belong in the CLI's supported authentication store, not either file.

A portable empty template:

```json
{
  "instance_url": null,
  "profile": null,
  "dataset_directory": null,
  "dashboard_directory": null,
  "data_source_id": null,
  "region": null,
  "preferred_data_source_name": null
}
```

- Directory preferences are paths to resolve against the current instance, not global IDs. A supplied ID must also be checked in that instance.
- Region is optional, supplied by the user's business task. It is not inferred from language or the machine's location. Match region and required data access before applying any name preference.
- If several data sources still qualify, use metadata and task evidence to narrow them; otherwise ask for that choice. Never silently choose the first result or fall back to another region.
- Resolve page and dataset paths separately. If a required child directory is absent, creation within an identified parent can be part of an authorized creation task. Do not silently use another location when parent identity or permissions are unresolved.
- These are creation preferences. They do not relocate an existing page or replace an existing dataset's connection.

The toolkit contains no organization-specific default values. Never commit filled settings, CLI credential stores, exported schema, resource IDs, private SQL or publishing evidence to this public repository.
