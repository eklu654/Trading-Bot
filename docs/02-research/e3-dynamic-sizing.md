# E3: Dynamic ETF Selection + Volatility Sizing

## Purpose

E3 tests whether a simple, predeclared position-sizing layer can improve the
E2 risk-adjusted family-selection baseline without tuning on the validation or
holdout periods.

## Rule

E2 selects the family using trailing 60-session return divided by trailing
20-session annualized realized volatility, then selects leverage using the
existing SPY 200-DMA/VIX controller.

For the selected ETF, E3 uses only the prior session's trailing 20-session
realized volatility. Allocation is:

    min(1.0, SPY_realized_vol / selected_ETF_realized_vol)

The remainder is cash. No fixed volatility target is optimized.

## Evaluation

Fixed chronological periods:
- Train: 2010-2019
- Validation: 2020-2022
- Holdout: 2023 through the available 2026 data

Primary questions:
1. Does sizing reduce the E2 drawdown, especially during 2022?
2. Does it preserve enough upside to remain substantially above SPY?
3. Does it improve risk-adjusted metrics without relying on holdout tuning?

E3 is not promoted based on one metric. It must be compared against E2,
SPY, static leveraged ETFs, and 200-DMA controls using CAGR, annual returns,
relative performance, drawdown, recovery behavior, volatility, downside risk,
and stress periods.


## Results from run #33

The full-period dataset runs from 2010-01-04 through 2026-09-25.

| Variant | CAGR | Volatility | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|
| E3 full-ratio sizing | 9.38% | 11.62% | 0.831 | -16.79% |
| E3 square-root sizing | 15.78% | 20.65% | 0.814 | -31.20% |
| SPY 1x benchmark | 14.15% | 17.05% | 0.863 | -33.72% |
| E2 risk-adjusted selection | 24.47% | 42.88% | 0.730 | -62.33% |

Chronological results:
- Full-ratio sizing: train 7.56%, validation 7.33%, holdout 16.23%.
- Square-root sizing: train 13.35%, validation 8.91%, holdout 28.80%.

Stress behavior:
- 2022: full-ratio -12.47%; square-root -22.83%; E2 -41.77%; SPY -18.18%.
- 2023-2024 recovery: full-ratio +39.79%; square-root +84.15%; E2 +201.32%; SPY +57.58%.

Interpretation: volatility sizing clearly reduces downside, but full normalization sacrifices too much upside. Square-root sizing modestly exceeds SPY's historical CAGR while materially reducing E2 drawdown, but it does not preserve E2's large return advantage. Neither sizing rule is promoted as the final strategy.

The next stage is therefore the AI regime/action selector, which can learn when to emphasize E2-style return seeking versus lower-exposure behavior instead of fixing the trade-off with a single hand-coded sizing formula.
