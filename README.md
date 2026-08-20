# Engineering skills

Canonical repository for Mario's cross-harness engineering workflow.

Source files live here. Installed skill directories are symlinks and must not become independent copies.

## Supported harnesses

| Harness | Installed path |
| --- | --- |
| Agent Skills common root | `~/.agents/skills/<name>` |
| Claude Code | `~/.claude/skills/<name>` |
| Codex | `~/.codex/skills/<name>` |
| Pi | `~/.pi/agent/skills/<name>` |

Each target resolves to `skills/<name>` in this repository. `~/.agents/skills` remains common cross-tool source, while explicit harness links make installation testable and independent of implicit discovery changes.

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

## Install

Inspect planned changes:

```fish
fish install/setup.fish
```

Apply after reviewing output:

```fish
fish install/setup.fish --apply
```

Conflicting files, directories, and symlinks move under:

```text
~/.engineering-skills-backups/<timestamp>/
```

Correct links remain unchanged. Re-running apply mode is idempotent.

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

`install/verify.fish` checks every harness link against canonical repository.

## Pi package

Repository is valid local Pi package through `package.json`:

```fish
pi --no-skills --skill ./skills/code-review --list-models __validation__
```

Normal installation uses symlinks. Do not also run `pi install` for this repository, because Pi already discovers installed links and duplicate names would depend on discovery order.

## Updating a skill

1. Change canonical copy under `skills/`.
2. Run checks and relevant behavior tests.
3. Update `skills.json` provenance when importing upstream changes.
4. Record meaningful divergence in `UPSTREAM.md`.
5. Commit repository before using new version across projects.

Never run bulk upstream skill updates against managed names. Review upstream changes and port them deliberately.

## External skills

Framework, browser, frontend-design, and package-provided skills remain externally managed. They are not copied here. Pi package filters should exclude duplicate names owned by this repository.

## Licensing

Original repository work is MIT licensed. Imported skills retain upstream MIT notices. See `THIRD_PARTY_NOTICES.md` and `licenses/`.
