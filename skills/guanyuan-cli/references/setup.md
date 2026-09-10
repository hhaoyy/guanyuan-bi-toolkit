# Official CLI setup

Start at the [official help center](https://www.guandata.com/help) and the vendor's published package documentation. Verify current platform support, Node requirements and installation instructions before installation. Package versions can differ between components; record the actual versions used in the private project.

Official package references:

- [guancli](https://www.npmjs.com/package/@guandata/guancli)
- [guands](https://www.npmjs.com/package/@guandata/guands)
- [guanvis](https://www.npmjs.com/package/@guandata/guanvis)
- [guanetl](https://www.npmjs.com/package/@guandata/guanetl)
- [guanwf](https://www.npmjs.com/package/@guandata/guanwf)
- [guanmetric](https://www.npmjs.com/package/@guandata/guanmetric)

Inspect package metadata with `npm view <package> version engines os cpu dist.integrity` and read its README. Verify the selected release rather than blindly updating an existing installation. For an explicitly requested full six-component setup, the documented npm installation pattern is:

```bash
npm install -g --foreground-scripts @guandata/guancli @guandata/guands @guandata/guanvis @guandata/guanetl @guandata/guanwf @guandata/guanmetric
```

For a smaller task, reuse the installation and install only missing required components. Where global installation is unavailable, use a user-selected private prefix and its bin directory according to npm/platform documentation. Do not hardcode a workstation path or copy someone else's installed binaries. Inspect install output: official packages may refresh their own component skills through postinstall. Retain those as version-matched API references alongside this orchestration skill; do not overwrite this skill with them. Follow current vendor guidance for `install-skill` if documentation was not installed.

After installation:

1. Run `doctor.py`; it checks all six by default, or use `--components guancli guands guanvis` for HTML work. Missing unrelated components do not block the requested subset.
2. Read `guancli auth --help` and `guancli auth status`. Reuse a suitable existing profile, otherwise follow the current login flow with information supplied by the user. Keep secrets out of command history, generated code and public logs; prefer supported interactive login or secret input.
3. Query a minimal authorized resource to verify connectivity and identity. Keep output private. Record separately: installed version, authenticated instance, read access, and operations actually tested.

Do not assume the newest client supports every server release. When a feature fails, identify the affected user action and available alternative. Do not turn one unsupported endpoint into a claim that all publishing fails. CLI help and package docs take precedence over examples here if syntax changes. Vendor packages retain their own licenses; this repository's MIT license does not relicense them.
