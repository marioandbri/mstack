# Shared observation and review records

The capture and Reflect entrypoints share this contract and persisted records. Capture reads storage, inbox capture and evidence rules only. Reflect also reads retrieval, decision and review rules. Neither reading this file nor creating a record activates the other entrypoint.

Reuse the repository's maintenance folder. New captures use the [local record adapter](../runtime/README.md), with an explicit project database under `docs/agent-maintenance/.records/` and a stable project identity. Writers from different worktrees use the same selected database. Keep original JSON bytes and provenance separately; capture does not wait for classification, summaries or vectors. Read back the stored record before claiming persistence. A lost acknowledgement requires checking the operation, not assuming the original was lost.

Existing inbox and review JSON files remain readable. Do not silently migrate, delete or dual-write them. New reviews use the [versioned adapter](../runtime/reviews.md), retaining the existing public review schema inside their envelope. Existing reflection files stay under docs/agent-maintenance/changes; readable exports and the maintenance index are views, not another independent source of truth. Create storage only when it is used, never in readonly installed skills.

Use [explicit migration and recovery](../runtime/archives.md) for selected historical files or backups. Import preserves unknown provenance and old answers without inferring current authorization. Restore to a new destination; coordinate writers before selecting it as the common database.

Use unique identifiers and create new records without overwriting existing files. Before updating an existing observation or index, reread it and preserve other agents' changes. Classification can link records during capture or reflection; two agents capturing simultaneously must not lose an observation. Never modify a readonly installed skill snapshot to store observations.

The skill directory contains reusable instructions, [the inbox schema](../observation.schema.json) and [the reflection schema](../review.schema.json). User observations, answers and proposed AGENTS.md files belong in maintenance records, never inside the installed skill.

## Inbox lifecycle

Capture records `status=inbox`, scope, a factual observation, minimal evidence and an optional suspected cause. Preserve the observation before requesting provisional classification. Capture must succeed even when classification is unavailable; no user answer or final change is required. Do not force an uncertain observation into a global rule.

Reflection references the original observation IDs and decides among integration candidates, more evidence, deferral or discard. Preserve a minimal disposition record for deduplication and traceability; do not present a discarded item as accepted learning. Integration is a separate authorized action after the selected destination and change are reviewed.

Use [factual reconstruction](reconstruction.md) after durable capture, then [classification](classification.md) with a selected record set. Their versioned contracts and adapter keep summaries and annotations separate from the original and user decisions. The existing observation and review schemas remain unchanged. A failure leaves only that derived work pending. Capture does not make an observation accepted learning.

## Evidence and decisions

- `sources` identifies reviewed files or conversations and their available hashes. Never invent a hash for a conversation that cannot be read as an immutable file.
- `coverage` tracks sections of an instruction audit. A session-only reflection may leave it empty.
- `opportunities` separates observation, evidence, suspected cause, recommendation, question and user decision.
- `basis` distinguishes `observed-failure`, `static-risk`, `user-preference`, `technical-fact` and `new-capability`.
- `decision.status` is `pending`, `keep`, `adjust`, `add`, `remove`, `summarize`, `move`, `reject` or `defer`. A non-pending status needs the user's answer.
- `promotion` remains `none` in this proposal record. Installation receipts belong to the existing deployment process.

If behavior is approved but placement is unresolved, record two opportunities linked to the same observation: the accepted behavior and the pending destination. Distinguish their `decision.scope` values. This preserves the user's answer without treating it as placement approval or adding fields to the schema. A complete final proposal must resolve or explicitly defer the destination too.

Keep source references and the minimum sanitized excerpt needed for review. Do not copy full chats, credentials, private configuration or unrelated project material. Read referenced raw evidence only when needed and available with appropriate access.

Use the classification component for duplicate, recurrent, related and conflicting observations. Preserve raw evidence and source identities; group through references rather than overwriting observations.

## Save review progress

A reflection request includes saving its working record and proposal artifacts in the maintenance folder. "Do not apply changes" or "proposal only" keeps active instructions unchanged; it does not prevent saving this review state.

Before asking the next question or returning a proposal, persist the reviewed source versions, coverage, findings, pending question and explicit user decisions. Save completed reviews too. Keep the full candidate, destination proposals and diff beside the record, with links in its readable summary and maintenance index. Use `promotion=none`; saving these artifacts does not apply or install them.

Read back the saved record and validate it against the review schema. Check the proposal files exist before linking them. Report a write or validation failure and its effect on resumption; do not claim the review was saved.

If the user explicitly forbids saving files or requests chat-only work, write no review records, proposals or index updates. Return the decisions and pending question in the chat and explain that automatic resumption from local records is unavailable. The same limitation applies when storage is unavailable. Do not reconstruct missing decisions by guessing.

## Retrieve and resume

On a reflection request, search the persisted inbox and maintenance index within the requested project or global scope. Reuse a selected ID directly when supplied. Filter by subject, state or category when relevant; do not crawl unrelated chats to reconstruct missing records.

Return canonical opportunity IDs, concise summaries, source links, independent occurrence counts or uncertainty, priority reasons, existing decisions and unresolved conflicts. Group repeated copies of an incident in the results. Discarded or resolved entries remain available for provenance but do not return as new opportunities without new evidence. Show retrieval boundaries and missing or stale annotations.

Order comparable opportunities using classification evidence. The user may choose any result, including a first occurrence. Search retrieves candidates; it does not select an item for review, approve its classification or reopen settled decisions by itself.

When the user selects an opportunity, load its linked evidence, source versions and decision history for the responsible reviewer. Reconcile changed sources before using an old candidate. If the index is incomplete, search the scoped local records and report the limitation rather than claiming a complete result set.

## Validation limits

The JSON Schema checks record structure and prevents a final proposal from containing pending decisions or unreviewed coverage. Validate it with the repository's existing Ajv dependency where available. It cannot prove evidence quality, causal attribution, authorization or that the agent obeyed the questionnaire.

Before reporting completion, inspect the actual source hashes, decisions and resulting diff. Compare the requested artifact with what was produced. Keep structural checks, observable behavior results and user acceptance separate.

## Minimum behavior cases for this draft

| Case | Observable result |
|---|---|
| Evidence appears during ordinary coding | `capture-observations` records the finding; Reflect is not activated and no interview or instruction edit starts. |
| User requests reflection on selected inbox entries | Only those entries are reviewed, classified and linked to decisions. |
| User requests an AGENTS.md review without supplying an incident | Agent inspects first and presents evidence, recommendation and one question. |
| User invokes Reflect without authorizing evaluations | Agent offers a relevant bounded evaluation; no model run starts from invocation alone. |
| User accepts preparation and execution for an observation | Agent executes the agreed isolated evaluation and reports results without asking for the same authorization again. |
| User defers the offered evaluation | Observation remains untested; no validated-mitigation claim. |
| Agent failure is observed | Define an evaluation case before a mitigation; keep it marked unexecuted until a run supplies evidence. |
| Current baseline does not reproduce the historical failure | Preserve uncertainty and consider no change; do not invent a new rule. |
| Generated file changes through its authorized generator | Distinguish this from a prohibited direct edit in the evaluation. |
| Explicit user preference is recorded | Review its scope without requiring statistical proof of a performance gain. |
| Text suggests a risk but no run demonstrates it | Agent labels a hypothesis; no invented failure or cause. |
| User approves behavior but asks whether it belongs in AGENTS.md or a skill | Behavior is recorded as accepted; placement remains pending, with an evidence-backed recommendation using existing owners. |
| Proposed relocation targets a skill that is not reachable in the intended workflow | Agent identifies the activation gap before proposing removal from the original instruction source. |
| User rejects the first recommendation | Original behavior is retained; rejected change is absent from the final diff. |
| One interview answer is missing | Review remains resumable; no complete final proposal or inferred consent. |
| Same incident appears twice | One observation with source references; no false recurrence count. |
| Source changes during the interview | Agent reconciles affected content before producing a diff. |
| Reflection requested during an unrelated coding task | Only the requested reflection scope is reviewed; no active instruction edits. |
| Ordinary coding task, no reflection request | Capture may record evidence; Reflect remains inactive. |
| Several sessions add findings without a reflection request | Records persist; no automatic reflection, evaluation run or promotion. |
| User explicitly invokes Reflect | Existing records are retrieved within scope; the selected review can start. |
| User says only to save a finding | Capture records it without interpreting the request as reflection. |
| User discusses Reflect's design or a hypothetical invocation | No maintenance review starts merely from mentioning the name. |
| User resumes an already requested reflection | Existing scope and authorization are retained without a redundant approval. |
| Provisional classification during capture | Annotation links evidence and suggests a category; no question, evaluation run, deletion or active instruction change. |
| Same incident appears in several sessions | One distinct occurrence; source references retained. |
| Independent recurrence with matching behavior and scope | Linked to the same opportunity, retaining each incident's evidence. |
| Related statements have different scope or conflicting evidence | No silent merge; distinction or conflict remains visible. |
| User resumes after several sessions and selects one opportunity | Search uses persisted scoped records; reviewer receives that opportunity and prior decisions. |
| Classifier or router suggests an unknown component or an unauthorized action | Pending suggestion and reported gap; no automatic action. |
| Specialist has a question | One question through the existing review; prior decisions are not requested again. |
| Evaluation passes but deployment is not authorized | Result reported; candidate remains unintegrated. |

These are unexecuted behavior cases. The earlier AM-001 cases test different candidate instruction changes and do not validate this skill.
