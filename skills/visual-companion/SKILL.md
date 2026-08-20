---
name: visual-companion
description: Creates low-fidelity wireframes, diagrams, and structural visual comparisons for an explicitly requested visual exploration. Manual-only; use when user asks for a rough visual aid, wireframe, flow, or layout choice rather than a polished review surface.
disable-model-invocation: true
---

# Visual Companion

Low-fi route for making one visual decision concrete. Deliberately rough: clarify structure, flow, hierarchy, or interaction; do not polish visual design.

## Boundary

- User must explicitly request or accept an offered low-fi visual aid.
- Use `/skill:lavish` instead for polished, interactive, annotatable hi-fi review.
- Never start a background server or infer a visual request from a plan, report, or comparison.

## Flow

1. State one visual question and success criterion.
2. Choose smallest useful form:
   - wireframe/layout → minimal HTML
   - system flow/state/data relationship → Mermaid
   - alternatives → two to four rough side-by-side options
3. Write artifact to `.scratch/visual-companion/<slug>-v<N>.html` in project. Keep new filename per iteration.
4. Use `chrome-devtools-axi` to open local artifact when a browser is available; otherwise give user absolute path and ask for terminal feedback.
5. Iterate only on feedback. Push no visual artifact once next decision is textual.
6. Summarize selected decision in chat; link artifact in handoff only when it remains relevant.

## Low-fi constraints

- Use labels, boxes, real content, and clear hierarchy.
- No product-ready styling, animation, or design-system polish.
- Do not create a tracking issue, spec, tickets, or implementation plan.

For optional choice-card markup, consult `../superpowers/skills/brainstorming/visual-companion.md`; do not run its bundled background server.
