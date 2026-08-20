# Upstream provenance

`skills.json` contains exact imported path and content hash or commit. This document records ownership policy and known divergence.

## Matt Pocock skills

Source: <https://github.com/mattpocock/skills>

Imported skills:

- `caveman`
- `code-review`
- `diagnose`
- `grill-me`
- `grill-with-docs`
- `handoff`
- `implement`
- `improve-codebase-architecture`
- `tdd`
- `to-spec`
- `to-tickets`
- `triage`
- `wayfinder`
- `write-a-skill`
- `zoom-out`

Local divergence:

- `code-review` loads routed conventions and supports explicit thermo structural axis.
- `improve-codebase-architecture` respects project conventions, ADR authority, and project vocabulary.
- tracker-facing skills use `setup-conventions-aware-engineering` instead of old setup command.

## Cursor Team Kit

Source: Cursor public `cursor-team-kit` plugin.

Imported skill: `thermo-nuclear-code-quality-review`.

Local divergence: governing context constrains remedies, project vocabulary wins, and 1k-line threshold no longer forces shallow decomposition.

## pstack unslop

Source: <https://github.com/cursor/plugins/tree/main/pstack/skills/unslop>

Imported skill: `unslop`.

No known local divergence at import.

## Superpowers

Source: <https://github.com/obra/superpowers>

Imported skills:

- `receiving-code-review`
- `verification-before-completion`

No known local divergence at import.

## Kun Chen tools

Sources:

- <https://github.com/kunchenguid/gh-axi>
- <https://github.com/kunchenguid/lavish-axi>

Imported skills:

- `gh-axi`
- `lavish`

CLI implementations remain external dependencies. Skill ownership here controls invocation and workflow policy, not CLI source. `gh-axi` invocation is pinned to `0.1.30` and uses `bunx`.

## Repository-owned skills

- `conventions-aware-engineering`
- `setup-conventions-aware-engineering`
- `visual-companion`

These originated in Mario's local workflow and have no external update stream.

## Update policy

1. Fetch upstream skill and license.
2. Compare against current canonical copy.
3. Port useful changes manually.
4. Preserve local workflow contracts.
5. Update `skills.json` import reference and this file when divergence changes.
6. Run full validation before commit.
