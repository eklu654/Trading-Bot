# Current Research Gate — 2026-10-02

## Purpose

This document records the current evidence state after the corrected $5,000 historical research run. It is a research-status record, not a trading recommendation.

## Verified pipeline state

The latest historical-research workflow completed successfully on commit `29091e76c07c771d56292686d12829311615144f`.

The workflow completed all 29 research stages, including:

- ETF-001 historical replay, trend/hysteresis matrix, cash sensitivity, local robustness, and chronological validation/holdout evaluation.
- OPTIONS-001 all-market, broad-sideways, turbulent-only, account-feasibility, and defense-variant replays.
- OPTIONS-002 defined-risk iron-condor replay and capital-ladder feasibility from $2,000 through $100,000.
- ETF-exit conditional options analysis.
- ETF-exit switcher evaluation and chronological holdout gating.
- Research artifact publication.

## ETF-001 observations

The full historical ETF-001 summary covers 2010-03-11 through 2026-09-25.

The generated summary reports:

| Model | Total return | Annualized return | Max drawdown |
|---|---:|---:|---:|
| Leveraged ETF buy-and-hold, 0% cash | 208.01x | 38.12% | -82.10% |
| 200-DMA trend, 0% cash | 37.97x | 24.79% | -47.84% |
| 200-DMA + VIX, 0% cash | 10.92x | 16.16% | -52.10% |

These are historical backtest outputs, not forecasts. The buy-and-hold row is included as a control and has materially different drawdown characteristics from the trend-controlled variants.

## OPTIONS-002 observations at the canonical $5,000 account

The $5,000 account-feasibility results are substantially more constrained than unconstrained candidate P&L.

For the 16-delta / 2-point-wing configuration at a 7% defined-risk ceiling:

- Broad-sideways, midpoint fill: 66 accepted trades, ending NLV $4,933.80, net P&L -$66.20, 63.64% win rate.
- Broad-sideways, conservative fill: 66 accepted trades, ending NLV $4,954.80, net P&L -$45.20, 63.64% win rate.
- Turbulent-only, midpoint fill: 36 accepted trades, ending NLV $4,999.80, net P&L -$0.20, 63.89% win rate.
- Turbulent-only, conservative fill: 34 accepted trades, ending NLV $4,952.20, net P&L -$47.80, 61.76% win rate.

At lower risk limits and smaller accounts, contract granularity causes many candidates to be rejected before trading. This means an unconstrained historical options result cannot be substituted for an account-realizable result.

## ETF-exit switcher holdout gate

The latest chronological holdout file divides the 4,162 observations into 2,218 training, 1,008 validation, and 936 holdout observations.

The switcher holdout option sample is currently too sparse for a deployment-quality conclusion:

- All-days conservative: 3 option-realized holdout days.
- All-days midpoint: 2 option-realized holdout days.
- Broad-sideways conservative: 2 option-realized holdout days.
- Broad-sideways midpoint: 2 option-realized holdout days.
- Turbulent-only conservative: 2 option-realized holdout days.
- Turbulent-only midpoint: 1 option-realized holdout day.

The holdout evaluator therefore marks these switcher samples as insufficient for a reliable option-sample conclusion. The small positive incremental values observed in several holdout rows must not be treated as evidence of a validated edge.

## Research implication

The current evidence does **not** establish that the options sleeve improves the ETF portfolio at the $5,000 account size.

The next research gate should therefore focus on increasing the quality and relevance of the options evidence rather than tuning the existing switcher against its sparse holdout sample. In particular:

1. Preserve the existing chronological holdout untouched.
2. Treat the $5,000 account-feasibility lifecycle as authoritative for small-account tests.
3. Keep OPTIONS-002 defined-risk structures separate from OPTIONS-001 unconstrained economics.
4. Continue the frozen 0DTE management-timing research using the already-defined benchmark matrix when valid timestamped/platform data are available.
5. Compare any surviving options configuration against the ETF control on common dates and under identical starting capital.
6. Require a non-sparse held-out sample before treating a switcher result as research evidence.

No candidate is promoted by this document.
