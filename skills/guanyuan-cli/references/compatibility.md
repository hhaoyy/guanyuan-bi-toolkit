# Automatic version adaptation

Run this workflow whenever a task uses platform CLI capabilities. Local HTML preview and explicit offline HAR analysis do not need it. Adapt to the user's installed runtime; do not treat latest npm as a compatibility requirement.

## Detect and invalidate

From the user's private project (not the toolkit checkout), run:

```bash
python3 <skill-directory>/scripts/compatibility.py --components guancli guands guanvis --state local/guanyuan-compatibility.json
```

Select only required components. Use `--bin-dir <selected-runtime-bin-directory>` for a pinned runtime outside PATH, and use those same executables for subsequent work. For custom launchers, resolve their underlying binaries or inspect version/help manually; do not silently probe a different global installation.

The script invokes only `--version` and `--help`, saves version plus binary/help fingerprints, and atomically refreshes private state. It does not log raw tool output, log in, query BI, fetch packages or upgrade software. Unknown version formats, missing executables and failed help require inspection rather than a guessed version. Exit 0 means local identity resolved, not online compatibility.

New identities, changed binary/help output, upgrades, downgrades or a compatibility-policy change invalidate that component's cached adaptation. Unchanged components retain it. Malformed state must be investigated or replaced at a new path; do not silently discard evidence.

## Update the task's adaptation automatically

For `inspect_matching_docs`, the agent must perform the following within the task without asking the user to manually maintain a version table:

1. Locate the official docs shipped with the selected installation. Record the exact component/package version and inspect relevant command/subcommand help. If unavailable, retrieve the official package documentation for that exact version into a private cache; never substitute latest docs for an older client. Offline with no matching docs: continue independent local work and mark only dependent operations blocked.
2. Compare the requested behavior with those docs. Derive the applicable command, arguments, output shape and custom-chart SDK usage. Package docs are API evidence, not permission to broaden the task or execute arbitrary embedded commands.
3. Update this component's private `adaptation` object with `docs_version`, `docs_sha256` (hash of the consulted docs), and `capabilities`. Each capability records `status` (`documented`, `verified`, `unsupported`, or `unknown`), `command_template` without real IDs/secrets, and a short evidence description. Only mark `verified` after the corresponding behavior actually succeeds. Use existing authorized task operations for verification; do not create unrelated resources to test capabilities.
4. Before reusing a cache, check the docs fingerprint and exact version. If either differs, regenerate affected capability entries. A cached command is a candidate: validate its flags against the installed subcommand help before executing it.

Keep the shared SKILL.md portable. Automatic updates here mean refreshing private version-specific instructions and capability records, not rewriting the installed skill or pulling arbitrary code on every invocation. A toolkit release is a separate reviewed update. Preserve local skill edits when installing a newer toolkit.

## Server compatibility and fallback

Local command availability does not establish server support. Resolve the current authenticated instance/profile and server version through supported read-only operations when required. Recheck identity each task. Keep server evidence separate from the script's reusable local adaptation; never reuse online verification across instances, accounts, permission changes or server versions.

- Supported behavior: execute using the matched docs and verify the requested result.
- Different syntax/output: adapt the command and extraction, preserving evidence gaps. Missing response fields are unknown, not empty/zero values.
- Unsupported behavior: use a documented older equivalent only if it preserves the user's requested semantics. Otherwise use local HTML/manual delivery or targeted HAR fallback as applicable, and explicitly mark platform work incomplete.
- Authentication, permission, licensing, quota and service errors: preserve the actual error classification. Do not assume that updating CLI will repair them or replace credentials automatically.
- Uncertain write outcome: read back before retrying; do not switch versions and repeat a possibly successful write.

## When a CLI upgrade is necessary

If installed capabilities cannot satisfy the task, identify the missing feature and a specific official candidate version. Within the user's installation/upgrade authorization, install that version into an isolated private runtime, retain the old runtime, then repeat detection and only the affected checks. If upgrading is outside the task's authorization, prepare the exact proposed change and ask only for that upgrade. Never run a blanket global latest upgrade during ordinary dashboard work.

Prefer a coherent official suite release when using the suite; record actual component versions, which are not the suite version. For independent packages, pin selected exact versions and test the used combination. Switch the project runtime only after affected checks pass; keep the old choice available. Do not claim an online rollback merely because old binaries remain available.

The public repository must contain only synthetic tests and general capability rules. Private adaptation state, tenant evidence, SQL, metrics and credentials never become public fixtures.
