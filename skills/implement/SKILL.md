---
name: implement
description: Execute an approved spec or set of tickets within its agreed scope and acceptance, reusing recorded decisions and returning verification evidence. Use for artifact-based implementation, not discovery or artifact authoring.
disable-model-invocation: true
---

# Implement

Read the complete approved resource, decisions, exclusions, acceptance and linked
project context. Execute that work in the owned task workspace established by
repository-workflow. Do not repeat discovery or approvals already captured.
Consult a missing material expectation or proposed scope change; resolve
technical execution choices that satisfy the approved work.

Use tdd for feature behavior and diagnose for reported bugs, preserving their
requirements and previously agreed test boundaries. Do not duplicate their
procedures here. Reuse tests already exercising the required public behavior.

Run applicable typechecking and focused checks during execution, and the
project's required final checks on the actual version. Load code-review for
applicable review. Return the implemented scope, commit, acceptance evidence,
checks, outcomes and limitations to the lifecycle owner.

Make scoped commits without coauthorship under the authorized repository
workflow. PR preparation, remote merge verification and closure belong to that
owner; completing implementation alone does not authorize them.
