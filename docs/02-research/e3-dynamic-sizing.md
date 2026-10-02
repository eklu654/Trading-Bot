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
