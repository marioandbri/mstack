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

- `code-review` loads routed conventions, supports explicit thermo structural axis, and adds the immutable `candidate.v1` request branch without changing fixed-point mode.
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

- <https://github.com/kunchenguid/chrome-devtools-axi>
- <https://github.com/kunchenguid/gh-axi>
- <https://github.com/kunchenguid/lavish-axi>

Imported skills:

- `chrome-devtools-axi`
- `gh-axi`
- `lavish`

CLI implementations remain external dependencies. Skill ownership here controls invocation and workflow policy, not CLI source. `gh-axi` invocation is pinned to `0.1.30` and uses `bunx`.

Chrome local divergence:

- Reviewed skill and MIT license at commit `06688b18adf5c0855fca6ed4efe2dbd0ad0e2ec6`. The notice matches `licenses/MIT-Kun-Chen.txt`.
- Replaces unpinned upstream npx invocations with installed AXI `0.1.35` and MCP `1.9.0`; CLI implementations are not imported or upgraded.
- Moves Mario's headless, session, tab, profile and process ownership requirements into a mandatory skill reference. The active global remains unchanged until the consolidated instruction proposal is reviewed and deployed.
- Narrows discovery to real browser work, respecting explicit tool choices, with normal automatic selection enabled. Normalizes upstream author metadata and omits the nonstandard `user-invocable` field; Codex invocation policy is declared in `agents/openai.yaml`. Cross-harness selection still requires behavioral validation.
- Existing externally installed source came from folder hash `624f2f8c26da9f9ac6bca30136fb3b54f53e60a2` in the local upstream installer lock. This candidate uses the reviewed commit above instead of claiming that folder hash identifies it.

## Repository-owned skills

- `capture-observations`
- `reflect`
- `conventions-aware-engineering`
- `local-env`
- `repository-workflow`
- `mobile-next-android-testing`
- `setup-conventions-aware-engineering`
- `visual-companion`

These originated in Mario's local workflow and have no external update stream.

## Cross-harness normalization

Internal skill references use skill names instead of Pi-specific slash commands. Delegation instructions refer to harness-available mechanisms rather than one tool API.

## Agent-maintenance candidate changes

- grill-with-docs separates interview completion from route selection; direct execution after an interview requires the user's request.
- implement preserves explicit invocation and artifact execution. The original repository-workflow skill coordinates the broader worktree-to-PR lifecycle and calls existing specialists.
- tdd and diagnose reuse approved test boundaries and retain functional smoke/regression evidence. diagnose holds scoped environment facts, not new Pi/Bitbucket/T3 skills.
- to-spec and to-tickets preserve the interview's decisions and exclusions without repeating resolved testing approvals.
- caveman requires explicit mode requests and respects the requested duration. unslop adjusts natural writing to the purpose. lavish discovery and body both require requested or accepted hi-fi review. Lavish and visual-companion Codex policy mirrors their existing explicit-only frontmatter.

## Update policy

1. Fetch upstream skill and license.
2. Compare against current canonical copy.
3. Port useful changes manually.
4. Preserve local workflow contracts.
5. Update `skills.json` import reference and this file when divergence changes.
6. Run full validation before commit.
