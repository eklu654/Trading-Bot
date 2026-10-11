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
