# DeepSWE local pilot: unchanged instructions and managed skills

Both profiles timed out under the 30-minute agent budget and received reward 0. Neither produced a committed patch. The task collects `git diff <base> HEAD`, so uncommitted agent work was excluded and the verifier received an empty submission. The dataset task declares a 10800-second agent budget; the pilot explicitly overrode it to 1800 seconds. This establishes a preliminary local baseline and verifies the integration; it does not establish a quality difference between profiles.

| Measurement | A: global instructions | B: instructions + 26 skills |
|---|---:|---:|
| Status | AgentTimeoutError | AgentTimeoutError |
| Reward | 0 | 0 |
| New tests passed | 0/37 | 0/37 |
| Existing tests passed | 1267/1267 | 1267/1267 |
| Input tokens, including cache | 8,950,680 | 7,257,791 |
| Cached input tokens | 8,529,920 | 7,072,768 |
| Output tokens | 42,970 | 45,701 |
| Pier API-equivalent estimated cost | $2.124212 | $1.534333 |

Cached tokens are part of input tokens, not an additional amount. The estimated cost is supplied by Pier and is not a ChatGPT bill or a measurement of the account allowance. Differences in token counts from one attempt are not an estimate of the effect of skills.

## Frozen conditions

- Task: `dynamodb-toolbox-lazy-recursive-schemas`; TypeScript; selection seed 42.
- Dataset commit: `0b9fabbb63b9104d678fe965e1632f2dd9eaa2ea`.
- Model: `gpt-6.1-sol`; reasoning: `high`.
- Codex `0.159.0`, Pier `0.3.1`, Python `3.13.2`, sandbox Node `24.12.0`.
- Apple Silicon MacBook Pro, 16 GiB host RAM; Linux AMD64 images through Docker emulation. Docker allocation: 10 GiB and 6 CPUs; task declares 8 GiB and 2 CPUs.
- Task/verifier image: `public.ecr.aws/d3j8x8q7/swe-bench-202605@sha256:1d4464b3be2c9b22e0835a50047bd8a87aa5bb077acd4ec60e12a5b0d164d030`.
- One attempt per profile, concurrency one, no automatic retry. Execution order A then B; B reused image/build caches. Setup time is not an agent-quality comparison.
- Global instructions SHA-256: `94da4db0016995c47a52a63cac44a00339614a4f9f77594cafa00e738ae0c157`.
- Both use the same instructions and task snapshot. B adds 26 skills / 55 files. Successful B commands read the entry points for `conventions-aware-engineering`, `unslop` and `verification-before-completion`; this does not prove compliance with every instruction.

## Local evidence and provenance

- State and raw results: `evals/deepswe/state-chatgpt-10g-v2/` (excluded from Git).
- Repository HEAD at preparation: `f62b9efa634174874b20aeaa5bd9f40cf16ec13b`. The integration was uncommitted; the recorded file hashes define the execution source, not that commit alone.
- `execution-code/` within the state preserves the runner, adapter, auth helper, lockfile and runtime declarations used by both jobs. Their hashes match the prepared manifest.
- Execution runner SHA-256: `742a2ac30a816ac13b30965d99f1491ef61b590c53955c7b50f255cb0bbcd629`.
- Execution adapter SHA-256: `81b32ad911f8e5a7e52e1d6195550ae3814e2f35ff4b83569afea1ed82a53905`.
- The report-only fix was applied after both jobs finished: results use the task name declared in frozen `task.toml`, which includes the `datacurve/` namespace. The old comparator incorrectly marked both results missing. Raw results and execution inputs were not changed.
- Corrected report generator SHA-256: `89eed29d3bf4fb976003d7f2c69f8b050877b2a624d22a8774f7354d4f3900d0`.
- `comparison.csv`, `summary.json` and `reporting.json` in the state retain the final comparison and audit hashes.

## Validation

- 17 runner tests passed, including real Docker Compose with the isolated configuration.
- A/B completed and independently graded. Both preserved renewed OAuth credentials; doctor passed after A before B.
- The reporter regression was reproduced against the real result format before fixing it.
