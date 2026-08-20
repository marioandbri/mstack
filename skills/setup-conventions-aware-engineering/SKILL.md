---
name: setup-conventions-aware-engineering
description: Configures repository documentation routing, ownership, conventions, domain docs, issue-tracker guidance, and agent entry points. Use manually when adopting conventions-aware engineering, creating docs/agents/documentation-map.md, or repairing an inconsistent engineering documentation layout.
disable-model-invocation: true
---

# Setup conventions-aware engineering

Scaffold repository contract consumed by `conventions-aware-engineering` and specialist engineering skills. This workflow edits project documentation, so inspect first and confirm before writing.

## Process

### 1. Explore

Read existing state without assuming layout:

- repository root, applications, packages, and deployable units;
- `AGENTS.md`, `CLAUDE.md`, and package-local instruction files;
- `docs/`, contributing guides, architecture docs, and standards;
- `CONTEXT.md`, `CONTEXT-MAP.md`, and ADR locations;
- git remotes, issue tracker guidance, and triage labels;
- build, test, code-generation, and deployment commands.

### 2. Classify existing documents

Assign each document one owner category from [DOCUMENT-LAYOUT.md](DOCUMENT-LAYOUT.md). Flag duplication, unclear authority, stale links, and mixed concerns. Preserve useful content. Do not rename or move files before approval.

### 3. Resolve decisions one at a time

Explain and confirm:

1. canonical agent instruction file or files;
2. single-context or multi-context domain layout;
3. technical convention scopes such as workspace, API, web, and design;
4. issue tracker and triage vocabulary;
5. document ownership, precedence, and task routing;
6. required local verification by scope.

Infer defaults from repository, but ask when evidence conflicts.

### 4. Draft

Show exact proposed changes before writing:

- small documentation-routing block for canonical agent instructions;
- `docs/agents/documentation-map.md`;
- `docs/agents/domain.md`;
- `docs/agents/issue-tracker.md` and `triage-labels.md` when tracker workflows need them;
- conventions only for confirmed scopes with real rules.

Use [DOCUMENTATION-MAP-TEMPLATE.md](DOCUMENTATION-MAP-TEMPLATE.md) as shape, not content to copy blindly. Use [TRACKER-AND-DOMAIN.md](TRACKER-AND-DOMAIN.md) when those integrations apply.

### 5. Write safely

After approval:

- update existing sections in place;
- link instead of duplicating rules;
- do not overwrite unrelated user content;
- do not create empty `CONTEXT.md`, ADR, convention, discovery, or runbook files;
- keep product behavior out of technical conventions;
- keep procedures out of ADRs and conventions;
- validate every new relative link and route-table path.

### 6. Verify

Report files created or changed, unresolved gaps, and specialist skills now able to consume layout. Recommend direct edits later; rerun setup only for structural changes.
