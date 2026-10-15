# Evaluate agent failures before choosing a mitigation

This workflow concerns changes to agent instructions. Continue fixing a user-requested product bug or a regression caused by the current task.

## Define the case

Preserve the observed action, expected behavior and evidence. A user correction can establish the expectation. Separate failures from textual risks and suspected causes; capture does not require recurrence.

Record the initial state, prompt, applicable instructions, tools and acceptance checks. Judge actions and artifacts rather than preferred wording. Add a nearby case where the restriction should not apply.

For the user's generated-CHANGELOG example, check for direct manual edits and distinguish changes produced by an authorized generator. Record generation metadata and task authorization. This is a supplied example, not a reported incident in Mario's environment.

## Evaluate selection cases

Use the findings from [skill support](skill-support.md) to test natural requests that should select the skill and nearby requests that should not. Judge selection and execution separately in the actual catalog and intended environment. Retain traces; an explicit invocation alone does not validate automatic selection.

## Offer and run the comparison

Offer preparation and execution when results would help the decision. State the case, expected behavior, baseline or candidate comparison, isolated environment and budget. The user can accept, limit or defer the offer. Resolve missing environment or budget details before running.

Execute within the selected or previously authorized scope. Capture or invocation alone does not authorize model runs. Acceptance of preparation and execution does not require another approval at the execution step.

Record model, reasoning, harness version, instructions, skills, fixture and budget. Bind results to the exact candidate and sources tested. Verify the context loaded and hold relevant conditions constant across comparisons.

Use a runner that can measure the case and preserve its traces. The mstack DeepSWE adapter measures coding tasks; a runner for Reflect and skill-selection cases still needs implementation. The [owned workspace collector](../runtime/collection.md) now covers the historical unreadable-export symptom with a deterministic regression. It records collection, execution and recovery separately and makes no model calls. Reuse it in the runner; it does not itself prove loaded context or behavior. If no compatible runner is available, return the prepared case and execution gap rather than substituting unrelated benchmark scores. Passing structural checks is a separate result.

## Interpret the baseline

Distinguish these outcomes:

- Case prepared, not executed: the observation remains untested.
- Failure reproduced: use the evidence to select relevant mitigations.
- Failure not reproduced: retain the historical evidence and uncertainty; consider no change, further diagnosis or a targeted repeat.
- Inconclusive: record the limitation, such as a timeout, unavailable tool or missing trace.

A single successful replay does not establish reliability or disprove the historical observation. An infrastructure failure does not establish an instruction's causal role. If evaluation is deferred or declined, do not claim a validated mitigation.

## Compare relevant interventions

Consider clarification, removal of a conflicting rule, a skill change, a mechanical check or no change. Select alternatives that address the evidence; do not run every possible intervention by default.

Test the targeted behavior and relevant negative or regression cases. Report outcomes, user interventions and actions outside scope. Treat tokens and calls as secondary measures.

Recommend the smallest supported change that preserves the user's intended behavior. Failed or inconclusive experiments remain evidence. Integrate only within the user's authorization and the existing deployment process.

## Handle other evidence

Explicit preferences and confirmed facts do not require statistical performance gains. Review their destination and scope. Project facts belong in documentation; architectural decisions may warrant an ADR. Check an existing owning skill before proposing a new procedure. Global invariants remain candidates until reviewed.

During requested reflection, discard ephemeral material while keeping the disposition needed to avoid repeated review.
