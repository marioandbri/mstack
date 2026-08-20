# Tracker and domain setup

## Issue tracker

Detect git remote and existing guidance. Offer only plausible choices:

- GitHub Issues;
- GitLab Issues;
- local markdown under repository-defined path;
- another tracker described by user.

`docs/agents/issue-tracker.md` records tracker, repository/project identity, pinned tool command when project requires one, and operations specialist skills need: create, read with discussion, list/filter, edit labels, comment, and close.

Do not create remote labels or issues during setup.

## Triage labels

Map these canonical roles to tracker vocabulary:

- `needs-triage`;
- `needs-info`;
- `ready-for-agent`;
- `ready-for-human`;
- `wontfix`.

Record mapping and meaning in `docs/agents/triage-labels.md`. Preserve existing labels unless user approves migration.

## Domain layout

Single context:

```text
CONTEXT.md
docs/adr/
```

Multiple contexts:

```text
CONTEXT-MAP.md
docs/adr/                 # system-wide
<owned-area>/CONTEXT.md
<owned-area>/docs/adr/    # area-specific, when needed
```

`docs/agents/domain.md` tells consumers where to read. It does not define domain terms.

Do not create empty context or ADR files. Domain-producing workflows create them when decisions exist.
