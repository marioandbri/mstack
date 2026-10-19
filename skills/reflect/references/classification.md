# Classify observations

Use during automatic capture and to refresh a selected opportunity during reflection. Return provisional findings to the caller, either capture or Reflect; do not conduct an interview or promote instructions. This procedure is the initial classification provider, not a requirement to use a particular model.

## Structure and compare

Read the observation and the smallest relevant set of indexed records, instructions and documentation. Preserve the raw evidence before classification. Distinguish an observed failure, textual risk, preference, fact and proposed capability. Structure the opportunity as observed behavior, expected behavior when established, scope, evidence and unresolved cause.

Check whether the behavior is already addressed in current instructions, skills or project documentation. Reference that owner and version rather than proposing a second copy. Similar wording does not establish equivalent scope or meaning. A rule already present may indicate a discovery or execution issue instead of missing instructions.

For each matching record, distinguish:

- Same incident repeated in another message or source: link to the existing occurrence. Do not increase recurrence.
- Independent incident with the same behavior and scope: link it to the opportunity and retain its own evidence.
- Related but different behavior, scope or version: cross-reference without silently merging it.
- Conflicting evidence: retain the conflict and its sources. Do not turn disagreement into consensus.

When identity is uncertain, mark a possible match. Preserve originals; grouping produces links, not destructive deduplication. If the search was incomplete, report its scope instead of claiming that no duplicates exist.

## Suggest a destination

| Category | Proposed destination |
|---|---|
| Ephemeral | Discard candidate, decided during reflection |
| Project fact | Project documentation |
| Architectural decision | ADR when appropriate |
| Reusable procedure | Existing owning skill or skill candidate |
| Global invariant | AGENTS.md candidate |
| Agent failure | Evaluation case first |
| Uncertain or mixed | Unclassified or split into linked opportunities |

Category, recurrence and priority are separate outputs. Give recurring findings priority among comparable opportunities, using distinct evidenced incidents. Keep impact, relevance to the user's objective, evidence quality and unresolved contradictions visible. A severe first incident must remain discoverable; frequency alone is not a reason to ignore it. Do not invent severity weights or present a confidence label as a calibrated probability.

## Replaceable provider contract

The local [runtime](../runtime/README.md) implements the versioned contract in [annotation.schema.json](../annotation.schema.json). The provider is this agent procedure; the adapter validates and stores its output without invoking a model.

Input includes the contract version, observation IDs and evidence, scope, relevant records and source versions, accepted decisions, allowed categories and the available component catalog. Supply only relevant, permitted data to a provider; introducing an external service needs its own configuration and data-access review.

Output includes:

- Provider identity and version, contract version and input source references.
- Structured opportunity, suggested category and rationale, confidence limits or abstention.
- Existing-content matches and their versions; duplicate, recurrent, related or conflicting record links with evidence.
- Distinct occurrence IDs supporting recurrence, priority rationale and any retrieval limits.
- Suggested next capability, missing information and evaluation need. This is advice, not an executable command or approval.

The calling workflow checks known record references, allowed categories, scope and evidence before accepting an annotation. A capture call returns to the original task; it cannot route into Reflect without a user request. Missing evidence, unknown routes or malformed output leave the raw observation pending. Reclassification creates a versioned annotation; it does not overwrite source evidence, user decisions or prior evaluation results.

To replace this procedure with another classifier, compare it on the same labeled observations and nearby negative cases. Measure classification, false merges, missed duplicates, recurrence inflation and useful prioritization separately. Keep downstream task success separate from label accuracy. Record disagreement and abstention; allow return to the prior provider. No provider is adopted merely because its response matches the contract.
