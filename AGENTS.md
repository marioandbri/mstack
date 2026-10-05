# mstack repository

This repository is canonical source for Mario's global instructions, managed workflow skills, sanitized defaults, installation and evaluations.

## Rules

- Edit skills here, never installed symlink paths as independent copies.
- Keep `skills.json`, `UPSTREAM.md`, and license notices aligned with imports.
- Preserve Agent Skills compatibility: valid frontmatter, matching directory/name, concise descriptions, and relative links.
- Keep skill entry points concise. Move detailed material into same skill directory.
- Use fish for installation scripts and Bun `1.3.14` for validation/tests.
- Installer must default to dry-run, back up conflicts, remain idempotent, install from commits and preserve unowned settings. Never deploy uncommitted source edits.
- Do not add external skill without license and provenance review.
- Do not add a dependency or CLI without exact version pin.
- Apply `unslop` to repository prose.
- Never edit generated changelogs.

## Verification

Before completion:

```fish
bun run check
bun test
fish install/verify.fish
```

`bun test` includes the Python installer suite against temporary Git sources and HOME directories. Keep that suite in the required checks; dry-run must make no home changes.

## Knowledge Gathered

### Ownership

- `skills.json` is the authoritative list of repository-owned workflow skills.
- Specialized frontend, browser, and package-provided skills remain external.
- Imported skills update through deliberate review, never automatic replacement.

### Local environments

- `local-env` owns environment-operation guidance and metadata-only helpers. Helpers never start/stop services or execute SQL; cleanup requires freshly verified ownership and no active consumers.
- Shared SQL containers identified by the user are `postgres` on `5432` and `mysql` with MySQL 8 on `3306`. When a task needs a stopped instance, verify current identity/image/bindings and start only that existing container. It remains shared and must stay running after cleanup. No automatic restart, recreation, or network/volume changes. The authorized MySQL binding uses all host interfaces; clients still connect through loopback and reports flag that exposure.
- Portless CLI baseline is `0.15.6` on Node.js `24+`. HTTP isolation E2E is opt-in via `env LOCAL_ENV_HTTP_E2E=1 bun test test/local-env-http.e2e.test.ts` and requires an already healthy loopback proxy. It does not establish SQL isolation acceptance.

### Benchmark isolation

- DeepSWE evaluation integration lives under `evals/deepswe`; Pier owns execution and grading.
- Benchmark ChatGPT OAuth uses `~/.local/share/mstack-evals/codex`, separate from the active Codex login. Keep credentials outside Git and evaluation artifacts; runs must serialize and preserve refreshed tokens before sandbox cleanup.
- Freeze instructions, skill content, dataset commit, task image digests, runtime versions and reasoning before A/B runs. Infrastructure errors and missing results are separate from verifier failures.
- An isolated Docker configuration must retain local CLI plugin directories for Compose without inheriting registry credentials or credential helpers. Preflight and execution must use the same runtime environment.
- The first comparison is unchanged global instructions versus the same instructions with repository-managed skills. Capture this baseline before instruction candidates or routing changes.

### Versioned installation

- `mstack.json` owns installation entries and keys; `skills.json` remains the only managed-skill inventory.
- `instructions/global/AGENTS.md` preserves the captured global instructions. Repository `AGENTS.md` is a separate maintenance entry point.
- Installed skills refer to readonly commit snapshots under `~/.local/share/mstack`; global instructions are a writable managed copy for the existing memory workflow. Detect local drift before updates or rollback rather than silently overwriting it.
- Codex owns only the declared model and reasoning defaults; Pi owns provider, model and thinking defaults. Preserve private settings, packages, extensions and credentials.
- `install/mstack_source.py` owns Git snapshots, `mstack_config.py` owned-key merges, `mstack_fs.py` private/atomic storage and `mstack.py` the transaction and CLI. TOML Kit is pinned in the installer lockfile to preserve shared TOML formatting.
- Candidate snapshots can be prepared without activation. Keep raw evaluation state and credentials outside Git; preserve execution-source hashes when reporting code changes after a run.
