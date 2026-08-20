# Lavish feedback loop for Codex and subagents

Use this runbook whenever an agent says it will **listen**, **monitor**, **poll**, or **act on** feedback from a Lavish artifact. It is intentionally strict because a detached or duplicated poll can consume a feedback delivery without waking the agent that must apply it.

## Invariants

1. One artifact/session has exactly one poll owner and at most one live `lavish-axi poll` process.
2. The poll runs in the foreground of an active agent turn, or in a harness-native tracked job whose completion is guaranteed to resume/notify that same agent.
3. The owner proves the wake path is live before anyone tells the user that monitoring is active.
4. A second poll is never started while the first may still exist.
5. A button's label matches its delivery semantics: **Encolar** queues; **Enviar** queues and sends.
6. The owner remains running while the Lavish session is open. It never reports `completed` while leaving a poll behind or while the user still expects active listening.

## Start checklist

1. Open/resume the artifact with the exact pinned version:

   ```fish
   bunx lavish-axi@0.1.45 .lavish/example.html
   ```

2. Name one owner. For a subagent workflow, the owner is the delegated listener, not both the root agent and subagent.
3. Check for an existing exact poll process before starting. Inspect only; do not use a broad destructive pattern:

   ```fish
   ps -ax -o pid=,ppid=,etime=,command= | rg '[l]avish-axi.*poll.*\.lavish/example\.html'
   ```

4. Start one foreground poll:

   ```fish
   bunx lavish-axi@0.1.45 poll .lavish/example.html
   ```

5. Confirm the execution harness returned a resumable handle and that the same owner can wait on it. Only then report “estoy escuchando feedback”.

## Codex execution handles

The durable process handle is the `session_id` returned by the nested `exec_command`, not the outer `functions.exec` cell ID. An outer cell is only a temporary handle for waiting until the JavaScript wrapper returns. If the wrapper prints only `r.output`, it discards `r.session_id` and orphans the poll.

Start the poll with a short inner yield, persist the returned session ID, and expose it in the result:

```javascript
const key = "lavish-poll:example";
const r = await tools.exec_command({
  cmd: "bunx lavish-axi@0.1.45 poll .lavish/example.html",
  workdir: "/absolute/project/path",
  yield_time_ms: 1000,
});
if (r.session_id) store(key, r.session_id);
text(JSON.stringify({
  output: r.output,
  session_id: r.session_id,
  exit_code: r.exit_code,
}));
```

Then wait on the same inner process with `write_stdin`, never by starting `poll` again:

```javascript
const key = "lavish-poll:example";
const sessionId = load(key);
if (!sessionId) throw new Error("Missing tracked Lavish poll session_id");
const r = await tools.write_stdin({
  session_id: sessionId,
  chars: "",
  yield_time_ms: 30000,
});
if (r.session_id) store(key, r.session_id);
text(JSON.stringify({
  output: r.output,
  session_id: r.session_id,
  exit_code: r.exit_code,
}));
```

Handle both layers correctly:

- If `functions.exec` yields `Script running with cell ID ...`, use `functions.wait` on that same outer cell until the wrapper returns. Read the printed nested result afterward.
- While the nested result contains a `session_id`, repeat `write_stdin` with that ID. A quiet 30-second yield is normal and is not permission to start a new poll.
- When the nested result has an `exit_code`, the poll process ended. Preserve and act on its complete `output`; only then may the owner start the next poll with `--agent-reply`.
- If there is no recoverable nested `session_id` or callback but `ps` shows the poll alive, the poll is detached and invalid. Do not claim monitoring. Stop that exact PID safely, verify it is gone, then start one attached replacement.

For a delegated listener, the subagent must report these two facts to the root before the root tells the user monitoring is active:

- it owns the live nested `session_id` (and any temporary outer cell currently waiting on it);
- the exact process count for the artifact is one.

## Receive, apply, and continue

1. Keep calling `write_stdin` on the same nested `session_id` until the poll returns a feedback batch or the session ends.
2. Preserve the whole returned batch in the owning agent's turn and send the root a compact acknowledgment if delegated.
3. Apply all actionable feedback to the artifact.
4. Validate the affected interactions and layout.
5. Start the next attached wait with a visible browser reply:

   ```fish
   bunx lavish-axi@0.1.45 poll .lavish/example.html --agent-reply "Cambios aplicados: <resumen breve>."
   ```

6. Again retain one owner and one live process. Do not stack a new poll on top of a still-running one.
7. After a quiet yield, continue waiting on the same inner `session_id`; do not send a final answer or mark the listener completed.

The poll wakes for explicit feedback delivery or session end. A fatal `artifact_failures` report may arrive without user action when the review surface itself is unusable. Layout warnings do not wake the poll by themselves; the user must explicitly queue/send them. Treat returned failures and layout warnings as actionable feedback.

## Custom feedback controls

Read `bunx lavish-axi@0.1.45 playbook input` before implementing controls.

- **Queue-only:** call `queuePrompt()`. Label the action **Encolar**, **Agregar feedback**, or equivalent. Visually show that the item is queued and still needs Lavish's Send action.
- **Immediate send:** call `queuePrompt()` and then `sendQueuedPrompts()`. Label the action **Enviar** or **Enviar feedback**.
- Never label a queue-only control **Enviar**.
- Queue one precise prompt per submit and use a stable `queueKey` so repeated submissions behave intentionally.

## Failure recovery

### Poll was killed or timed out

1. Check the tracked handle first.
2. If the same process still exists, resume the same handle.
3. If it is gone, verify the exact process count is zero and start exactly one replacement.
4. Feedback still queued but not yet delivered remains available. Do not promise recovery of feedback already consumed by a detached poll whose output was discarded.

### Duplicate polls exist

1. Stop the exact duplicate PIDs; never use a broad pattern that could affect unrelated Lavish sessions.
2. Verify the exact count is zero.
3. Start one foreground, tracked replacement owned by one agent.
4. Tell the user transparently if feedback may have been consumed before an agent captured it.

### User selected Send & End

Consume and apply that final feedback once. Do not reopen or resume the session without a new user request.

### Listener wants to finish or transfer ownership

The listener may finish only when one of these conditions is true:

- the user ended the session with **Send & End**;
- the user explicitly asked to stop listening;
- a new owner has accepted the handoff, proved its inner `session_id`, and confirmed an exact live poll count of one.

Never return a final/completed status while the session is open and no verified replacement owner exists. Before handing off, stop or finish the old tracked process so ownership never overlaps.

## Diagnostic boundaries

Lavish's local state and server logs may help diagnose a failure, but they are not a supported substitute for the poll output or a wake callback. Never build the normal feedback workflow by scraping state files. The durable transport guarantee applies only while feedback is queued; delivery to a detached poll can clear the queue.

## Handoff template

Use this exact information when transferring ownership:

```text
Artifact: <absolute-or-repo-relative-path>
Poll owner: <agent/task>
Inner exec session_id: <durable process handle>
Outer wait cell ID: <temporary wrapper handle or none>
Exact live poll count: 1
Last applied feedback: <summary or none>
Session ended by user: yes/no
Owner allowed to complete: yes/no + reason
```
