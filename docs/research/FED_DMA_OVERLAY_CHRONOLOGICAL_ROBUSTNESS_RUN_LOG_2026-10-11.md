# Workflow Execution Log Addendum — 2026-10-11

- Successful Actions run #8: https://github.com/eklu654/Trading-Bot/actions/runs/38128578754
- Run ID: 38128578754; head commit: debbeeb2b1873ae4b3821a3c537fa4914dea39fb.
- All workflow steps completed successfully: dependency install, Python compile, frozen replay, artifact upload.
- Frozen inputs: 4,189 common QQQ/TQQQ sessions, 2010-02-11 through 2026-10-07; SHA-256 d632ca3613395464a5f80bf050d4080cc767b383838d60620d9bf53e7c2b99ed.
- At 25 bps: B0 ending equity $3,852,660 / max DD -73.80%; F50 $3,829,981 / max DD -61.62%; F75 $3,898,855 / max DD -67.99%.
- F50 failed the preregistered 2018 recovery-window gate. F75 passed all six preregistered gates.
- Critical caveat: excluding 2022-2024 returns without changing signals leaves F75 at $2,528,414 vs B0 $2,733,976. The modest full-period wealth advantage is concentrated in that period. F75 remains research-only; no paper/live promotion.
- Full results: FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_RESULTS_2026-10-11.md.


## Audit correction and rerun — 2026-10-11

- Review of the run #8 script found it downloaded a fresh QQQ/TQQQ snapshot instead of using the canonical frozen B0 input. Its zero-cost B0 final ($4,040,318) differed slightly from the canonical run #29 frozen-input value ($4,040,314.667614526). This is consistent with source-snapshot drift and means run #8 is not the authoritative exact-input reconciliation.
- Also identified an edge-case accounting risk: a shock still waiting for its +10% recovery at the sample end must remain defensive through the last session. Added terminal-event censoring and three synthetic guardrail tests.
- Corrected implementation now downloads the immutable frozen input from run #29 (artifact `tqqq-actual-partial-dma-matrix`, ID `11694047458`), verifies its SHA-256 (`6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`), reconstructs B0 independently, asserts exact signal equality to canonical `b0_signal`, and fails unless the 0-bps B0 terminal equity matches $4,040,314.667614526 within $0.00001.
- Added the artifact-download step and synthetic tests to the workflow. Latest commit at time of note: `0bbd719b94c89419ca5cf8546b31dbf542003672`.
- Current rerun: [Actions run #14](https://github.com/eklu654/Trading-Bot/actions/runs/38129052911). Do not use the old run #8 performance values as final candidate evidence until this canonical-input rerun completes and the exact B0 reconciliation passes. Run #8 remains an execution-history record, not the final validated result.


## Canonical-input rerun completed — 2026-10-11

- Authoritative run #15: [38129135473](https://github.com/eklu654/Trading-Bot/actions/runs/38129135473), conclusion `success`, head commit `e275c8b8d9adf05e26c9bb55e998b713c095ee60`.
- Artifact ID `11699001137`; all workflow steps passed, including artifact retrieval, exact B0 signal reconciliation, three synthetic terminal-censoring tests, replay, and upload.
- Exact input hash check passed: source CSV SHA-256 `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`. Reconstructed B0 matched all 4,189 frozen `b0_signal` values. Zero-cost B0 ending equity was `4040314.667614814`, versus canonical `4040314.667614526` (difference `0.000000288`).
- Canonical-input 25-bps results: B0 `$3,852,657`, -73.80% max DD; F50 `$3,829,979`, -61.62% max DD; F75 `$3,898,853`, -67.99% max DD. F50 fails the 2018 recovery gate; F75 passes all six preregistered gates.
- F75 still loses to B0 in the fixed exclusion diagnostic outside 2022–2024: `$2,528,413` vs `$2,733,976`. Keep F75 research-only and do not tune thresholds.
- The initial run #8 performance report is superseded for baseline reproducibility by run #15. The strategy decision is unchanged; only canonical source control and precise terminal balances have been corrected.
- Updated results: [FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_RESULTS_2026-10-11.md](FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_RESULTS_2026-10-11.md).


## Forward evaluation registered

- Added preregistration: [F75 Prospective Shadow Evaluation](F75_PROSPECTIVE_SHADOW_EVALUATION_PREREGISTRATION_2026-10-11.md).
- The plan fixes B0/F75 rules, 25-bps primary costs, 0/50-bps sensitivity, $5,000 shadow starting equity, canonical market input through 2026-10-07, causal close-to-next-open execution, and a 252-return-bearing-session observation horizon.
- No orders are placed. The next implementation task is a shadow-only scheduled monitor with persistent daily ledger, exact B0 reconciliation, stale-data fail-closed behavior, and no tuning during the observation window.
- Narrowed the partial-DMA matrix workflow's push filters to its actual script and dependencies so unrelated research edits no longer trigger the expensive matrix replay.


## Final housekeeping verification — 2026-10-11

- Partial-DMA matrix workflow filter cleanup validated by successful [run #61](https://github.com/eklu654/Trading-Bot/actions/runs/38129305559); its push trigger now targets only the matrix script and its two direct Python dependencies, plus the workflow file.
- Exact-canonical Fed-DMA run #15 remains successful and is the authoritative result. The historical F75 gate passes do not override the 2022-2024 concentration warning.
- Forward shadow plan is registered but the scheduled/persistent ledger implementation has not been started. Keep it separate from broker execution; the current branch is a research branch, and GitHub scheduled workflows only run from the repository's default branch, so do not imply a daily schedule is active without resolving branch placement.
