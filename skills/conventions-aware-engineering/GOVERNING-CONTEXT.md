# Governing context

Use this shape when passing project guidance to another agent. Omit empty sections.

```md
## Governing context

Task:
Affected scopes:

### Authoritative documents
- `path`: why it applies

### Applicable rules
- `path:section`: concise rule

### Domain terms and invariants
- Canonical term: relevant meaning

### Required verification
- Command, test, generated artifact, or manual flow

### Conflicts or unresolved decisions
- Sources in conflict and why workflow cannot resolve them silently
```

## Rules

- Cite documents by path and section or exact rule.
- Summarize constraints. Do not paste whole documents unless consumer requires full text.
- Keep facts separate from interpretations.
- Preserve canonical project vocabulary.
- State when a document was expected but absent only if absence affects task.
- For delegation, include enough source content that child agent does not need to guess precedence.
