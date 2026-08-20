---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

## Workflow routing

Honor global workflow policy in `suggested skills`:

- unresolved non-trivial work → `grill-with-docs`
- shared understanding, one cohesive flow → `to-spec`
- shared understanding, multiple vertical slices → `to-tickets`
- approved spec or ticket set, explicit implementation request → `implement`
- multi-session decision fog → `wayfinder`

If visual accompaniment remains useful for an unresolved concept or proposal, say it can be offered in next session; wait for user agreement before choosing low-fi or hi-fi route.
