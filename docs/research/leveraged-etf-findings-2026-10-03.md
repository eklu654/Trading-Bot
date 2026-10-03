# Leveraged ETF Research Findings — 2026-10-03

## Completed runs
- Historical ETF workflow run #287 (37108741706, commit 68d59d33b9c2f061dc5720f6502569766b9134bb) completed successfully through ETF-007 and the existing downstream analyses.
- ETF-007 was added specifically as an oracle diagnostic to determine whether directional timing is the main bottleneck.

## ETF-002 directional rotation
The 200-DMA bull/bear directional rotation was not robust across chronological splits.

| Top N | Train annualized | Validation annualized | Holdout annualized | Validation max DD | Holdout max DD |
|---:|---:|---:|---:|---:|---:|
| 1 | -4.27% | -6.54% | 10.87% | -62.21% | -69.99% |
| 2 | 1.62% | -4.39% | 17.33% | -58.11% | -56.94% |
| 3 | 2.21% | -6.21% | 22.73% | -59.27% | -45.88% |
| 5 | 1.53% | -10.54% | 14.72% | -57.12% | -42.69% |

This argues against making the current inverse-side switching rule the primary replacement for cash.

## ETF-003 bull-only / Dow pivot
Replacing TQQQ with UDOW in the fixed three-sleeve structure reduced annualized returns in all three chronological splits tested:

| Strategy | Train | Validation | Holdout |
|---|---:|---:|---:|
| Existing TQQQ/SPXL/SOXL | 22.08% | 14.49% | 50.65% |
| UDOW/SPXL/SOXL | 20.32% | 7.89% | 37.15% |

UDOW remains a valid future bull-only candidate, but the fixed substitution did not improve the tested baseline.

## ETF-004 cash versus bear-side fallback
The initial test used immediate exit below the 200-DMA and five consecutive sessions above the 200-DMA for bull re-entry. Each sleeve either stayed cash or used its corresponding bear ETF; the same-underlying bull and bear sides were never held simultaneously.

| Fallback | Train ann. | Validation ann. | Holdout ann. | Validation max DD | Holdout max DD |
|---|---:|---:|---:|---:|---:|
| Cash | 22.47% | 23.68% | 43.85% | -37.66% | -35.68% |
| Bear ETF | 2.52% | 4.32% | 12.16% | -61.23% | -56.06% |

This shows the tested switching rule favored cash; it does not establish that a better directional signal could not make inverse ETFs useful.

## ETF-005 transaction-cost sensitivity
The corrected cost replay compared the baseline 200-DMA/5-session rule with the locally robust 200-DMA / 2% exit buffer / 1% re-entry buffer / 5-session rule.

The robust candidate had total turnover of 3.75x during validation and 10.25x during holdout. At 0 bps assumed cost its annualized returns were 18.37% validation and 28.20% holdout. At 50 bps per unit turnover they were 17.63% and 26.44%, respectively.

## ETF-006 inverse timing grid
Searching exit confirmation, re-entry confirmation, and DMA buffers materially changed inverse results by period. The best tested validation configuration was approximately 12.34% annualized, while the best holdout configuration reached approximately 41.70% annualized. The winning settings differed materially between validation and holdout, which is evidence against treating one timing configuration as established.

## ETF-007 oracle timing diagnostic
ETF-007 intentionally uses next-day returns and therefore is impossible as a live strategy. Its purpose is to measure the theoretical headroom available if directional timing were perfect.

| Strategy | Train ann. | Validation ann. | Holdout ann. |
|---|---:|---:|---:|
| Oracle: bull vs inverse vs cash | 105.22% | 2381.16% | 422.01% |
| Bull-only oracle: bull vs cash | 11.47% | 55.11% | 27.03% |

The enormous gap between these hindsight upper bounds and the ordinary signal strategies is the strongest evidence so far that timing/regime identification is a major research bottleneck. The oracle is not a candidate strategy and must not be used for live selection.

The result also changes the research framing: we should not conclude that inverse ETFs are inherently unhelpful merely because the first 200-DMA switch underperformed cash. There is demonstrable downside opportunity in hindsight; the unresolved question is how much of it can be captured ex ante without excessive false signals, turnover, or inverse-ETF path-dependence losses.

## Research-integrity correction
The original ETF-001 matrix split evaluator used cumulative full-history portfolio_value when calculating validation/holdout annualized returns. Those earlier matrix validation/holdout annualized figures are not reliable for candidate selection.

The matrix generator has now been corrected in commit 0b360bf8ef66914dffce7bf47c277c7dd47158ed to independently rebase portfolio_value and recompute split drawdown before calculating split metrics. The corrected matrix must be rerun before any parameter is promoted.

## Current direction
1. Rerun the corrected ETF-001 matrix and downstream robustness evaluation.
2. Use only training/validation results from the corrected split calculations for candidate selection; keep holdout untouched until selection is frozen.
3. Test realistic transaction costs and turnover on candidates that survive corrected validation.
4. Build the next directional-signal research around interpretable, ex-ante features: 200-DMA distance, 200-DMA slope, 50/200-DMA relationship, 20/60-day momentum, persistence below trend, cross-market confirmation, and volatility/VIX.
5. Compare the same signal's choices of cash vs inverse exposure rather than comparing unrelated switching rules.
6. Test partial defensive exposure as well as all-or-nothing switching.
7. Only after a candidate survives chronological validation and realistic costs should it become a paper-trading candidate.
