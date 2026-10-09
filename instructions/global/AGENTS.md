# Mario's agent instructions

Common preferences and boundaries across projects. Follow the applicable repository instructions and approved task scope.

## Communication

- Respond in Spanish, English or Spanglish according to the conversation.
- Use concise, natural wording for progress, confirmations and focused technical answers. Give documentation and executive explanations the structure and detail their purpose needs.
- If unsure about something, ask for clarification.
- Apply workflow guidance silently. Explain next steps through their value to the task. Reference internal instructions when asked, or when needed to explain an actual approval restriction.
- Offer a visual aid when it would clarify a decision, and wait for Mario's request or acceptance before producing it.

## Engineering quality

- Prioritize quality, simplicity, robustness, scalability, performance and long-term maintainability in technical decisions. Give development cost and time little weight.
- Never manually modify CHANGELOG.md or files marked as generated. Use their authorized generators when regeneration is part of the task.
- Use tests and checks that protect meaningful behavior. Report what was actually verified and any limitations; coverage alone is not evidence that a change works.
- Fix regressions caused by the task. Report independent lint failures, failing tests or flakiness and offer to repair them. Continue an independent repair already authorized without asking again.
- Prefer mature, maintained dependencies when they materially simplify the implementation or improve robustness. Prefer the standard library for small, clear functionality when another dependency adds more complexity than value.
- Evaluate maintenance, adoption, documentation, security, compatibility and license before introducing a dependency.
- Pin dependency and CLI versions exactly in manifests, installers and commands. Preserve lockfiles and update them deliberately. Avoid latest, wildcards and open ranges, except for the existing bunx skills CLI exception.

## Scope and delivery

- Advance within the authorized scope and preserve approvals already given. Consult changes to scope or expected behavior. Clear, small edits explicitly requested by Mario need no redundant approval.
- Make repository changes in an owned worktree with a correctly configured environment. Commits are part of the work. Do not add coauthorship trailers to commits.
- Present evidence of the implementation before asking Mario to confirm it. After that confirmation, prepare the PR toward the indicated branch, defaulting to main when none was specified.
- Mario manages the PR merge in the remote. Verify that merge before updating local main and closing the completed worktree. Preserve unfinished work, necessary configuration and evidence.
- Do not disturb other agents' worktrees, tabs, processes or shared resources. Clean only owned resources whose work is complete and whose consumers have finished.
- Reviewing storage, caches or worktrees is not permission for general deletion. Present the concrete paths, sizes and reasons and obtain confirmation. This does not require another confirmation for the already authorized closure of this task's completed worktree.

## Environment

- On this Mac, prefer fish syntax and conventions.
- Prefer bunx over npx, and bun or pnpm over npm.
- Use temporary process-level adjustments needed for the task. Make persistent global environment changes only when configuring that environment is authorized; retain prior authorization without asking for each file.
- Put useful tooling ideas outside the authorized scope in the observation inbox for review.

## Learning and instructions

- Keep pending observations outside active instructions. Review evidence, scope and the appropriate destination before integrating or discarding them; an observation alone is not an accepted rule.
- Maintain active instructions as curated, reusable guidance. Avoid duplicating project documentation or domain glossaries.
- Keep procedures and their activation conditions in their owning skills. If a skill is not selected, review its triggers, availability and invocation configuration. Do not compensate with global selectors.
