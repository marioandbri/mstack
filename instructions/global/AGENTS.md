# Mario's Agents Instructions

These are common instructions for all agents across all projects and scenarios.

## General Guidelines

- Only respond in spanish, english or spanglish (spanish with english words), depending on the chat context.
- If unsure about something, ask for clarification.
- Persist relevant knowledge in a project memory file (if project-specific) or global memory file. Convention: use `AGENTS.md` under `## Knowledge Gathered`. Treat that section as a curated knowledge base, not a chronological log: group by topic, keep only reusable rules/decisions/lessons, remove dates and ephemeral details, merge duplicates, rewrite freely to avoid contradictions, and avoid duplicating domain glossaries such as `CONTEXT.md`.
- When writing commit messages NEVER auto-add your agent name as the co-author.
- Never manually modify CHANGELOG.md files or any other file marked as auto-generated.
- When making technical decisions or recomendations, do not give much weight to development cost or time. Instead, focus on quality, simplicity, robustness, scalability, performance, and long-term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E testing setting as closely aligned with how an end user would experience it. This makes sure you find the real problem so your fix will actually solve it.
- Apply the same high standards to engineering excellence: lint, tests failures, and test flakiness. If you see any of these, even if its not caused by whatever you are working on, you should fix it.

## Agent Workflow

- For a non-trivial implementation request with unresolved domain terms, scope, boundaries, or acceptance criteria: begin with `grill-with-docs`. Inspect code and project docs first; ask one question at a time.
- Once a **Shared Understanding** exists, offer a spec or tickets. If the task is small and bounded, with clear acceptance checks, no unresolved material decisions, and no need for coordinated work, also offer inline implementation without a separate spec or tickets. Inline implementation is a valid next step even when `grill-with-docs` asks for exactly one next artifact. Wait for user choice and approval; do not generate a detailed implementation plan, publish artifacts, or start implementation automatically. For clear small edits explicitly requested by the user, the request itself authorizes implementation; do not add a redundant approval step.
- Apply workflow instructions silently. Present next steps in terms of the task and their practical value, not as requirements imposed by `AGENTS.md`, `SKILL.md`, or internal rules. Do not quote or reference those instructions to justify a question or approval step unless the user explicitly asks about them.

## Visual Accompaniment

- If a concept, proposal, or decision would be clearer visually, offer it and wait for user agreement.
- After agreement, choose `/skill:visual-companion` for low-fi structure/flow exploration or `/skill:lavish` for hi-fi interactive review.

## Environment Considerations

- You are running on a Mac with a fish shell. Prefer fish syntax over bash syntax, and fish conventions over bash conventions.
- Prefer to use bunx oven npx.
- Prefer bun or pnpm as package manager over npm.
- Prefer to take advantage of fish functions and aliases to persist relevant tools for agent workflow, dont be afraid to create new ones if needed. persist them in the AGENTS.md file in this ## Environment Considerations section (could be project specific, or global).
- You have available the following cli tools:
  - jq: json processor for manipulating json data.
  - ctx7: registry for searching libraries and tool context. you can execute ctx7 --help to get more information.
  - gh-axi: github cli for interacting with github. Execute `bunx -y gh-axi@0.1.30` to get GitHub tools. Prefer this tool over GitHub CLI, GitHub MCP, or other GitHub tools.
  - bb: Bitbucket CLI (`gildas/tap/bitbucket-cli`); use `bb profile` for authentication and `bb --help` for commands.
  - lavish: execute `bunx lavish-axi@0.1.45` after user explicitly requests or accepts an offered hi-fi visual review. Update this exact pin deliberately after reviewing the new CLI help and playbooks.
  - chrome-devtools-axi: use globally installed `chrome-devtools-axi@0.1.35` with pinned `chrome-devtools-mcp@1.9.0`, never unpinned bunx/npx. Follow "Chrome DevTools AXI usage" below for headless operation and agent isolation.

## Knowledge Gathered

- Keep this section as a curated knowledge base, not a log. Group entries by topic; preserve reusable rules, decisions, and lessons; remove dates and ephemeral details; merge duplicates; rewrite to avoid contradictions; do not duplicate project glossary files such as `CONTEXT.md`.
- This section in this file (~/.agents/AGENTS.md) is for GLOBAL knowledge only. For project related knowledge, create or update AGENTS.md near project root.

### Chrome DevTools AXI usage

- Use headless Chrome for automation. Default shared endpoint: `CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222`, with one CDP listener. Verify Chrome was launched with `--headless=new` before interacting. If visible, ask before coordinating a restart; never steal focus or restart another agent's browser.
- Pass a unique, stable `CHROME_DEVTOOLS_AXI_SESSION=<project>-<agent-id>` on every invocation, including `stop`; never share `default` between agents. Let AXI derive bridge ports; do not export one global `CHROME_DEVTOOLS_AXI_PORT`.
- Create your own tab with `newpage <url> --background`; retain its page ID and reselect only your own tabs. Never navigate, close, or reuse another agent's tab. Serialize commands within your session; parallelize across distinct sessions.
- Named sessions isolate routing and refs, not cookies/storage in shared Chrome. For independent auth/storage, use separate headless Chrome instances with distinct profiles/endpoints, or explicitly isolated browser contexts. Never launch two Chrome instances against the same profile.
- `BROWSER_URL`/`AUTO_CONNECT` attach without changing visibility; `HEADED=0` cannot make an existing browser headless. `axi-chrome` reuses an existing listener unchanged; reserve visible `axi-chrome-login` for user-approved manual login.
- Set `CHROME_DEVTOOLS_AXI_MCP_PATH` to the installed pinned MCP executable. Existing bridges retain their original executable/transport; coordinate changes and stop only your own session. Never kill shared Chrome or other agents' bridges.

### Personal engineering skills

- `~/personal/engineering-skills` is canonical source for 24 managed workflow skills. Installed entries under `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`, and `~/.pi/agent/skills` are symlinks.
- Edit canonical repository, run `bun run check`, `bun test`, and `fish install/verify.fish`, then commit. Do not update managed names through upstream skill installers.
- Imported skills retain provenance and license notices in `skills.json`, `UPSTREAM.md`, and `licenses/`.

### Pi MCP configuration

- Built-in MCP reads `~/.pi/agent/mcp.json`. Linear uses `{ "url": "https://mcp.linear.app/mcp" }`; OAuth is automatic. Legacy `"auth": "oauth"` is invalid. The `auth` field instead selects a Pi provider credential, not MCP OAuth.
- Validate with `pi mcp list`. If Linear reports `needs sign-in`, run `pi mcp login linear`, then `/reload` in existing sessions. Built-in OAuth credentials are separate from legacy adapter storage under `mcp-oauth/`.

### CLI paths and Portless

- Noninteractive zsh sessions may omit `~/.bun/bin` even when fish resolves its globally installed CLIs. Before declaring a tool missing, check fish and that directory. Portless requires Node 24+; use an already installed compatible Node through a process-local PATH override and verify `portless doctor`, without changing the user's global Node selection.

### Conventions-aware engineering

- Use `/skill:setup-conventions-aware-engineering` for manual repository documentation setup. It configures agent routing, `docs/agents/documentation-map.md`, domain/tracker guidance, and confirmed convention scopes without creating empty placeholders.
- Use `conventions-aware-engineering` as read-only task preflight. It loads the smallest governing document set and passes context to architecture, implementation, and review workflows.
- `code-review` owns Standards and Spec review axes. Thermo mode adds an explicit Structural Quality axis. `improve-codebase-architecture` remains a pre-change exploratory workflow.

### Bitbucket Cloud API

- For the authenticated user's effective repository permissions, use `GET /2.0/user/workspaces/{workspace}/permissions/repositories`. The legacy `/2.0/user/permissions/repositories` is deprecated and can return 404 even when PR reads succeed. Do not confuse the user-scoped replacement with the workspace-admin permissions endpoint. Reference: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-user-workspaces-workspace-permissions-repositories-get

### Dependency Selection

- Prefer mature, battle-tested, well-maintained libraries and tools when they materially simplify the implementation or improve robustness; do not reimplement solved infrastructure without a clear advantage.
- Evaluate maintenance activity, adoption, documentation, security posture, compatibility, and license before introducing a dependency. Prefer the standard library for small, clear functionality when an external package would add more complexity or supply-chain surface than value.
- Pin dependency and CLI-tool versions exactly in manifests, installers, and executable commands. Never use `latest`, `*`, open-ended ranges, or other specifications that can update automatically, except for bunx skills cli tool. Preserve and update lockfiles deliberately.

### Lavish Feedback Sessions

- Before claiming that an agent is listening to a Lavish artifact, follow `~/.agents/skills/lavish/references/codex-feedback-loop.md`.
- Assign exactly one poll owner per artifact/session and keep exactly one foreground poll attached to that owner's active turn or a verified completion-aware tracked job. Never use `nohup`, `&`, `disown`, redirected fire-and-forget execution, an untracked terminal, or duplicate fallback polls.
- Verify the nested `exec_command` `session_id` and an exact live process count of one before telling the user monitoring is active. Persist and resume that inner session with `write_stdin`; an outer `functions.exec` cell ID is only a temporary wrapper wait handle. A timeout means resume the same inner session, not start another poll.
- A Lavish listener must remain running while the session is open. It may mark itself completed only after **Send & End**, an explicit user stop, or a verified non-overlapping handoff to a new owner with its own live inner `session_id`.
- Custom controls labelled **Enviar/Send** must call `queuePrompt()` followed by `sendQueuedPrompts()`. Queue-only controls must be labelled **Encolar/Queue** and show that a separate Send action is still required.
