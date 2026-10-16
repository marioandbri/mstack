# T3 Code thread and worktree association

Use this reference when repository work runs in T3 Code. The behavior below was
verified in T3 Code `0.0.45`; inspect the current build's supported controls and
tools before relying on an integration.

## Associate the owned worktree

Prefer a thread started in T3's **New worktree** mode. Verify its path, branch
and task ownership, then reuse that checkout instead of creating another one.

For a thread started in **Current checkout**, use supported T3 controls or an
exposed tool to select the existing owned worktree. T3's internal metadata
operation is `thread.meta.update`, with both `branch` and `worktreePath`.
Discover the available integration; the agent's MCP tools may not expose it.
Updating only the branch name does not associate a different directory.

Retain task state before a workspace transition. Follow T3's session transition
procedure so the next turn starts from the selected worktree. Verify the thread's
registered path and branch, and the resumed session's working directory. Check
that T3's Git status and diff refer to that checkout before using them as evidence.

When creating or selecting the worktree through T3 is unavailable, retain the Git
fallback from the lifecycle guide. Run every command and edit in the owned
worktree explicitly. Record and report the association gap: T3's terminals,
diffs and checkpoints may still refer to the original checkout. Use the owned
worktree's Git diff and verification outputs for acceptance. Do not claim T3
tracks the worktree merely because those commands succeed or the PR is linked.

Do not switch the shared main checkout to the task branch to trigger a notice.
Do not edit T3's SQLite state directly to associate a thread.

## Interpret branch change notices

The **Branch changed** notice detects a different branch inside the checkout
already associated with a local thread. Sending the next message updates that
thread's branch metadata. T3 can also follow branch changes within an already
registered worktree after a turn completes.

Creating a separate directory with `git worktree add`, passing `workdir` to a
command, or editing an absolute path does not establish that association. The
original checkout can remain on `main` while the agent edits its task worktree,
so that branch change notice does not appear.
