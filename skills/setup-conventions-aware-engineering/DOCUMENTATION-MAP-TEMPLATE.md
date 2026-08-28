# Documentation map

Read smallest set of documents governing task. This map owns routing and document authority, not product or technical decisions.

List only paths that exist. Add a route when its target gains first authoritative content; remove or update route in same change that moves its target.

## Ownership and authority

| Location | Owns | Does not own |
| --- | --- | --- |
| `AGENTS.md` | Agent operating rules and routing pointer | Detailed standards |
| `docs/conventions/design.md` | UI/UX and design-system rules | Domain behavior or architecture rationale |
| `docs/conventions/architecture.md` | Prescriptive architecture constraints | Current topology or decision history |
| Other `docs/conventions/` files | Reusable technical rules for confirmed scopes | Product behavior or package manuals |
| `CONTEXT.md` | Domain vocabulary and invariants | Framework conventions |
| `docs/adr/` | Durable decisions and rationale | Routine standards |
| `docs/discovery/` | Open questions and evidence | Resolved authority |
| `docs/runbooks/` | Reproducible procedures | Architectural rationale |
| `docs/agents/` | How agents find project docs and tooling | Product or implementation policy |

Replace example locations with repository paths that exist after approved setup.

Describe authority by concern rather than one total ordering. State explicit overrides, such as applicable ADR over convention or resolved context over older discovery.

## What to read

| Task | Required reading |
| --- | --- |
| Workspace or package change | Relevant workspace or package convention and ADRs |
| API implementation or review | API and workspace conventions, relevant ADRs, domain context when behavior-sensitive |
| Design-system or UI change | Design, web or mobile, and accessibility conventions; relevant ADRs and domain context |
| Architecture-sensitive change | Architecture and affected-scope conventions, relevant ADRs, domain context when boundaries use domain concepts |
| Product or domain decision | Context, relevant ADRs, unresolved discovery only when needed |
| Operational procedure | Relevant runbook and conventions governing its effects |

Replace rows with repository's real scopes. Include transitive contract routes when one area generates artifacts consumed by another. A detected package suggests a route only after project rules for its concern exist.

## External sources

Manifests and lockfiles own package versions. Convention documents may link official version-appropriate sources supporting accepted rules. This map does not list package manuals.

## Maintenance rules

- Put each rule in one authoritative document.
- Link instead of copying.
- Put reusable technical standards in narrowest applicable convention.
- Put durable trade-offs in ADRs.
- Put resolved domain terms and invariants in context docs.
- Put commands and expected results in runbooks.
- Flag cross-owner conflicts instead of resolving them silently.
- Keep every route valid in same change that creates, moves, or deletes target.
