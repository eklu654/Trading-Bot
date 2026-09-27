# VIX and Buying-Power Allocation Research

**Status:** Unresolved — no authoritative numerical schedule frozen  
**Last reviewed:** 2026-09-27

## Finding

The project previously considered a numerical table mapping VIX ranges to percentages of buying power allocated to options. Current primary-source research does **not** justify treating that table as an official universal tastytrade/tastylive rule.

The table must therefore **not** be encoded as "the tastytrade method."

## What the primary sources do establish

The current tastytrade backtesting API supports VIX as an explicit entry and exit condition. Its documented example can require VIX to be between a minimum and maximum at entry and can also use a VIX condition at exit.

This establishes that volatility-regime filtering is a supported research dimension. It does not establish a specific production allocation curve.

The official backtesting API also supports maximum active trials. This gives the project a second, independent way to constrain concurrent option risk.

## Project interpretation

VIX should initially be treated as a **risk-budget input**, not as a direct instruction such as "VIX X means allocate Y%."

The research engine should be able to test several classes of allocation model:

### Model A — Fixed risk budget

Use a constant maximum aggregate options buying-power budget regardless of VIX.

Purpose: establish a control group.

### Model B — Piecewise VIX budget

Define discrete VIX bands and assign each band a maximum buying-power budget.

Purpose: test the user's hypothesis that elevated implied volatility may justify greater premium-selling capacity while preserving explicit risk limits.

### Model C — Continuous VIX function

Map normalized VIX or IV-rank information to a continuous risk budget.

Purpose: avoid abrupt changes at arbitrary VIX boundaries.

### Model D — VIX plus portfolio stress

Use VIX together with realized volatility, drawdown, beta-weighted Delta and current buying-power usage.

Purpose: test whether VIX alone is an inadequate proxy for portfolio risk.

## Important distinction

Higher implied volatility can increase option premium, but higher volatility can also increase mark-to-market losses, buying-power requirements and tail risk. Therefore:

**higher VIX ≠ automatically safer option selling**

Any allocation increase at higher VIX must be validated against drawdown, buying-power expansion and adverse price-gap scenarios.

## Small-account constraint

The initial account size is $2,000. Whole-contract granularity means percentage-based allocation rules can become discontinuous. A nominal 1–3% position-sizing preference can be impossible to implement precisely when one contract represents substantially more than that percentage.

The system should therefore calculate:

1. desired risk budget,
2. contract-level buying-power impact,
3. post-trade aggregate buying-power usage,
4. post-trade beta-weighted Delta,
5. worst-case or defined-risk loss where available,
6. remaining liquidity buffer.

If a candidate trade cannot fit the hard risk constraints, it is rejected rather than forced into the portfolio.

## Research matrix

The backtester should compare VIX allocation models over identical historical periods and identical fills/transaction-cost assumptions.

Required outputs:

- CAGR / annualized return
- maximum drawdown
- volatility
- Sharpe and Sortino
- worst daily loss
- worst trade
- buying-power utilization
- frequency of buying-power spikes
- frequency of rejected entries
- time spent without eligible trades
- turnover
- exposure by VIX regime
- tail-loss behavior

The project should prefer robustness across periods over the strongest result in one historical window.

## Current decision

No numerical VIX-to-buying-power table is authoritative.

A project-specific schedule may be created later, but it must be explicitly labeled **experimental** and compared against fixed-budget controls.

## References

- tastytrade Developer Docs — Create a backtest: https://developer.tastytrade.com/reference/backtesting/postBacktests/
- tastytrade Developer Docs — Run a backtest: https://developer.tastytrade.com/docs/guides/backtesting/
