# Leveraged ETF Research Findings — 2026-10-03

## Completed runs
- Historical ETF workflow run #283 (`4a807bd8cd349f76197e76fc40c12c3377d6115b`) completed successfully through ETF-005.
- Research tests run #492 for the same commit completed successfully.

## ETF-002 directional rotation
The 200-DMA bull/bear directional rotation was not robust across chronological splits.

| Top N | Train annualized | Validation annualized | Holdout annualized | Validation max DD | Holdout max DD |
|---:|---:|---:|---:|---:|---:|
| 1 | -4.27% | -6.54% | 10.87% | -62.21% | -69.99% |
| 2 | 1.62% | -4.39% | 17.33% | -58.11% | -56.94% |
| 3 | 2.21% | -6.21% | 22.73% | -59.27% | -45.88% |
| 5 | 1.53% | -10.54% | 14.72% | -57.12% | -42.69% |

This argues against making inverse-side switching the primary replacement for the existing cash behavior.

## ETF-003 bull-only / Dow pivot
Replacing TQQQ with UDOW in the fixed three-sleeve structure reduced annualized returns in all three chronological splits tested:

| Strategy | Train | Validation | Holdout |
|---|---:|---:|---:|
| Existing TQQQ/SPXL/SOXL | 22.08% | 14.49% | 50.65% |
| UDOW/SPXL/SOXL | 20.32% | 7.89% | 37.15% |

Momentum rotation across the four/five bull candidates produced stronger holdout results in some variants, but validation was much weaker and drawdowns remained large. It therefore remains a research candidate rather than a replacement.

## ETF-004 cash versus bear-side fallback
This was replayed with immediate exit below the 200-DMA and five consecutive sessions above the 200-DMA required to re-enter the bull side. Each original 25% sleeve either stayed cash or used its corresponding bear ETF; the same-underlying bull and bear sides were never held simultaneously.

| Fallback | Train ann. | Validation ann. | Holdout ann. | Validation max DD | Holdout max DD |
|---|---:|---:|---:|---:|---:|
| Cash | 22.47% | 23.68% | 43.85% | -37.66% | -35.68% |
| Bear ETF | 2.52% | 4.32% | 12.16% | -61.23% | -56.06% |

The cash fallback was materially stronger in these tests and had substantially smaller drawdowns.

## ETF-005 transaction-cost sensitivity
The corrected cost replay compared the baseline 200-DMA/5-session rule with the locally robust 200-DMA / 2% exit buffer / 1% re-entry buffer / 5-session rule.

The robust candidate had total turnover of 3.75x during validation and 10.25x during holdout. At 0 bps assumed cost its annualized returns were 18.37% validation and 28.20% holdout. At 50 bps per unit turnover they were 17.63% and 26.44%, respectively. The drawdown and Sharpe changes were modest under these tested costs.

## Important research-integrity correction
The existing ETF-001 matrix split evaluator used the cumulative full-period `portfolio_value` when calculating validation/holdout annualized returns. That means the previously printed validation/holdout annualized-return fields in the matrix robustness/evaluation reports can be overstated because the split was not rebased to 1. The transaction-cost replay correctly rebased each split and should be treated as the reliable reference for the two tested candidates until the matrix generator is corrected.

## Current direction
- Keep the cash fallback as the primary 200-DMA defensive mechanism for now.
- Do not promote the inverse-ETF directional rotation to the core strategy.
- UDOW is worth retaining as a possible future bull-only rotation candidate, but the current fixed Dow substitution did not improve the tested baseline.
- The next high-value research step is to correct the matrix split normalization, rerun the full ETF-001 parameter/robustness evaluation, and then test realistic turnover/costs on the genuinely validated candidates before paper trading.