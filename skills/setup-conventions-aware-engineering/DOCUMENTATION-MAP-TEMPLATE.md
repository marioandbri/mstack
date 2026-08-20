# Documentation map

Read smallest set of documents governing task. This map owns routing and document authority, not product or technical decisions.

## Ownership and authority

| Location | Owns | Does not own |
| --- | --- | --- |
| `AGENTS.md` | Agent operating rules and routing pointer | Detailed standards |
| `docs/conventions/` | Reusable technical rules | Product behavior |
| `CONTEXT.md` | Domain vocabulary and invariants | Framework conventions |
| `docs/adr/` | Durable decisions and rationale | Routine standards |
| `docs/discovery/` | Open questions and evidence | Resolved authority |
| `docs/runbooks/` | Reproducible procedures | Architectural rationale |
| `docs/agents/` | How agents find project docs and tooling | Product or implementation policy |

Describe authority by concern rather than one total ordering. State explicit overrides, such as applicable ADR over convention or resolved context over older discovery.

## What to read

| Task | Required reading |
| --- | --- |
| Workspace or package change | Relevant workspace convention and ADRs |
| API implementation or review | API and workspace conventions, relevant ADRs, domain context when behavior-sensitive |
| Web implementation or review | Web, design, and workspace conventions, relevant ADRs, domain context when behavior-sensitive |
| Product or domain decision | Context, relevant ADRs, unresolved discovery only when needed |
| Operational procedure | Relevant runbook and conventions governing its effects |

Replace rows with repository's real scopes. Include transitive contract routes when one area generates artifacts consumed by another.

## Maintenance rules

- Put each rule in one authoritative document.
- Link instead of copying.
- Put reusable technical standards in narrowest applicable convention.
- Put durable trade-offs in ADRs.
- Put resolved domain terms and invariants in context docs.
- Put commands and expected results in runbooks.
- Flag cross-owner conflicts instead of resolving them silently.
