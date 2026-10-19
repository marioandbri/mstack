---
name: capture-observations
description: Record evidence-backed agent-work findings during the current task, such as a user correction, repeated failure, instruction conflict or reusable lesson. Use when such evidence arises or the user asks to save a finding. Do not open a reflection interview or change active instructions.
---

# Capture observations

Capture a finding without interrupting the task. This entrypoint has automatic selection enabled; Reflect is a separate user-requested workflow.

## Capture and return

1. Identify concrete evidence from the current work. Do not create an observation for routine progress, speculate about a failure or search unrelated sessions for material.
2. Read the storage and capture sections of the shared [record contract](../reflect/references/records.md). Save the minimal evidence and scope using the [observation schema](../reflect/observation.schema.json), outside active instructions and installed skills. Preserve a raw record before classification. If storage is unavailable, report that it was not saved rather than claiming persistence.
3. After durable capture, prepare the [factual reconstruction](../reflect/references/reconstruction.md) using the available origin context. Keep minimal sanitized excerpts, explicit gaps and source references. A summary failure leaves reconstruction pending and preserves the original.
4. Use the shared [classification procedure](../reflect/references/classification.md) with the smallest relevant record set. Link duplicates and independent recurrences, and record provisional category and priority. If classification is unavailable, retain the raw observation as pending.
5. Return to the original task. Do not ask maintenance questions, run model evaluations, modify active instructions, discard source evidence or invoke Reflect. A later user request starts reflection.

Load only the shared capture, reconstruction and classification resources, not Reflect's entrypoint, interview or reviewers. Reading a shared contract does not invoke the manual workflow. The paired resources must remain available; validate their paths when packaging the candidates.

Classification is advisory. The capture caller checks evidence, references, allowed categories and scope before saving an annotation. Unknown routes remain pending. No classification result can grant permission to review or integrate a change.

Use the existing record IDs and occurrence links to avoid repeated capture of the same event. Evidence from another independent incident may increase recurrence; another telling of the same incident does not. Preserve uncertainty and conflicting evidence.

This is agent behavior during an active task, not a background service or a guarantee that every session is observed. Recording a finding does not authorize installation, commits, publication or expanded data access.
