---
name: code-review
description: Reviews changes since a fixed point on separate Standards and Spec axes, using the repository's routed conventions and source requirements. Supports an explicit thermo mode for a third Structural Quality audit. Use for branch, PR, or work-in-progress review since a commit, branch, tag, or merge-base.
---

# Code review

Review `HEAD` against user-supplied fixed point. Keep axes independent so correctness against spec cannot hide standards failures.

## 1. Pin fixed point

If user omitted fixed point, ask. Resolve with `git rev-parse`. Capture once:

```text
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Fail early on invalid ref or empty diff.

## 2. Find spec

Search in order:

1. issue references in commits, fetched using `docs/agents/issue-tracker.md`;
2. user-supplied path or issue;
3. matching spec under documented project locations;
4. ask user. If no spec exists, skip Spec axis and report that.

If tracker guidance is missing and needed, use documentation fallback. Recommend loading `setup-conventions-aware-engineering` only when ambiguity blocks review.

## 3. Load governing context

Apply `conventions-aware-engineering` to review intent and changed paths. Include documented transitive relationships, such as API contract to generated client to web consumer. Record authoritative documents, applicable rules, terminology, verification, and conflicts.

Generated output is reviewed for source and reproducibility, not as handwritten implementation.

## 4. Select axes

Default:

- **Standards**: documented project rules plus [SMELL-BASELINE.md](SMELL-BASELINE.md).
- **Spec**: requested behavior and acceptance criteria.

Add **Structural Quality** only when user explicitly requests `thermo`, strict structural review, or manually attaches `thermo-nuclear-code-quality-review`. Do not enable it from model judgement alone.

## 5. Run independent reviewers in parallel

Provide each reviewer diff command, commits, full relevant diff, and changed-file contents needed to verify findings.

### Standards prompt

Include governing context, applicable source files, and full smell baseline. Ask for:

- hard documented-rule breaches with `source path + rule`;
- labelled smell judgements with changed hunk;
- project rule precedence over baseline;
- no tooling-enforced or cosmetic noise;
- under 400 words.

### Spec prompt

Include spec content. Ask for missing or partial requirements, scope creep, and incorrect implementation. Require quoted spec evidence. Under 400 words.

### Structural Quality prompt

Include governing context and tell reviewer to load complete `thermo-nuclear-code-quality-review` rubric. Project conventions, ADRs, and canonical vocabulary constrain remedies. Ask reviewer not to repeat pure compliance findings already owned by Standards.

If parallel reviewers are unavailable, run axes sequentially while preserving separate context and reports.

## 6. Aggregate

Report without cross-axis reranking:

```text
## Standards
## Spec
## Structural Quality   # explicit thermo mode only
```

Lightly clean wording; preserve finding substance. End with count and worst finding within each axis. Never select one winner across axes.
