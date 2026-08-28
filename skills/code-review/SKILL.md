---
name: code-review
description: Reviews manual fixed points or immutable Review Unit Candidates on separate Standards, Spec, and Structural Quality axes. Candidate mode binds the exact workspace, provenance, and input hashes without creating Git refs.
---

# Code review

This skill has two request modes. Select the mode from the request envelope. Do not infer a mode from the size of a diff or from a moving Git reference.

The machine-readable request contract is [candidate-review.schema.json](candidate-review.schema.json). It defines the discriminated `fixed-point` and `candidate` branches, including the exact hash and provenance fields.

## Fixed-point mode

`fixed-point` is the existing manual branch and remains the default when a manual request omits `mode`. It reviews `HEAD` against a user-supplied fixed point. Keep Standards and Spec independent so correctness against requirements cannot hide a standards failure.

If the user omitted the fixed point, ask for it. Resolve and freeze the supplied fixed point, current `HEAD`, and merge base once:

```text
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Fail early on an invalid ref or empty diff. Use the frozen object IDs for the rest of the review. Do not let later branch movement, staged work, or unstaged work change the review input.

Find the governing specification in this order:

1. Issue references in commits, fetched using `docs/agents/issue-tracker.md`.
2. A user-supplied path or issue.
3. A matching spec under the project's documented locations.
4. Ask the user. If no spec exists, skip the Spec axis and report that.

If tracker guidance is missing and it blocks the review, use the documented fallback. Load `conventions-aware-engineering` for the smallest authoritative context for the changed paths.

The manual default axes are:

- Standards, using project rules and [SMELL-BASELINE.md](SMELL-BASELINE.md).
- Spec, using the requested behavior and acceptance criteria.

Add Structural Quality only when the user explicitly requests `thermo`, a strict structural review, or the `thermo-nuclear-code-quality-review` skill. Do not enable it from model judgement alone. When enabled, load the complete versioned Thermo-Nuclear rubric and keep its findings separate from Standards and Spec.

## Candidate mode

Candidate mode is the Agent Pilot v4 branch. The request must set `mode` to `candidate`, `protocolVersion` to `candidate.v1`, and provide one `axis`:

- `standards`
- `spec`
- `structural_quality`

One request reviews one axis. Agent Pilot starts three fresh requests when it needs the composite Implementation Review. All three requests carry the same `candidate`, `candidateHash`, and `workspace` bindings. They receive disjoint axis context and never see sibling reports.

The candidate packet is an immutable Review Unit Candidate. Its required bindings include:

- schema version, run, Review Unit, and candidate identity;
- repository fingerprint;
- base Git `headHash` and `treeHash` object IDs;
- aggregate Git `treeHash`, diff and patch hashes, patch path, and changed-path inventory, including `oldPath` for renames;
- member candidates in dependency order, with candidate, assignment, patch, evidence, validation, and authority hashes;
- the categorical Review Requirement Decision and its hash;
- successful interaction validation;
- `skillProvenance`, including the canonical engineering-skills revision as a Git object ID, `packageHashes` for invoked skills, and `referenceHashes` for required skill references.

Before reviewing, validate every binding against the packet and the expected read-only workspace. The repository fingerprint, expected head and tree, changed-path hash, candidate hash, authority, validation, context, and skill package hashes must match exactly. The persisted report records these exact hashes. A mismatch is a blocked review, not an invitation to repair or reinterpret the packet.

Candidate mode reads the supplied candidate and expected workspace directly. It never resolves `HEAD`, creates commits, creates branches or tags, changes refs, stages files, or includes ambient staged or unstaged changes. It does not synthesize a Git commit to represent the candidate. It reviews only the candidate's aggregate patch and dependency-closed affected scope.

The repository's minimal read-only adapter is [candidate-harness.ts](candidate-harness.ts). It accepts the controller's exact expected binding, verifies the bound patch, context, and protocol-source hashes, and returns only the supplied candidate identity and scope. It has no Git runner.

The axis context is intentionally narrow:

- Standards receives the exact Project Authority manifest, every applicable routed convention, and the smell baseline.
- Spec receives the exact bound Work Orders, specification and acceptance criteria, plus each applicable Context Brief.
- Structural Quality receives the applicable architecture context and the complete Thermo-Nuclear rubric.

`context.documents` contains the inline, hash-bound semantic documents for the selected axis. Each document has a repository-relative logical `path`, a SHA-256 `hash`, and its exact JSON `content`. `context.protocolSources` contains the absolute, hash-bound files that the Worker must read for the executable protocol (including `skills/code-review/SKILL.md` and `candidate-review.schema.json`). `context.allowedPaths` is only the repository-relative changed-path inventory for the candidate; it is not a permission to read sibling documents or to modify files. Never put an absolute protocol source or an unchanged authority path in `allowedPaths`.

No axis reads sibling reports, asks another model to combine results, or delegates to a nested Worker. Structural Quality is selected by `axis: "structural_quality"`; candidate mode has no separate `thermo` switch.

Return one semantic JSON payload for the selected axis:

```json
{
  "axis": "standards",
  "verdict": "pass",
  "findings": [],
  "observations": [],
  "evidence": ["..."],
  "summary": "..."
}
```

Use the actual selected axis. `verdict` is `pass`, `fail`, or `escalate`. Put only evidenced gating defects in `findings`; put preferences, nits, and optional improvements in `observations`. Return `fail` or `escalate` with at least one complete structured finding containing authority/invariant identity, affected scope, evidence, impact, and closure criteria. Return `pass` only when the axis has no supported gating finding. If a non-passing response cannot satisfy that contract, the controller may issue one format correction; a second invalid response is quarantined and remains non-passing. The controller attaches the frozen candidate identity, candidate hash, axis, reviewer selection, protocol hash, and skill provenance to the persisted axis report.

## Shared review rules

Load `conventions-aware-engineering` for review intent and changed paths. Include documented transitive relationships such as an API contract and its generated consumers. Record authoritative documents, applicable rules, terminology, verification, and conflicts. Review generated output for source and reproducibility, not as handwritten implementation.

For Standards, report hard documented-rule breaches with their source path and rule. Label smell judgements with the changed hunk. Project rules take precedence over [SMELL-BASELINE.md](SMELL-BASELINE.md). Do not report tooling-enforced, cosmetic, or unrelated pre-existing issues.

For Spec, identify missing or partial requirements, scope creep, and incorrect behavior. Cite the bound requirement or acceptance evidence. Do not turn an optional improvement into a gating finding.

For Structural Quality, load the complete `thermo-nuclear-code-quality-review` rubric. Use the governing architecture context and canonical project vocabulary. Do not repeat pure compliance findings that belong to Standards.

If multiple axes are requested in a manual fixed-point review, run them in fresh isolated sessions where possible. If capacity forces serial execution, preserve the same inputs and separate reports. Aggregate only at the owning control plane. A composite result passes only when every required axis passes. No axis offsets another axis, and no prose merge or second model call changes the verdict.

End every manual report with the finding count and the worst finding for each reported axis. Keep the axes visibly separate:

```text
## Standards
## Spec
## Structural Quality
```
