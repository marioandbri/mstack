# DeepSWE corrected local reference

Both profiles received official task reward **1/1**, passed **37/37 new tests**, and preserved **1267/1267 existing tests**. Each submitted a nonempty committed patch and finished without a trial exception. This is a useful reference for this task; one task and one attempt per profile cannot establish general reliability or a benefit from skills.

| Measurement | A: global instructions | B: instructions + 26 skills |
|---|---:|---:|
| Official task reward | 1/1 | 1/1 |
| New tests passed | 37/37 | 37/37 |
| Existing tests preserved | 1267/1267 | 1267/1267 |
| Submitted patch bytes | 173865 | 133959 |
| Agent elapsed wall time | 84m 27s | 80m 44s; interrupted by sleep |
| Input tokens, including cache | 18,760,028 | 14,065,782 |
| Cached input tokens | 18,391,808 | 13,714,176 |
| Output tokens | 116,816 | 72,001 |
| Pier API-equivalent estimated cost | $3.743781 | $2.794640 |

Cached tokens are already included in input tokens. Estimated costs are not ChatGPT bills or measurements of the account allowance. The observed token difference is descriptive; it does not estimate the causal effect of skills.

## Conditions and interpretation

The task is `dynamodb-toolbox-lazy-recursive-schemas`, selected with seed 42 from the TypeScript subset. Dataset commit is `0b9fabbb63b9104d678fe965e1632f2dd9eaa2ea`. Both profiles use `gpt-6.1-sol`, reasoning `high`, Codex `0.159.0`, Pier `0.3.1`, Python `3.13.2`, and sandbox Node `24.12.0`. The Apple Silicon host executes Linux AMD64 images through emulation; Docker has 10 GiB and 6 CPUs, while the task declares 8 GiB and 2 CPUs. A ran before B, with concurrency one and no automatic trial retry.

Both use the task-native 10800-second agent budget and delivery contract v2: save checkpoints after focused checks and keep correcting and verifying. The tests, collection rules, instructions, model, reasoning, task image, and 26-skill content match the first pilot. Budget and delivery instructions changed equally for A and B, so the improvement over the old empty submissions cannot be attributed to skills. The original 30-minute results remain intact in `state-chatgpt-10g-v2`.

The Mac entered **Clamshell Sleep at 2026-10-05T04:35:52Z during B** and later maintenance sleep. B logged a transient stream reconnection and resumed, then finished with no trial exception. Its verifier still evaluated the committed patch and passed every fixed test. Timing is affected by suspension and reconnection; this run supports a correctness reference, not a clean speed comparison. Agent-created local tests differ between profiles and are not the common score.

After both trials, the runner gained a process-scoped idle-sleep assertion and a closed-lid preflight check. Keep the MacBook lid open throughout future benchmarks. This change does not alter these runs or global power settings; new runs require a fresh state.

## Evidence and reproduction

Local state: `evals/deepswe/state-reference-v2/` (excluded from Git). It contains raw jobs, verifier rewards, committed patches, `comparison.csv`, `summary.json`, the original execution source, and metadata-only `host-sleep-evidence.json`. Both raw verifier rewards agree with trial results; doctor passed with the frozen source after A/B. Credentials remain outside the state.

Frozen execution commit: `173b680c9ac397a156d318357fabd3d9f7feea21`. Runner SHA-256: `627f02e9c3be9e914fd8935b2dd18213976bb30146c2db0b3b73d3981d6b024a`. Adapter SHA-256: `22ce3970a7edc794b98b1d24a138b92b9aa39eea2673ebe341ce857fe822a371`. Manifest SHA-256: `bb82a9137eb14022682737a3a00f2df20d16d2f8f8e78e5626d6712bc0f170e9`.

- A trial: `dynamodb-toolbox-lazy-recursive__cRHLKoS`. Patch SHA-256: `5ca102bf59e9229facb8a1f4c5da302a678934c1903ab58b90f52a9a126ba150`. Result SHA-256: `c28f6a9daf6b7c1d5057cdc2e8433a5aecd144f7bd84179ed8766d981242af89`.
- B trial: `dynamodb-toolbox-lazy-recursive__XqehKTf`. Patch SHA-256: `d832208645e9160f556fdbdacf09441d129773236773b1667df3eea0a95cd3c7`. Result SHA-256: `92a858a60f7efeb226d249a4840d6bf27552d8f97a567c8e6e4253107fd3b437`.

Reproduce historical verification without creating bytecode in the frozen archive:

```fish
cd /Users/mario.brito/personal/engineering-skills/evals/deepswe
env PYTHONDONTWRITEBYTECODE=1 uv run --locked python state-reference-v2/execution-code/bench.py --state-dir /Users/mario.brito/personal/engineering-skills/evals/deepswe/state-reference-v2 doctor
```

Use the same archived command with `report` to regenerate the comparison. Do not rerun A or B in this state.

## Verification on 2026-10-06

The previously interrupted verification was repeated with the lid open and a temporary idle-sleep assertion. The repository suite passed 28 tests, with one optional Portless HTTP test skipped and zero failures. Its real Git/temporary-HOME installer suite completed in 9.64 seconds, within the original 30-second timeout; no timeout limit was increased.

All 24 benchmark-runner tests passed, including real Docker Compose and acquisition/release of the macOS idle-sleep assertion. Repository validation passed for 26 skills and 45 Markdown files. The active installation at `9fb33a24252d36ed6a9362441df1a51d7e8d65b3` passed verification of all 110 targets and owned settings.

The historical doctor passed using frozen source without bytecode writes. Original A/B result and patch hashes still match those recorded above; both rewards remain 1/1. No new benchmark trials or model calls were made.

MySQL retained its original container identity and responded to `SELECT 1`. PostgreSQL retained its original container, `pgdata` volume, and configured loopback binding on port 5432, but was stopped when inspected. It was not started or modified during this verification, so no live PostgreSQL query was performed. PostgreSQL is not required by the test suites repeated here.
