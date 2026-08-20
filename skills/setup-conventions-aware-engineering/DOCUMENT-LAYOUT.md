# Document layout

Use ownership categories to prevent one rule from appearing in several places.

| Location | Owns | Does not own |
| --- | --- | --- |
| `AGENTS.md` or equivalent | Agent operation and pointer to routing map | Detailed architecture, product rules, long procedures |
| `docs/agents/documentation-map.md` | Document ownership, routing, authority by concern | Product or technical decisions |
| `docs/agents/domain.md` | How agents find and consume domain docs | Domain definitions themselves |
| `docs/agents/issue-tracker.md` | Tracker location and commands | Product requirements |
| `docs/agents/triage-labels.md` | Canonical workflow-role mapping | Triage policy prose duplicated from skills |
| `docs/conventions/` | Reusable technical architecture, coding, testing, generated-artifact, and task-graph rules | Product behavior and long-lived rationale |
| `CONTEXT.md` or mapped contexts | Domain vocabulary, actors, invariants, ownership, sources of truth | Framework and tooling rules |
| `docs/adr/` and mapped ADR directories | Durable consequential decisions and rationale | Routine standards and checklists |
| `docs/discovery/` | Open questions, hypotheses, and evidence | Final authority after resolution elsewhere |
| `docs/runbooks/` | Reproducible procedures, commands, expected results, and rollback | Architectural rationale |
| issue or spec | Requested behavior and acceptance criteria | Repository-wide standards |

## Structural rules

- Create only categories repository needs.
- Convention scopes follow real ownership. Do not assume `api` and `web` exist everywhere.
- Keep shared rules in narrowest common convention. Link from scoped conventions.
- Put hard-to-reverse choices with genuine alternatives in ADRs.
- Put newly resolved domain language in context docs.
- Use runbooks for executable procedures.
- Keep routing map short enough to read before task.

## Agent instruction block

Prefer a pointer over duplicated policy:

```md
## Documentation routing

Before changing or reviewing code, read
`docs/agents/documentation-map.md` and follow its task routing,
ownership, and authority rules. Read only documents relevant to task.
```

When several instruction files serve different harnesses, select canonical source with user. Other files should point to it or repeat only small routing block.
