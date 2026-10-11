# Research Continuation Log — Frozen Chronological Robustness Test — 2026-10-11

## Scope

Registered and implemented the next bounded test for the existing Fed-active / QQQ-below-200-DMA partial-exposure overlay. No thresholds or strategy parameters were tuned.

## Preregistration

- Protocol: [FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_PREREGISTRATION_2026-10-11.md](FED_DMA_OVERLAY_CHRONOLOGICAL_ROBUSTNESS_PREREGISTRATION_2026-10-11.md)
- Frozen candidates: B0, F50 (50% TQQQ target during the sticky overlay state), and F75 (75% target).
- Cost sensitivity: 0, 10, 25, and 50 bps per full exposure change.
- Fixed chronological windows: 2010–2014, 2015–2019, 2020–2021, 2022–2024, 2025 onward, plus the fixed 2018–2019 recovery-risk, COVID crash/rebound, and 2022 tightening windows.
- Decision gates frozen before the next run: at least 90% terminal-wealth retention at 25 bps, >=5 percentage-point max-DD improvement, >=5 percentage-point worst rolling-year improvement, and no >15 percentage-point underperformance in the fixed 2018–2019 or COVID windows.
- All windows are retrospective descriptive checks. The history has already been inspected; this is not an untouched holdout and cannot alone authorize paper/live trading.

## Implementation

- Replay script: [fed_dma_chronological_robustness.py](../../research/fed_dma_chronological_robustness.py)
- Workflow: [fed-dma-chronological-robustness.yml](../../.github/workflows/fed-dma-chronological-robustness.yml)
- The replay creates a same-run B0/F50/F75 comparison from the same downloaded QQQ/TQQQ input, records its SHA-256, uses close[t] signals with next-open execution, and emits daily equity, window, cost, comparison, gate, transition, and manifest outputs.
- The workflow is configured to run on pushes affecting the frozen protocol/script/dependencies, as well as manual dispatch. The latest implementation commit is `6dc114d340a6783b240946e9ef4eb5114d8cf228`.
- No candidate has been selected. Wait for the Actions result and inspect the run logs/artifacts before making a decision. If either candidate fails any gate, do not relax the criteria after seeing the results.

## Interpretation constraint

F50/F75 are still development candidates because their full-period performance was already inspected. A successful replay is evidence of reproducibility and cross-regime behavior, not independent statistical validation.
