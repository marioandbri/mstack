# Session setup and isolation

Read before connecting or interacting. These requirements also apply on resumption; a saved session name does not prove that its endpoint or process is unchanged.

## Pinned executables

Locate the installed `chrome-devtools-axi` and `chrome-devtools-mcp`. Fish may resolve them in `~/.bun/bin` when a noninteractive shell does not. Use a process-local PATH if needed; do not change global shell configuration for this task.

Choose a unique stable `CHROME_DEVTOOLS_AXI_SESSION=<project>-<agent-id>` before invoking AXI. Verify AXI version **0.1.35** and MCP version **1.9.0** with their version commands. Resolve the MCP launcher to the installed package's actual executable and set `CHROME_DEVTOOLS_AXI_MCP_PATH` to that absolute path. Never fall back to an unpinned npx/bunx command or run an advertised update.

Existing bridges retain their executable and transport. Verify them before reuse. If they disagree with the pinned configuration, coordinate correction and stop only this task's bridge. Missing executables or a version mismatch are setup blockers, not permission to install a different version.

## Headless browser and endpoint

Default shared endpoint: `CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222`. There must be one CDP listener for that endpoint. Verify its listener and actual Chrome process were launched with `--headless=new` before interaction. Do not dump full process environments or credentials while checking identity.

A reachable endpoint does not establish headless operation. `BROWSER_URL` and `AUTO_CONNECT` attach without changing visibility; `HEADED=0` cannot make an existing visible browser headless. If the browser is visible, ask before coordinating a restart. Never steal focus or restart another agent's browser. If the endpoint is absent, establish an authorized headless instance with an unused endpoint and profile or report the missing setup.

The local `axi-chrome` helper reuses a listener unchanged. `axi-chrome-login` is reserved for user-approved visible manual login; do not assume either helper is installed.

## Session, tabs and state

Pass the same unique session name, verified endpoint and MCP path on every AXI invocation, including `stop`. Never share `default` between agents. Let AXI derive bridge ports from the session; do not export one global `CHROME_DEVTOOLS_AXI_PORT`.

For example, after independently verifying these values, use process-scoped environment assignments in fish:

```fish
env CHROME_DEVTOOLS_AXI_SESSION=$chrome_task_session \
    CHROME_DEVTOOLS_AXI_BROWSER_URL=$chrome_task_endpoint \
    CHROME_DEVTOOLS_AXI_MCP_PATH=$chrome_task_mcp \
    chrome-devtools-axi newpage $chrome_task_url --background
```

Retain session identity, endpoint, owned page IDs and process ownership in task state without secrets. A session name isolates command routing and refs, not all browser state. Never navigate, close or reuse another agent's tab. Serialize commands within a session; distinct owned sessions can run independently.

## Authentication and storage

Named sessions on shared Chrome share cookies and storage. For independent authentication or storage, use separate headless Chrome instances with distinct profiles and endpoints, or an explicitly isolated browser context supported by the verified tooling. Never launch two Chrome instances against one profile. Do not claim that a named session or a separate worktree alone provides browser storage isolation.

Use the shared endpoint only when its shared browser state is appropriate for the task. If the required isolation cannot be established, stop before interacting with that state and report the limitation.

## Close owned resources

Recheck ownership before closing tabs or stopping a session. A saved name or apparently idle process is insufficient to claim another task's resources. Stop only this task's bridge, with the same session environment. Leave shared Chrome and other agents' bridges running. A private browser may be closed only when this task owns it and no other work depends on it.
