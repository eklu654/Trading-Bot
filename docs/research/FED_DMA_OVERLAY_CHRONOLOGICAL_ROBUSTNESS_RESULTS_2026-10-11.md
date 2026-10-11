# Frozen Fed-DMA Chronological Robustness Results — 2026-10-11

> **Authoritative rerun update (2026-10-11):** Use [workflow run #15](https://github.com/eklu654/Trading-Bot/actions/runs/38129135473), artifact ID `11699001137`, for the canonical-input result. The earlier run #8 used a fresh market-data download and is superseded for exact baseline reconciliation. Run #15 loaded the canonical frozen input from matrix run #29, verified SHA-256 `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`, matched all 4,189 B0 signal values exactly, and matched the canonical zero-cost terminal balance to within $0.0000003. The strategy decision and gate outcomes did not change.

## Run and reproducibility

- Authoritative GitHub Actions run: [#15 — Frozen Fed-DMA Chronological Robustness](https://github.com/eklu654/Trading-Bot/actions/runs/38129135473) (the original execution was run #8)
- Run ID: `38129135473`; commit: `e275c8b8d9adf05e26c9bb55e998b713c095ee60`
- Result: **success**. Dependency installation, Python compilation, replay, and artifact upload all completed.
- Artifact: `fed-dma-chronological-robustness` (ID `11699001137`; 11 files, including the canonical source input, daily replay, gates, windows, and manifest).
- Canonical frozen input: 4,189 common QQQ/TQQQ sessions, 2010-02-11 through 2026-10-07; source CSV SHA-256 `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`. Reconstructed B0 signal matched all 4,189 canonical signal values exactly; zero-cost ending equity was `$4,040,314.667614814` versus canonical `$4,040,314.667614526` (absolute difference under $0.000001).
- Initial equity: $5,000. No parameters were tuned in this run.

## Full-period results at preregistered 25 bps per full exposure change

| Strategy | Ending equity | Max drawdown | Worst rolling 252-session return | Avg. exposure |
|---|---:|---:|---:|---:|
| B0 baseline | $3,852,657 | -73.80% | -72.91% | 93.46% |
| F50 | $3,829,979 | -61.62% | -60.33% | 91.08% |
| F75 | $3,898,853 | -67.99% | -66.91% | 92.27% |

At 25 bps, F50 retained 99.41% of B0 terminal wealth and improved max drawdown by 12.18 percentage points and worst rolling-year return by 12.59 points. However, it underperformed B0 by 22.58 percentage points in the fixed 2018-12-04 to 2019-03-29 recovery-risk window, failing the preregistered 15-point limit.

F75 retained 101.20% of B0 terminal wealth, improved max drawdown by 5.80 points and worst rolling-year return by 6.00 points, and did not breach the preregistered underperformance limits for either the COVID or 2018 recovery-risk window. **F75 passes all six preregistered gates at 25 bps.** This is a development result, not independent validation or authorization for paper/live trading.

## Cost sensitivity

| Cost (bps) | B0 ending equity | F50 ending equity | F75 ending equity |
|---:|---:|---:|---:|
| 0 | $4,040,315 | $4,087,452 | $4,124,681 |
| 10 | $3,964,236 | $3,982,509 | $4,032,875 |
| 25 | $3,852,657 | $3,829,979 | $3,898,853 |
| 50 | $3,673,277 | $3,588,274 | $3,684,972 |

F75 remains slightly ahead of B0 at 50 bps (+$11,694), while F50 is behind at 25 and 50 bps. Both overlays improve drawdown metrics throughout this cost grid; F75's maximum-drawdown improvement ranges from about 5.73 to 5.88 percentage points.

## Concentration diagnostic: exclude 2022–2024 returns without changing signals

At 25 bps, compounded equity excluding only the returns dated 2022-01-01 through 2024-12-31 is:

- B0: $2,733,976
- F50: $2,318,313 (about $415,664 below B0)
- F75: $2,528,414 (about $205,562 below B0)

The terminal-wealth advantage of F75 does **not** persist when the 2022–2024 return window is excluded. This is an important concentration warning: the apparent full-period terminal-wealth edge is dependent on that window, even though the overlay improves full-period drawdown statistics. Do not describe the terminal-wealth advantage as broadly regime-independent.

## Interpretation and next decision

1. The workflow is operational and the frozen replay completed successfully.
2. F50 is rejected by the preregistered recovery-window gate.
3. F75 passes the preregistered gates, but remains a research candidate only. Its wealth edge is small at realistic costs and does not survive the 2022–2024 exclusion diagnostic.
4. Do not tune the gates after seeing these results. Do not promote F75 to paper/live trading based on this retrospective run alone.
5. The next useful step is an explicitly predeclared, untouched forward/holdout evaluation or a further independent robustness design, with special attention to whether drawdown improvement justifies the weak and regime-concentrated terminal-wealth benefit.

## Files

The run artifact contains:
- `fed_dma_chronological_robustness_summary.csv`
- `fed_dma_chronological_robustness_comparison.csv`
- `fed_dma_chronological_robustness_gates.csv`
- `fed_dma_chronological_robustness_windows.csv`
- `fed_dma_chronological_robustness_ex_2022_2024.csv`
- `fed_dma_chronological_robustness_daily.csv`
- `fed_dma_chronological_robustness_transitions.csv`
- `fed_dma_chronological_robustness_frozen_inputs.csv`
- `fed_dma_chronological_robustness_manifest.json`


## Interpretation clarification — regime specialization versus concentration risk

The 2022–2024 exclusion diagnostic is descriptive and is **not a rejection test by itself**. Excluding those returns while leaving the original signals and all other returns intact shows that F75's small full-period terminal-wealth edge depends on this window; it does not establish that the overlay is overfit or that its defense is ineffective in other bear markets.

This concentration can be consistent with the intended thesis: reduce leveraged exposure during a prolonged tightening / below-200-DMA regime. The key unanswered question is whether the gain reflects repeatable protection in the target regime or a one-episode interaction specific to 2022–2024.

The existing metrics give a mixed but promising risk/return trade-off at 25 bps:
- F75 ending wealth: $3,898,853 vs B0 $3,852,657 (+$46,196, +1.20% relative terminal wealth).
- Maximum drawdown: -67.99% vs -73.80% (5.80 percentage-point improvement).
- Worst rolling 252-session return: -66.91% vs -72.91% (6.00-point improvement).
- Excluding the 2022–2024 returns: F75 $2,528,414 vs B0 $2,733,976. This signals regime dependence, not necessarily overfitting.

Therefore, retain F75 as a serious defensive-specialization candidate rather than rejecting it solely on this exclusion test. Do not promote it yet: the full-sample maximum drawdown is still nearly 68%, and all historical windows are retrospective/descriptive rather than untouched holdouts.

Next analysis should be predeclared and mechanism-focused, not a broad parameter sweep:
1. Quantify defensive-state days, turnover, entry/exit dates, and P&L contribution by fixed calendar regime.
2. Compare B0 and F75 specifically across independently specified slow/prolonged bear episodes and their recoveries, reporting absolute loss, relative return, max drawdown, time under water, and missed rebound participation.
3. Distinguish the 2022–2024 tightening bear from 2000–2002, 2007–2009, 2011, 2015–2016, 2018, and COVID; do not claim these were tested with equivalent real TQQQ history. Use underlying index returns for pre-TQQQ periods, clearly label any leveraged simulation as synthetic, and never present it as actual TQQQ performance.
4. Preserve the frozen rules and the 252-session prospective shadow plan. Do not tune F75 in response to any one episode.

Decision framing: the 2022–2024 concentration warning is a reason to test whether the defense generalizes, not a reason to dismiss a candidate whose stated purpose is regime-specific defense.
