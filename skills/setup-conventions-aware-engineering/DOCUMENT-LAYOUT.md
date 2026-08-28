# Document layout

Use ownership categories to prevent one rule from appearing in several places.

| Location | Owns | Does not own |
| --- | --- | --- |
| `AGENTS.md` or equivalent | Agent operation and pointer to routing map | Detailed architecture, product rules, long procedures |
| `docs/agents/documentation-map.md` | Document ownership, routing, authority by concern | Product or technical decisions, external package index |
| `docs/agents/domain.md` | How agents find and consume domain docs | Domain definitions themselves |
| `docs/agents/issue-tracker.md` | Tracker location and commands | Product requirements |
| `docs/agents/triage-labels.md` | Canonical workflow-role mapping | Triage policy prose duplicated from skills |
| `docs/conventions/design.md` | UI/UX, design-system, token, component, interaction, and accessibility rules | Domain behavior, current architecture, decision history |
| `docs/conventions/architecture.md` | Prescriptive boundaries, dependency direction, coupling constraints, and approved architecture patterns | Current topology, package manuals, historical rationale |
| Other `docs/conventions/` files | Reusable technical rules for confirmed scopes | Product behavior, dependency inventory, long-lived rationale |
| `CONTEXT.md` or mapped contexts | Domain vocabulary, actors, invariants, ownership, sources of truth | Framework and tooling rules |
| `docs/adr/` and mapped ADR directories | Durable consequential decisions and rationale | Routine standards and checklists |
| `docs/discovery/` | Open questions, hypotheses, alternatives, and evidence | Final authority after resolution elsewhere |
| `docs/runbooks/` | Reproducible procedures, commands, expected results, and rollback | Architectural rationale |
| Issue or spec | Requested behavior and acceptance criteria | Repository-wide standards |

## Design and architecture boundary

`design.md` governs reusable product-interface rules. `architecture.md` governs prescriptive technical constraints. Neither is mandatory; create one only after its first rules are confirmed.

Architecture conventions may name allowed module shapes and boundaries. They should not cache a directory tree or narrate how system currently works when code makes that obvious. Create descriptive architecture documentation only when topology cannot be inferred reliably, then give it a distinct owner and route.

Durable decisions and rationale belong in ADRs. If a rule exists because one consequential alternative was chosen over another, ADR records choice and convention states resulting reusable constraint.

## Structural rules

- Create only categories repository needs.
- Convention scopes follow real ownership. Do not assume API, web, mobile, design, or architecture applies everywhere.
- Treat packages, frameworks, and installed skills as evidence for scope, not automatic policy.
- Keep shared rules in narrowest common convention. Keep package-local rules local when scope is truly local.
- Link official package docs only where they support a confirmed rule; do not copy manuals.
- Put newly resolved domain language in context docs.
- Use runbooks for executable procedures.
- Keep routing map short enough to read before task.

## Agent instruction block

Prefer pointer over duplicated policy:

```md
## Documentation routing

Before changing or reviewing code, read
`docs/agents/documentation-map.md` and follow its task routing,
ownership, and authority rules. Read only documents relevant to task.
```

When several instruction files serve different harnesses, select canonical source with user. Other files should point to it or repeat only small routing block.
