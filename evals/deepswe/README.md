# DeepSWE pilot with a private ChatGPT login

Run Codex CLI against the same frozen TypeScript task in two conditions:

- A installs the current global `AGENTS.md`.
- B installs the same file and a snapshot of the repository-managed skills.

Pier owns task execution and grading. This adapter prepares profiles, verifies injected instructions, preserves renewed OAuth credentials and compares results. Built-in and repository-provided instructions or skills are present in both conditions.

## Requirements

Use Docker with Compose, git, uv and Codex CLI. Dependencies are locked in `uv.lock`; Pier is pinned to `0.3.1`. The Python environment uses `3.13.2`. Codex uses the exact locally detected CLI release unless `--codex-version` is supplied. The sandbox Node runtime is pinned to `24.12.0`. The initial model is `gpt-6.1-sol`, with `high` reasoning.

On Apple Silicon, the pilot runs the task's `linux/amd64` image through Docker emulation. Check Docker memory and free disk space. The initial task declares 8 GiB RAM. A smaller Docker allocation can cause infrastructure failures even though macOS has more memory. Resource changes require a new experiment state.

## Login

```fish
cd evals/deepswe
uv sync --locked
uv run --locked bench.py login
```

Complete the device-code flow in your browser. Enable device-code login in your ChatGPT security settings if needed. This login uses `~/.local/share/mstack-evals/codex`, with private file storage. It does not copy your everyday `~/.codex/auth.json`.

Keep this directory private and use it only for the benchmark. The runner locks it for the duration of a job and recovers refreshed credentials before Pier removes the sandbox copy. OAuth files never belong in Git or evaluation results. See [Codex authentication](https://learn.chatgpt.com/docs/auth).

## Prepare

First clone DeepSWE and pull the selected task's prebuilt image. This pilot selects one TypeScript task deterministically with seed `42` from dataset commit `0b9fabbb63b9104d678fe965e1632f2dd9eaa2ea`: `dynamodb-toolbox-lazy-recursive-schemas`. The local prepared state contains the dataset copy.

```fish
uv run --locked bench.py --state-dir state-chatgpt prepare \
  --agents ~/.agents/AGENTS.md \
  --skills ../../skills \
  --dataset /path/to/deep-swe \
  --model gpt-6.1-sol \
  --reasoning high \
  --tasks 1 \
  --timeout 10800
```

Preparation needs no model calls and can finish before login. It resolves skill symlinks into copies, records the dataset commit and hashes, and replaces image tags with their downloaded content digests in the local task copy. It records the original task hashes so this image pin is explicit. Both profiles use that same copy.

An existing state is never overwritten. Use a fresh `--state-dir` for another experiment. The state manifest records instructions, tasks, images, model, reasoning, CLI version, runner code, lockfile and Docker memory allocation. `DOCKER_CONFIG` is isolated per state for public registry pulls. It retains only the local CLI plugin directories needed for Compose; registry credentials and credential helpers are excluded. Doctor checks Docker and Compose using this same configuration. Global Docker configuration remains under its normal owner.

## Run and compare

```fish
uv run --locked bench.py --state-dir state-chatgpt doctor
uv run --locked bench.py --state-dir state-chatgpt run A
uv run --locked bench.py --state-dir state-chatgpt run B
uv run --locked bench.py --state-dir state-chatgpt report
uv run --locked pier view state-chatgpt/jobs
```

Concurrency is one, with one attempt per profile and no automatic retries. The selected task declares a 3-hour agent budget, which is also the preparation default. Use `--timeout` for an explicit override, and report that override separately from the task budget. Container preparation and verification add to that time. This timeout is not a token or spending cap. ChatGPT usage draws on the signed-in account's allowance.

`comparison.csv` reports each planned task's status, reward, patch delivery and size, new tests passed/total, existing tests preserved/total, agent time, tokens and API-equivalent estimated cost when Pier supplies it. New tests measure the requested behavior; passing existing tests alone does not demonstrate an implementation. Empty or missing patches are separated from nonempty submissions, and partial new-test progress does not change the official binary reward. `summary.json` keeps pass, fail, timeout, infrastructure error, missing and unscored counts separate. Missing measurements remain blank. An API-equivalent cost is not a ChatGPT bill.

The same task authorization permits disposable local commits in both profiles because DeepSWE extracts committed changes for grading. Both agents receive the same elapsed-time budget and deadline, plus explicit authorization for progress checkpoints while broader verification is pending. A checkpoint never claims completion; timeouts remain visible as failures. It prohibits pushing and inspecting hidden verifier inputs. Evaluation files and reference solutions remain on the host; only runtime instructions and skills are uploaded to the agent.

One task checks the integration and establishes a preliminary local baseline. It does not establish that one profile is reliably better or reproduce an official full-benchmark score. Capture the baseline before changing global instructions. Compare instruction candidates and skill changes in separate experiments. Laya routing requires its own later experiment.

## Verification

```fish
uv run --locked python -m unittest -v test_bench
uv run --locked python -m compileall -q bench.py mstack_codex.py auth_state.py
```

Tests cover A/B equivalence, result classification, OAuth permissions and format, single-run locking, atomic refresh, competing modifications and adapter cleanup failures. Run the opt-in Compose regression with `env MSTACK_DOCKER_E2E=1 uv run --locked python -m unittest -v test_bench`. Real model calls are verified by the paired pilot.

## First local pilot

See [the local pilot report](reports/pilot-local.md). Both profiles timed out with reward 0 under the 30-minute budget. Their raw state is ignored by Git. The execution source is retained in that state under `execution-code/`; the task-name reporting fix was applied only after A/B finished. New experiments must use a fresh state with the current runner hashes.

## Reference after the empty-submission pilot

Use a new state such as `state-reference-v2` with the same task, model, reasoning, instructions and 26-skill content, a 10800-second budget, and delivery contract v2. Run A then B once. The budget and contract differ from the first pilot, so this is a new paired baseline rather than a direct attribution of improvement over the 30-minute runs. Tests and collection rules remain unchanged.

Preparation automatically archives execution files and records their hashes, native task budgets and delivery-contract version. Each agent log records its exact runtime deadline and contract hash. Do not edit execution files or evaluation inputs while either profile is running.
