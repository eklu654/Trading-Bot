# Frozen Fed-DMA Chronological Robustness Results — 2026-10-11

## Run and reproducibility

- GitHub Actions run: [#8 — Frozen Fed-DMA Chronological Robustness](https://github.com/eklu654/Trading-Bot/actions/runs/38128578754)
- Run ID: `38128578754`; commit: `debbeeb2b1873ae4b3821a3c537fa4914dea39fb`
- Result: **success**. Dependency installation, Python compilation, replay, and artifact upload all completed.
- Artifact: `fed-dma-chronological-robustness` (9 files, including daily replay, gates, windows, frozen inputs, and manifest).
- Frozen input: 4,189 common QQQ/TQQQ sessions, 2010-02-11 through 2026-10-07; input CSV SHA-256 `d632ca3613395464a5f80bf050d4080cc767b383838d60620d9bf53e7c2b99ed`.
- Initial equity: $5,000. No parameters were tuned in this run.

## Full-period results at preregistered 25 bps per full exposure change

| Strategy | Ending equity | Max drawdown | Worst rolling 252-session return | Avg. exposure |
|---|---:|---:|---:|---:|
| B0 baseline | $3,852,660 | -73.80% | -72.91% | 93.46% |
| F50 | $3,829,981 | -61.62% | -60.33% | 91.08% |
| F75 | $3,898,855 | -67.99% | -66.91% | 92.27% |

At 25 bps, F50 retained 99.41% of B0 terminal wealth and improved max drawdown by 12.18 percentage points and worst rolling-year return by 12.59 points. However, it underperformed B0 by 22.58 percentage points in the fixed 2018-12-04 to 2019-03-29 recovery-risk window, failing the preregistered 15-point limit.

F75 retained 101.20% of B0 terminal wealth, improved max drawdown by 5.80 points and worst rolling-year return by 6.00 points, and did not breach the preregistered underperformance limits for either the COVID or 2018 recovery-risk window. **F75 passes all six preregistered gates at 25 bps.** This is a development result, not independent validation or authorization for paper/live trading.

## Cost sensitivity

| Cost (bps) | B0 ending equity | F50 ending equity | F75 ending equity |
|---:|---:|---:|---:|
| 0 | $4,040,318 | $4,087,455 | $4,124,684 |
| 10 | $3,964,239 | $3,982,511 | $4,032,878 |
| 25 | $3,852,660 | $3,829,981 | $3,898,855 |
| 50 | $3,673,280 | $3,588,276 | $3,684,975 |

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
