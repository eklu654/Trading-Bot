# Current Research Gate — 2026-10-02

## Purpose

This document records the current evidence state after the corrected $5,000 historical research run. It is a research-status record, not a trading recommendation.

## Verified pipeline state

The latest corrected historical-research workflow completed successfully as GitHub Actions run **#183**, run ID `36967330414`, on commit `21adf5f6ceda593c34fe0709665d29259b1c7d6f` ("Print corrected ETF-exit switcher results").

The workflow completed all 29 research stages successfully, including:

- ETF-001 historical replay, trend/hysteresis matrix, cash sensitivity, local robustness, and chronological validation/holdout evaluation.
- OPTIONS-001 all-market, broad-sideways, turbulent-only, account-feasibility, and defense-variant replays.
- OPTIONS-002 defined-risk iron-condor replay and capital-ladder feasibility from $2,000 through $100,000.
- ETF-exit conditional options analysis.
- Corrected ETF-exit switcher evaluation and chronological holdout gating.
- Research artifact publication.

The repository's full research-test suite also completed successfully on the subsequent commit `e87ab9f49b0f04547a18ca60db02f0462805c356`, with `pytest -q` passing in GitHub Actions run #260.

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

The $5,000 account-feasibility results remain substantially more constrained than unconstrained candidate P&L.

For the 16-delta / 2-point-wing configuration at a 7% defined-risk ceiling:

- Broad-sideways, midpoint fill: 66 accepted trades, ending NLV $4,933.80, net P&L -$66.20, 63.64% win rate.
- Broad-sideways, conservative fill: 66 accepted trades, ending NLV $4,954.80, net P&L -$45.20, 63.64% win rate.
- Turbulent-only, midpoint fill: 36 accepted trades, ending NLV $4,999.80, net P&L -$0.20, 63.89% win rate.
- Turbulent-only, conservative fill: 34 accepted trades, ending NLV $4,952.20, net P&L -$47.80, 61.76% win rate.

At lower risk limits and smaller accounts, contract granularity causes many candidates to be rejected before trading. This means an unconstrained historical options result cannot be substituted for an account-realizable result.

## Corrected ETF-exit switcher holdout gate

The corrected chronological holdout still contains 936 observations, with 2,218 training and 1,008 validation observations.

The mutually-exclusive switcher now suppresses ETF returns throughout an open option lifecycle and applies realized option P&L as a dollar change to the account's current equity. The corrected holdout results are:

| Configuration | Holdout option-realized days | Option P&L | Switcher ending equity | ETF ending equity | Incremental vs ETF | Sample status |
|---|---:|---:|---:|---:|---:|---|
| All-days, conservative | 3 | -$21.60 | $10,922.59 | $11,204.45 | -$281.86 | Insufficient |
| All-days, midpoint | 2 | -$39.40 | $11,192.60 | $11,204.45 | -$11.84 | Insufficient |
| Broad-sideways, conservative | 2 | +$1.60 | $11,167.36 | $11,204.45 | -$37.08 | Insufficient |
| Broad-sideways, midpoint | 2 | +$2.60 | $11,167.66 | $11,204.45 | -$36.79 | Insufficient |
| Turbulent-only, conservative | 2 | +$5.60 | $11,205.45 | $11,204.45 | +$1.01 | Insufficient |
| Turbulent-only, midpoint | 1 | +$24.80 | $11,208.88 | $11,204.45 | +$4.43 | Insufficient |

The evaluator therefore marks every switcher holdout sample as insufficient for a reliable option-sample conclusion. The small positive incremental values in the turbulent-only rows are observations from one or two realized option days, not validated evidence of an edge.

## 0DTE management-timing evidence

The frozen 45-cell 0DTE management-timing matrix is already completed for 1,012 sessions per configuration from 2022-06-16 through 2026-09-28. It remains research-only.

The documented 16D/6D iron-condor 15:55 control returned +14.01% on the $100,000 platform preview, but the experiment contains 45 related hypotheses and therefore has multiple-testing/selection risk. The result is not out-of-sample evidence and is not a production selection.

The next valid 0DTE research step is chronological validation of a frozen candidate/control set, followed by regime conditioning, bounded loss-management tests, cost sensitivity, and actual account-feasibility replay.

## Research implication

The current evidence does **not** establish that the options sleeve improves the ETF portfolio at the $5,000 account size.

The immediate research priorities are:

1. Preserve the chronological holdout and do not tune against it.
2. Treat the $5,000 account-feasibility lifecycle as authoritative for small-account tests.
3. Keep OPTIONS-002 defined-risk structures separate from OPTIONS-001 unconstrained economics.
4. Keep the corrected ETF/options switcher mutually exclusive and require a non-sparse held-out option sample before interpreting incremental results.
5. Advance the frozen 0DTE timing matrix into chronological validation rather than expanding full-sample optimization.
6. Compare any surviving options configuration against the ETF control on common dates and under identical starting capital.
7. Keep candidate promotion and unattended deployment disabled until the economic, account-feasibility, out-of-sample, execution, and risk gates are all satisfied.

No candidate is promoted by this document.
