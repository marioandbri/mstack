# mstack

Versioned source for Mario's global instructions, managed engineering skills, sanitized model defaults, installation and evaluations.

`AGENTS.md` governs work on this repository; `instructions/global/AGENTS.md` is the global file distributed to other projects. `mstack.json` describes installation and references `skills.json` without duplicating its inventory.

## Supported harnesses

| Harness | Installed path |
| --- | --- |
| Agent Skills common root | `~/.agents/skills/<name>` |
| Claude Code | `~/.claude/skills/<name>` |
| Codex | `~/.codex/skills/<name>` |
| Pi | `~/.pi/agent/skills/<name>` |

The managed installer links skills to a readonly commit snapshot. Development edits do not change the active installation. Global instructions remain a managed copy so the existing memory workflow stays writable; the verifier detects local drift.

## Workflow

```text
govern project docs
  -> grill decisions
  -> write spec
  -> write tickets
  -> triage
  -> diagnose or implement with TDD
  -> review standards and spec
  -> run structural review when requested
  -> verify before completion
  -> hand off
```

`skills.json` is managed-skill manifest and provenance index.

## Installation

Choose one method. Do not combine Skills CLI and clone-based installation for same skill names on same machine; both manage target paths and ownership metadata.

### Skills CLI

Recommended for using skills without maintaining repository checkout. Repository is private, so Git and GitHub access must already work through SSH, credential helper, or authenticated GitHub CLI.

List available skills without installing:

```fish
bunx skills add git@github.com:marioandbri/mstack.git --list
```

Install one skill globally and let CLI prompt for target agents:

```fish
bunx skills add git@github.com:marioandbri/mstack.git \
  --skill setup-conventions-aware-engineering \
  --global
```

Install one skill globally for Pi without prompts:

```fish
bunx skills add git@github.com:marioandbri/mstack.git \
  --skill setup-conventions-aware-engineering \
  --agent pi \
  --global \
  --yes
```

Install every skill for every agent supported by CLI:

```fish
bunx skills add git@github.com:marioandbri/mstack.git \
  --global \
  --all
```

Omit `--global` for project-local installation. Use `--copy` only when target agent cannot follow symlinks. Review skills before installation; they run with agent permissions.

### Managed installation from a clone

Use this method for the complete system. [Installation and rollback](install/README.md) documents ownership, snapshots, custom directories and recovery.

```fish
git clone git@github.com:marioandbri/mstack.git
cd mstack
bun install --frozen-lockfile
uv sync --locked --project install
bun run check
bun test
fish install/setup.fish --ref HEAD
fish install/setup.fish --ref HEAD --apply
fish install/verify.fish
```

The first setup command is a dry-run. Apply the same reviewed commit explicitly. Conflicts are backed up privately under `~/.local/share/mstack/backups/`. The active version lives under `~/.local/share/mstack/versions/<commit>/`. Reapplying a verified version is idempotent.

Only the declared model defaults are merged into shared Codex and Pi settings; other values are preserved. OAuth, sessions, logs, caches and machine overrides remain outside Git.

Use `fish install/rollback.fish` to inspect rollback and add `--apply` to perform it. Local edits and damaged backups stop rollback before changes.

## Verify

```fish
bun run check
bun test
fish install/verify.fish
```

`bun run check` validates:

- manifest and directory agreement;
- Agent Skills frontmatter;
- unique names;
- nonempty descriptions;
- relative Markdown links;
- provenance and license coverage.

`install/verify.fish` checks the active snapshot, managed instructions, all harness links, owned application defaults, duplicate names and upstream ownership conflicts.

## Pi package

Repository is valid local Pi package through `package.json`:

```fish
pi --no-skills --skill ./skills/code-review --list-models __validation__
```

Managed installation uses snapshot links. Do not also run `pi install` for this repository, because Pi already discovers installed links and duplicate names would depend on discovery order.

## Local environment skill

`local-env` guides application launch and integration/E2E environments through Portless `0.15.6`, reusing shared SQL servers with `existing` or `disposable` databases. Bundled helper records private metadata and checks ownership eligibility; it never executes SQL or starts/stops application services.

[Skill instructions](skills/local-env/SKILL.md) describe configuration inspection, effective-target checks, reuse, and owned-resource cleanup. Run opt-in HTTP isolation test only with an already healthy loopback proxy:

```fish
env LOCAL_ENV_HTTP_E2E=1 bun test test/local-env-http.e2e.test.ts
```

This checks two real application workspaces and independent process cleanup. Full SQL isolation acceptance additionally requires an authorized project connection, migrations/fixtures, and actual disposable databases. Do not substitute metadata tests for that acceptance.

## Updating a skill

1. Change canonical copy under `skills/`.
2. Run checks and relevant behavior tests.
3. Update `skills.json` provenance when importing upstream changes.
4. Record meaningful divergence in `UPSTREAM.md`.
5. Commit the candidate, prepare its snapshot, evaluate it and explicitly install that commit before using it across projects.

Never run bulk upstream skill updates against managed names. Review upstream changes and port them deliberately.

## Reflect and observation capture

`capture-observations` records findings during active work; `reflect` reviews them when explicitly requested. Both are managed together because capture uses Reflect's shared classification, record contract and observation schema. Their procedures match the evaluated persistence candidate; the earlier copies under `docs/agent-maintenance/candidates/` retain that evaluation state and are not the maintained source.

Maintain the installed sources under `skills/capture-observations/` and `skills/reflect/`. [Persistence layout](docs/agent-maintenance/persistence.md) explains the inbox, decisions, proposals and evidence. Capturing and saving a proposal do not activate instruction changes. Automatic capture is an agent behavior during a session, not a background listener or guaranteed monitoring of every chat.

## External skills

Framework, browser, frontend-design, and package-provided skills remain externally managed. They are not copied here. Pi package filters should exclude duplicate names owned by this repository.

## Licensing

Original repository work is MIT licensed. Imported skills retain upstream MIT notices. See `THIRD_PARTY_NOTICES.md` and `licenses/`.

## Evaluations

[DeepSWE with Codex and Pier](evals/deepswe/README.md) prepares fixed A/B profiles and uses a separate ChatGPT login. The [first local pilot](evals/deepswe/reports/pilot-local.md) records both timeouts and consumption; it validates integration rather than proving a quality difference. Instruction candidates, skill changes and Laya routing are separate later experiments.
