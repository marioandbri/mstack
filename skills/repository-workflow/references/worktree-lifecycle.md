# Worktree lifecycle

## Inspect and retain task state

Read repository instructions, contributing guidance and the approved task before
mutating Git. Identify the canonical repo, current checkout, worktrees, remotes,
branching conventions and base. The phrase Git flow does not mandate the formal
GitFlow develop/release model. Respect the repository's actual conventions.

Reuse a compatible worktree owned by this task when available. Never take over
another agent's checkout or transfer unrelated uncommitted changes. When creating
one, prefer the harness's managed-worktree tool for the correct repository; use
Git worktree tooling when that tool cannot address this repo. Give the task a
separate branch from the intended base. Main is the default PR target only when
none was specified. Verify that branch exists; do not silently substitute another
branch or invent main. Resolve an ambiguous remote or incompatible convention.

Use the existing durable task record. If none exists, keep a private task record
outside the disposable worktree, for example under a task-specific directory in
the repository's Git common directory. Do not store secrets or publish this state.
Retain task identity, canonical paths, base and target, owned branch/worktree,
authorized scope, resource or acceptance references, evidence locations, current
commit, implementation confirmation, PR identity and delivery stage. Save before
handing off or waiting for merge. Preserve another writer's state; do not infer
confirmation or ownership from a directory name.

## Configure the owned worktree

Verify runtime, dependencies, local configuration loaders, required test commands
and ignored inputs from the worktree. Use locked versions. Prefer process-level
overrides and ignored local configuration; do not overwrite another checkout's
configuration or introduce global changes without authorization.

Directory separation alone does not prove isolation of services, databases or
browser state. Follow local-env for services and owned resources, and the browser
owner for browser sessions when needed. A skills/docs task may need dependencies
but no running app. Record precise blockers instead of running a misleading test.

## Implement, commit and verify

Use the approved artifact or direct task acceptance without repeating the
interview. Ask about changes to expected behavior or scope; choose technical
execution details within the agreed boundaries. Keep unrelated repairs separate
unless already authorized.

Stage task-owned changes explicitly. Do not commit someone else's files, secrets,
local config or generated artifacts changed outside their authorized generator.
Commits are included in this workflow and have no Co-authored-by trailers. Follow
repository commit conventions. An intermediate checkpoint may be unfinished;
its message and report must not claim checks that did not run.

Preserve evidence for the exact version: acceptance covered, tests and checks
run, environment, outcomes, relevant outputs and limitations. Keep reports in
tracked task docs where appropriate or a verified durable private location, not
only an ephemeral worktree. Run the project's required checks and applicable
review on the version to be delivered. Revalidate affected checks after changes;
do not repeat a passing suite without a reason.

## Prepare the PR after confirmation

Confirm implementation through evidence before asking Mario to accept it. If
that acceptance already applies to this version and scope, retain it. Do not
create a PR merely because the implementation stage ended without confirmation.

Use the configured host's client. For GitHub, use gh-axi and its pinned procedure;
for Bitbucket, use the installed bb client's help and configured profile. Do not
assume every repo is on GitHub. Push only this task's branch as required for the
authorized PR; preserve repository protection and review rules. Bind the PR to
the target, actual change, acceptance evidence and known limitations. Attach it
to the chat when the harness supports that. Reuse an existing task PR rather than
creating a duplicate on resume.

Record awaiting-merge and return the PR to Mario. Mario merges through the
remote. Do not merge locally, invoke remote merge or enable auto-merge. A PR
being closed is not proof of merge. Do not create a background monitor unless
requested; resume this recorded workflow when the user continues it.

## Verify merge and close

On resumption, verify remote merged state, target and inclusion of this task's
work. Squash or rebase merge can change hashes; original branch ancestry alone
is not sufficient. Check for later task commits not included in the merged PR.
If work remains, retain the checkout and report it.

Fetch the relevant remote state, including main. Update local main only by a
safe fast-forward when its working tree and ownership permit it. Main might be
checked out in the primary or another worktree; inspect before updating it.
Do not switch another agent's checkout, reset divergent main, discard changes or
rewrite history to make closure succeed. Report a divergence or missing main.
For a PR to another target, still update main as Mario requested; retained merge
evidence belongs to the actual target. Do not equate an unchanged main with a
missing merge to a different branch.

Recheck consumers and ownership. Stop only this task's services and disposable
resources using local-env's close procedure. Shared services stay running.
Inspect tracked, untracked and ignored files, necessary local config, databases,
uploads, submodules and evidence. Preserve needed material in a verified private
backup before removal; archive managed worktrees recoverably when supported.
Do not force removal to hide unresolved state. Cleanup of this completed owned
worktree is authorized as part of the cycle; a request to review general storage
or other worktrees still needs a concrete deletion list and confirmation.

For storage accounting on APFS, directory sizes can count shared clone/hard-link
blocks more than once. Use filesystem free space before and after to report real
recovery. Docker's reclaimable volumes can hold data; they are not disposable
build caches. Do not delete remote branches or unrelated caches through this
worktree cleanup procedure.

Mark closed only after checking the owned worktree and resources actually closed
and retained evidence is accessible. On uncertainty, preserve them and record
what prevents completion.
