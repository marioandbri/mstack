---
name: lavish
description: Turn complex or visual agent responses into rich, reviewable HTML artifacts the user can annotate and send feedback on, using the lavish-axi CLI. Use when about to give a plan, comparison, diagram, table, code diff, report, or anything easier to grasp visually than as prose.
disable-model-invocation: true
metadata:
  hermes:
    tags: [html, review, artifacts, visualization]
    category: productivity
---

# Lavish Editor

> **Hi-fi route.** Use after user explicitly requests or accepts an offered hi-fi visual review. Use `/skill:visual-companion` for low-fi wireframes, diagrams, and structural choices.

Lavish Editor helps agents turn rich HTML artifacts into collaborative human review surfaces. Whenever you are about to give user a complex response that will be easier to understand via a rich / interactive page, consider using Lavish Editor. First generate an interactive HTML artifact according to user request, then run `bunx lavish-axi@0.1.45 <html-file>` so the user can visually review it, annotate elements or selected text, queue prompts, and send feedback back through `bunx lavish-axi@0.1.45 poll`.

You do not need lavish-axi installed globally. Use the exact version pinned here; update the pin deliberately only after reviewing the new version's `--help` and playbooks. If lavish-axi output shows a follow-up command starting with `lavish-axi`, run it as `bunx lavish-axi@0.1.45 ...` instead.

## Request

$ARGUMENTS

If the request above is non-empty, the user invoked `/lavish` explicitly - build an HTML artifact for that request now, following the workflow below.
If it is empty, infer what to visualize from the conversation.

## When to use

Use lavish-axi when the user asks for a visual artifact, HTML explainer, interactive prototype, review surface, product or technical plan, comparison, report, or browser-based feedback loop

## Workflow

1. Create the HTML artifact (default location `.lavish/<name>.html` in the working directory).
2. Run `bunx lavish-axi@0.1.45 <html-file>` to open or resume a review session in the browser.
3. When feedback listening is requested, read [references/codex-feedback-loop.md](references/codex-feedback-loop.md) and assign exactly one poll owner for the artifact/session.
4. The owner runs `bunx lavish-axi@0.1.45 poll <html-file>` in the foreground, attached to an active agent turn or to a harness-native tracked job that is guaranteed to wake that same agent. Do not detach it with `&`, `nohup`, `disown`, redirected fire-and-forget execution, or an untracked terminal.
5. Verify the wake/resume handle is live before telling the user that the artifact is being monitored. Never start a second poll as a fallback while the first one may still be alive.
6. A poll wakes when the user sends feedback or ends the session. A fatal `artifact_failures` report may also arrive without user action. Browser layout warnings are delivered only after the user explicitly queues them; they do not independently wake the poll. Fix any returned failure, overflow, clipping, or overlap before requesting further review.
7. Apply human feedback, then poll again with `--agent-reply "<message>"` to reply in the browser and keep the loop going. The poll owner must remain running; it must not return a final/completed status merely because a wait yielded silently.
8. Run `bunx lavish-axi@0.1.45 end <html-file>` only when the review is finished. The owner may complete only after **Send & End**, an explicit user stop, or a verified handoff to a new live owner. If the user chose **Send & End**, consume that final delivery and do not reopen the session unless invited.

## Feedback controls

- A control labelled **Encolar**, **Queue**, or equivalent may call `queuePrompt()` only. Its UI must visibly distinguish selected state from queued state, and the user completes delivery with Lavish's Send action.
- A control labelled **Enviar**, **Send**, or equivalent must call `queuePrompt()` and then `sendQueuedPrompts()` so its behavior matches its label.
- Run `bunx lavish-axi@0.1.45 playbook input` before building any custom feedback controls. Use stable `queueKey` values and queue one precise prompt per submit.

## Visual guidance

- Use visual hierarchy to make the most important decisions, risks, tradeoffs, and next actions obvious at a glance
- Use visual structure such as sections, cards, tables, diagrams, annotated snippets, and side-by-side comparisons instead of long prose
- Choose typography, spacing, color, and layout deliberately so the artifact has a clear point of view
- Prevent horizontal overflow at every nesting level: nested grid/flex children also need minmax(0, 1fr) tracks and min-width: 0, especially when badges, labels, or status text use wide pixel or monospace fonts; wrap, truncate, or contain long unbreakable text deliberately

## Playbooks

Run `bunx lavish-axi@0.1.45 playbook <id>` for focused, detailed guidance on any of these.
One artifact often combines several playbooks (for example a plan that includes a comparison and a diagram), so MUST open each matching playbook before writing HTML.
For flows, architecture, state, or sequence diagrams, do not hand-build boxes-and-arrows from div/flexbox; open the diagram playbook and use Mermaid unless SVG is needed for richly annotated nodes.

- `diagram` - Map relationships, flows, state, and architecture
- `table` - Turn dense records into scan-friendly review surfaces
- `comparison` - Show options, tradeoffs, and current vs target behavior
- `plan` - Explain a product or technical plan before implementation
- `code` - Render source code, code files, patches, PR diffs, and before/after code inside Lavish artifacts
- `input` - Must be used when the agent needs to collect user input on decisions, choices, preferences, triage, scope, or other structured feedback from within the artifact
- `slides` - Create a deliberate presentation when slides are requested

## Commands & rules

- Run `bunx lavish-axi@0.1.45 <html-file>` to open or resume a Lavish Editor session
- Unless the user specifies another location, create HTML artifacts in the current working directory under `.lavish/`
- Lavish serves the html file through a local express.js server. If your html needs to reference other filesystem assets such as images, CSS, fonts, and local scripts, copy them into the same directory as the HTML file, then reference them with relative paths from that directory. Never prepend `/` to those asset paths - root paths won't work
- Run `bunx lavish-axi@0.1.45 poll <html-file>` only through the attached single-owner feedback loop above. If the attached process is killed, confirm that exact process is gone before starting one replacement; feedback still queued but not yet delivered remains available
- Run `bunx lavish-axi@0.1.45 end <html-file>` to end a session
- Run `bunx lavish-axi@0.1.45 stop` to shut down the background server (it also self-stops when idle or after the last session ends with nothing connected)
- Run `bunx lavish-axi@0.1.45 playbook <playbook_id>` for focused artifact guidance. One artifact often combines several playbooks (for example a plan that includes a comparison and a diagram), so MUST open each matching playbook before writing HTML.
- Lavish does not auto-inject any design system - artifacts stay portable so they render identically when opened directly without lavish-axi running. Before writing any HTML, decide the design direction in this strict priority order, and only move to the next step when the current one truly yields nothing: (1) if the user asked for a specific look or named design system, use that; (2) otherwise you must first inspect the project the artifact is about - the subject or product whose content or UI it represents, which may differ from your current working directory - and match that project's design system: Tailwind or theme config, shared CSS variables or design tokens, component library, brand assets, or existing styled pages. If the artifact previews, proposes, or mocks a specific app's UI, render it in that app's own design system so it faithfully shows the product, even when you are running in a different repo; (3) only when both steps come up empty, use the Lavish-recommended Tailwind CSS browser runtime v4 + DaisyUI v5, available via CDN - run `bunx lavish-axi@0.1.45 design` for a content-to-playbook router, a copy-pasteable CDN snippet, a Mermaid CDN snippet/init for diagrams, and the DaisyUI component reference, and prefer the Tailwind/DaisyUI CDN snippet over hand-writing styles unless explicitly instructed otherwise by the user. When you deliver the artifact, state which of the three design sources you used and why.
- Use lavish-axi when the user asks for a visual artifact, HTML explainer, interactive prototype, review surface, product or technical plan, comparison, report, or browser-based feedback loop
