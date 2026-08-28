---
name: setup-conventions-aware-engineering
description: Guided setup for documentation routing, conventions, domain context, design, architecture, tracker guidance, and agent entry points. Adapts its proposal to greenfield and brownfield repositories.
disable-model-invocation: true
---

# Setup conventions-aware engineering

Build the repository contract consumed by `conventions-aware-engineering` and specialist skills. This workflow edits broad project documentation. Explore first, guide one decision at a time, and obtain approval before writing.

## Process

### 1. Establish repository posture

Read [REPOSITORY-POSTURE-AND-STACK.md](REPOSITORY-POSTURE-AND-STACK.md). Inspect repository history and current state, then record concrete evidence for greenfield or brownfield. Do not persist lifecycle classification. If evidence is ambiguous, present it and ask the user to choose before continuing.

Inventory:

- applications, workspace packages, deployable units, source, tests, migrations, and generated contracts;
- manifests, lockfiles, workspace definitions, framework config, build scripts, and deployment config;
- installed skills and their repository configuration needs;
- `AGENTS.md`, `CLAUDE.md`, package-local instructions, existing docs, context maps, and ADRs;
- remotes, tracker guidance, triage labels, verification, code generation, and deployment commands.

### 2. Classify documents and concerns

Assign every existing document one owner category from [DOCUMENT-LAYOUT.md](DOCUMENT-LAYOUT.md). Flag duplication, stale links, mixed concerns, and unclear authority. Preserve useful content.

Use packages and frameworks as evidence for concern-level scopes such as workspace, API, web, mobile, data, testing, operations, design, and architecture. Never propose one convention document per package. Consult version-appropriate official docs when a proposal needs current package facts, but store only confirmed project rules.

### 3. Follow posture branch

#### Greenfield

Propose smallest useful structure. Resolve real rules one concern at a time. Do not create empty context, ADR, convention, design, architecture, discovery, or runbook files. Add a document only when its first confirmed content is ready.

#### Brownfield

Inventory and route existing documents before proposing moves or merges. Preserve established content and paths unless duplicated or ambiguous authority causes harm. Show each migration separately; move only after approval and update every affected link.

### 4. Resolve setup decisions

Lead with recommended answer, explain only genuine branches, and confirm one decision at a time:

1. canonical agent instruction file or files;
2. single-context or multi-context domain layout;
3. confirmed technical scopes, including separate design and architecture conventions when needed;
4. issue tracker and triage vocabulary required by installed workflows;
5. document ownership and authority by concern;
6. task routing, including transitive package and generated-contract relationships;
7. local verification required by each scope.

### 5. Draft exact change set

Show exact proposed changes before writing:

- small routing block for canonical agent instructions;
- `docs/agents/documentation-map.md`, containing only paths that exist after the approved change set;
- `docs/agents/domain.md` when domain routing is needed;
- tracker and triage guidance only when installed workflows need them;
- convention documents only for confirmed scopes with real rules;
- approved brownfield moves, merges, and link updates.

Use [DOCUMENTATION-MAP-TEMPLATE.md](DOCUMENTATION-MAP-TEMPLATE.md) as shape, not boilerplate. Use [TRACKER-AND-DOMAIN.md](TRACKER-AND-DOMAIN.md) only when those branches apply.

### 6. Write safely

After approval:

- update existing sections in place and preserve unrelated content;
- link to one authority instead of copying rules;
- keep product behavior in context or specs, durable rationale in ADRs, and procedures in runbooks;
- keep package manuals outside the internal documentation map;
- validate every new relative link and route-table path;
- rerun safely without duplicating routing blocks or overwriting user-owned docs.

### 7. Verify

Confirm every mapped path exists, every relative link resolves, and every approved concern has one owner. Report changed files, preserved brownfield locations, unresolved conflicts, and downstream skills now configured. Recommend direct edits for routine maintenance; rerun setup only for structural changes.
