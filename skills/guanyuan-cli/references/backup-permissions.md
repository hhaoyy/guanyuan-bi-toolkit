# Backup-export permission fallback

Use for an already authorized same-ID dashboard update blocked specifically by the CLI's pre-overwrite resource-export backup permission. Do not repeatedly ask the user to obtain backup/export permission or reconfirm that same authorized edit. Existing explicit requirements to produce a backup still apply; if the user requires one, resolve that requirement before overwriting.

## Decide from the failed stage

Confirm the intended instance, page IDs, source project and existing authorization. Inspect the actual error and stage: lack of backup-export permission is distinct from lack of page update/import permission. A timeout, generic 403, authentication error, quota error or unknown write outcome is not sufficient evidence to skip backup. If the write may have started, reconcile online state before retrying.

When the blocker is confirmed to be backup export and the selected version supports the escape hatch:

1. Preserve available local source and snapshots. Describe that this update will have no new CLI pre-overwrite export backup; local source is not guaranteed to restore all online state. Do not require a new export using the same unavailable permission.
2. Check the installed version's relevant docs/help or implementation evidence for the skip mechanism. `GUANVIS_SKIP_OVERWRITE_BACKUP=1` is an environment variable, not a `--skip-backup` CLI flag. Help omission alone does not prove absence. Do not patch the vendor binary or fabricate flags.
3. Keep the original target, profile and runtime. Use the setting for this single invocation only, together with the explicit overwrite flag:

   ```bash
   GUANVIS_SKIP_OVERWRITE_BACKUP=1 guanvis publish <project-directory> --allow-overwrite
   ```

   Replace `guanvis` with the exact selected executable or existing launcher. Do not persist the variable globally. Run the applicable preview/dry-run and resource checks; the option skips only the export backup, not page permissions, drift checks, resource integrity or server validation.
4. Continue the authorized update without another generic backup confirmation. Read back the saved configuration, bindings and affected behavior; report whether the update succeeded and that the new export backup was skipped. On a further failure, inspect its stage and state instead of blindly retrying or switching accounts/browsers.

If support is unknown or absent, record the precise missing capability. Inspect a supported candidate runtime under the version-adaptation workflow; do not assume that setting an ignored environment variable fixes the blocker. Do not disable another safety check as a substitute. A resource-specific workflow that explicitly requires a backup for preservation cannot be treated as this ordinary permission fallback without resolving that constraint.

## Public evidence, checked 2026-10-30

- Official `@guandata/guanvis` **0.1.60** README and bundled `skills/guanvis/references/publish-and-constraints.md` still describe automatic backup before `--allow-overwrite`, with backup failure/timeout aborting the upload. They do not claim that ordinary users always possess backup-export permission.
- The integrity-verified official `@guandata/guanvis-darwin-arm64` **0.1.60** binary contains `GUANVIS_SKIP_OVERWRITE_BACKUP`. This confirms the marker remains in that artifact; it is not an online acceptance test or a guarantee for every platform/build. No new live publication was performed for this documentation change.
- Binary SHA-256: `3537599963f6f50fcaa21e5f8f9086bb0c355d76ce7bbeb825a36cb99cb2cba6`.
- Sources: [official GuanVis package](https://www.npmjs.com/package/@guandata/guanvis/v/0.1.60), [exact package metadata](https://registry.npmjs.org/@guandata%2fguanvis/0.1.60), [exact Darwin ARM64 artifact metadata](https://registry.npmjs.org/@guandata%2fguanvis-darwin-arm64/0.1.60).

Treat newer versions according to their actual implementation and docs. Do not generalize this fallback into skipping all backups for all operations.
