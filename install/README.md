# Installing mstack

The installer reads `mstack.json` and `skills.json` from a Git commit. Uncommitted source edits never reach the active installation.

It uses Python `3.13.2` and TOML Kit `0.15.1`, locked in `uv.lock`. [TOML Kit](https://pypi.org/project/tomlkit/0.15.1/) preserves comments, whitespace and ordering while editing the owned Codex defaults. JSON configuration preserves unowned values; formatting can change when owned values change.

## Install and verify

From the repository root:

```fish
uv sync --locked --project install
bun run check
bun test
fish install/setup.fish --ref HEAD
fish install/setup.fish --ref HEAD --apply
fish install/verify.fish
```

Select a reviewed commit with `--ref <commit>`. Setup defaults to dry-run and reports target changes without creating state or modifying your home. Apply backs up conflicts under `~/.local/share/mstack/backups/<generation>/` and records the installation privately. Reapplying the same verified version makes no changes.

A first installation replaces the old checkout links with links through `~/.local/share/mstack/active/skills/<name>`. The active pointer switches to a readonly commit snapshot. External skill names and Pi packages remain under their current owners.

Global instructions are a managed, writable copy at `~/.agents/AGENTS.md`; Codex and Pi refer to that file. Claude keeps its small wrapper. This preserves the existing global-memory workflow. A later local edit is detectable drift: installation and rollback stop before overwriting it. Reconcile the local content deliberately with the source and last installed version before updating; neither operation automatically merges global instructions.

Only these application keys belong to mstack:

| File | Owned keys |
|---|---|
| Codex `config.toml` | `model`, `model_reasoning_effort` |
| Pi `settings.json` | `defaultProvider`, `defaultModel`, `defaultThinkingLevel` |

Credentials, trusted projects, MCP configuration, packages, extensions and other settings stay in their existing files. Credentials and raw configuration backups never belong in Git. The state directory and backups are private to the user.

## Candidate snapshots for evaluation

```fish
uv run --locked --project install python install/mstack.py snapshot --ref HEAD
uv run --locked --project install python install/mstack.py snapshot --ref HEAD --apply
```

The command prints the snapshot directory. It does not activate the candidate. Pass its `instructions/global/AGENTS.md` and `skills/` directories to the [DeepSWE preparation command](../evals/deepswe/README.md). Keep model, reasoning and evaluation budgets explicit. Install that same commit only after reviewing the evaluation.

## Rollback and recovery

```fish
fish install/rollback.fish
fish install/rollback.fish --apply
```

Rollback defaults to dry-run and checks drift and backup integrity before the first change. It restores the previous owned state, preserving later edits to unowned application keys. The first installation can be undone to the original files, directories and links. If an original checkout-linked skill changed since installation, restoring that mutable source is refused.

An interrupted transaction retains a journal. Inspect its recovery plan, then apply it:

```fish
uv run --locked --project install python install/mstack.py recover
uv run --locked --project install python install/mstack.py recover --apply
```

Snapshots and private receipts remain available after rollback. The installer serializes state mutations and refuses overlapping operations. It does not start or stop application, Docker or SQL services.

## Different directories

`--home <directory>` gives a completely separate home layout and ignores ambient agent-directory variables. This is used by the real installation tests.

Without `--home`, the installer respects `CODEX_HOME`, `CLAUDE_CONFIG_DIR` and `PI_CODING_AGENT_DIR`. Explicit `--agents-dir`, `--codex-dir`, `--claude-dir`, `--pi-dir` and `--state-dir` take precedence. Instruction override files are detected rather than replaced.

Machine-specific directory overrides can live in `mstack.local.json`, which is excluded from Git:

```json
{
  "directories": {
    "codex": "/absolute/path/to/codex-profile"
  },
  "stateDir": "/absolute/path/to/mstack-state"
}
```

A managed installation records its directories. Changing them later requires a separate state or deliberately undoing the original installation; the installer does not abandon owned targets silently.

## Tests

`bun test` includes the real installer suite. It creates separate temporary Git repositories and homes, exercises all four harnesses, verifies that dry-run changes nothing, and covers shared settings, readonly snapshots, idempotence, upgrades, drift, backups, rollback, transaction failure, recovery, duplicate ownership, overrides and concurrent operations.

Run the suite independently with:

```fish
uv run --locked --project install python -m unittest discover -s install -p test_mstack.py -v
```
