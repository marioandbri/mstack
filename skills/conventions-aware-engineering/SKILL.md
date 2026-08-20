---
name: conventions-aware-engineering
description: Loads the smallest authoritative set of project documentation for an engineering task and resolves its scope, precedence, terminology, and verification rules. Use before architecture analysis, implementation, or code review in repositories with AGENTS.md, docs/agents/documentation-map.md, docs/conventions/, CONTEXT.md, or ADRs.
---

# Conventions-aware engineering

Prepare governing context for another engineering workflow. Do not review code, choose architecture, or rewrite documentation unless the user asks.

## Process

1. Find repository root and read every applicable `AGENTS.md` or equivalent instruction file from root to working directory.
2. Read `docs/agents/documentation-map.md` when present. Treat it as authority for document ownership and routing, but not for product or technical decisions.
3. Classify task using its intent and affected paths. Common scopes include workspace, API, web, design, domain, operations, and cross-application contracts.
4. Read smallest document set required by map. Include relevant ADRs. Read domain context only when behavior or terminology is domain-sensitive. Read runbooks only when executing their procedure.
5. Resolve authority by concern. Do not invent one global precedence order:
   - agent operation: applicable agent instructions;
   - document routing: documentation map;
   - domain vocabulary and invariants: `CONTEXT.md` or mapped context;
   - durable decisions: applicable ADRs;
   - reusable technical rules: applicable conventions;
   - procedures: runbooks;
   - unresolved evidence: discovery documents;
   - requested behavior: issue or spec.
6. Surface contradictions. Never silently choose between sources that own different concerns. An applicable ADR may override a convention. Resolved context overrides older discovery notes. A spec conflicting with either must be reported.
7. Prepare governing context using [GOVERNING-CONTEXT.md](GOVERNING-CONTEXT.md). Keep it internal unless another agent needs it or user asks to see it.

## Path-sensitive routing

Start from changed or proposed paths, then include documented transitive relationships. A contract change may govern API, generated client, workspace graph, and web consumer even when diff touches one area.

Generated files inherit rules from generator source and artifact owner. Do not treat generated output as handwritten implementation.

## Fallback

If documentation map is absent, inspect agent instructions, conventions, ADRs, context, contributing guides, and package-local docs. Continue when authority is clear. Recommend loading `setup-conventions-aware-engineering` only when missing routing creates real ambiguity. Never create placeholder context, ADR, convention, or runbook files.
