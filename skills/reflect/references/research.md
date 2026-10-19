# Research provenance and limits

This draft combines Mario's design decisions with research used to form testable hypotheses. It does not claim to reproduce published results or to have measured a Reflect improvement.

## Project material

Mario supplied four reports in the canonical repository under `docs/agent-maintenance/sources/`: `deep-research-report.md`, `evaluacion-de-skills-y-memoria-para-agentes.md`, `proceso-de-mantenimiento-y-evaluacion-de-agentes.md` and `redaccion-clara-y-precisa-de-skills.md`. The maintenance review at `docs/agent-maintenance/research-review.md` records their hashes and the primary-source checks performed. Preserve the originals. These paths describe this project's provenance, not dependencies required to use the skill elsewhere.

The reports contain recommendations from different stages of the discussion. Mario's later decisions control the scope. In particular, his request to prepare Reflect supersedes the older proposal's temporary restriction on creating skills, only for this candidate.

## Primary sources checked

| Source | Relevant limit and implication |
|---|---|
| [Evaluating AGENTS.md, v3](https://arxiv.org/html/2602.11988v3) | Its results do not establish a universal file-length threshold. Review behavior and relevance instead of treating line count as a success criterion. |
| [SkillsBench, v4](https://arxiv.org/html/2602.12670v4) | The self-generated and curated conditions differ. Evaluate a proposed skill in its actual workflow; do not assign it the published aggregate gain or loss. |
| [SWE Context Bench, v3](https://arxiv.org/html/2602.08316v3) | Oracle-selected summaries and freely retrieved summaries are different conditions. A compact record alone does not demonstrate useful retrieval. |
| [Agent Skills specification](https://agentskills.io/specification) | Use a directory with `SKILL.md` and load supporting resources when needed. This packaging standard is not a benchmark result. |
| [Anthropic skill authoring guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Use concrete discovery cues and match detail to the operation. Keep required behavior explicit while moving conditional detail to references. This is authoring guidance, not a measured effect of paraphrasing Reflect. |

These checks cover the design points above, not every statistic in the local reports. Record the source version, population, baseline, intervention and limitations before using a research result to recommend a change. Mark the step from experimental evidence to a local design as an inference.

## Decisions supplied by the user

- Capture brief observations with evidence automatically during current work, outside active instructions. Include failures and uncertainties without presenting a suspected cause as fact.
- Start reflection when requested. The agent discovers opportunities, explains evidence and recommendations, and asks one question at a time. The user's experience directs decisions.
- Classify before integrating: discard ephemeral material; send facts to project documentation, procedures to skill candidates, global invariants to AGENTS candidates and agent failures first to evaluation cases.
- Offer bounded evaluation preparation and execution when it helps assess an observation. Execute within the selected or previously authorized scope; reflection alone does not start a model evaluation.
- Let each skill own its activation metadata and conditions. Diagnose missed or excessive selection in the skill and its actual discovery configuration, without adding compensating selectors to AGENTS.md. This is Mario's placement decision; metadata alone does not guarantee selection.
- Present the complete AGENTS.md proposal after the agreed review. Preferences can be accepted as preferences; hypotheses of improved behavior need observed results before claiming improvement.

These are accepted design choices, not conclusions proved by a paper. Line caps, installed-skill quotas, expiry schedules, classifiers and automatic promotion have not been adopted. Capture records and structural validation do not establish that a collector is installed or that behavior improved.
