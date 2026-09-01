# Engineering skills

Canonical repository for Mario's cross-harness engineering workflow.

Canonical source files live here. Installation method controls whether agent targets use links or managed copies.

## Supported harnesses

| Harness | Installed path |
| --- | --- |
| Agent Skills common root | `~/.agents/skills/<name>` |
| Claude Code | `~/.claude/skills/<name>` |
| Codex | `~/.codex/skills/<name>` |
| Pi | `~/.pi/agent/skills/<name>` |

Skills CLI supports these harnesses directly. Clone-based installation links each target to `skills/<name>` in checkout and uses `~/.agents/skills` as common cross-tool source.

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

### Cloned repository

Use this method when developing skills or keeping checkout as canonical local source.

```fish
git clone git@github.com:marioandbri/mstack.git
cd mstack
fish install/setup.fish
```

`fish install/setup.fish` runs in dry-run mode. Apply after reviewing plan:

```fish
fish install/setup.fish --apply
```

Installer requires Fish and `jq`. Conflicting files, directories, and symlinks move under:

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
