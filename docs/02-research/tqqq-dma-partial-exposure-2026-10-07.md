# TQQQ DMA Partial-Exposure Matrix — 2026-10-07

## Decision

The predeclared partial-exposure tests do **not** improve on the hard 100-DMA binary defense.

Framework:
- $5,000 initial capital
- synthetic daily-reset 3x QQQ
- close-to-next-open signal
- immediate re-entry
- 0% costs and 0% cash yield
- full 1999-03-10 through 2026-10-05 window
- above DMA = 100% exposure
- below DMA = fixed 0%, 25%, 50%, 75%, or 100% exposure

## Key results

| DMA | Below exposure | Ending balance | CAGR | Max DD |
|---:|---:|---:|---:|---:|
| **100** | **0%** | **$128.31B** | **85.69%** | **-45.97%** |
| 100 | 25% | $9.43B | 68.91% | -74.33% |
| 100 | 50% | $337.94M | 49.70% | -95.17% |
| 100 | 75% | $5.88M | 29.24% | -99.37% |
| 125 | 0% | $14.77B | 71.69% | -55.31% |
| 150 | 0% | $5.49B | 65.63% | -63.82% |
| 175 | 0% | $2.05B | 59.81% | -63.82% |
| 200 | 0% | $611M | 52.95% | -71.00% |
| 250 | 0% | $248M | 48.02% | -75.27% |

All tested partial-exposure variants below 125/150/175/200/250 DMA were materially below the 100-DMA binary baseline.

## Interpretation

The result is unusually clear: **when the 100-DMA defense triggers, reducing exposure rather than exiting is substantially worse than going to cash** in this synthetic framework.

This is not merely a drawdown tradeoff. Partial exposure simultaneously produced:
- much lower terminal wealth, and
- much worse maximum drawdown.

The strongest partial case tested was 100-DMA with 25% exposure below the DMA, ending at about $9.43B versus $128.31B for the hard binary rule.

Longer DMAs also underperformed the 100-DMA binary rule. Among binary/cash variants, 125-DMA was the strongest alternative at about $14.77B, still far below $128.31B.

## Research implication

Do **not** replace the current hard 100-DMA exit with a simple fixed fractional exposure ladder. The evidence currently favors:

**100-DMA → 100% invested above / 0% invested below → immediate re-entry.**

Future partial-exposure work should only proceed if it is conditional on additional information (for example, macro/regime context) rather than a fixed percentage below a DMA.
