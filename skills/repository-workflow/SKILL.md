---
name: repository-workflow
description: Coordinate authorized changes in a Git repository through an owned worktree, configured environment, commits, verification evidence, PR preparation and post-merge cleanup. Use for repository implementation and resuming its delivery. Skip read-only reviews, explanation-only requests and non-Git work.
---

# Repository workflow

Own the delivery lifecycle, not each specialist's procedure. Read
[worktree lifecycle](references/worktree-lifecycle.md) before changing a checkout,
preparing a PR or closing resources. Resume the recorded task state before acting.

## Coordinate the task

1. Load conventions-aware-engineering for governing repository context. Preserve
   the authorized scope and route. If material requirements remain unresolved,
   use grill-with-docs; do not restart discovery for an approved resource.
2. Prepare or reuse an owned worktree and task branch with the required setup.
   Load local-env only when running services or test databases are needed.
3. Execute the approved resource with implement when using spec or tickets.
   For authorized direct work, use the same scope and acceptance in task state.
   Use tdd for feature behavior and diagnose for reported bugs; reuse their
   existing procedures. Plain document edits need no application smoke.
4. Make scoped commits without coauthorship. Use applicable code-review and
   verification-before-completion procedures on the actual candidate; do not
   treat intermediate commits as evidence that the task passes acceptance.
5. Present the result and retained evidence. After Mario confirms correct
   implementation, prepare the PR toward the indicated branch or main.
   Preserve confirmation already given for this version and scope.
6. Mario manages remote merge. Record the PR and wait for resumption. Before
   post-merge closure, verify its remote merged state and retained work, then
   update local main and close owned resources and worktree as the reference
   specifies. Do not execute or schedule auto-merge.

Each supporting skill owns its triggers and content. A missing owner or failed
selection is a dependency to inspect, not a reason to add a global selector.
Keep the task state and evidence outside a worktree that will be removed. Report
implementation, verification, PR and integration states separately.
