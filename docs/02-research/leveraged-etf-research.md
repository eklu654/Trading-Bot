# Leveraged ETF Strategy Research

**Status:** Hypothesis stage — thresholds not frozen  
**Last reviewed:** 2026-09-27

## Strategy hypothesis

The initial ETF instance is designed around:

- TQQQ
- SPXL
- SOXL
- cash as the fourth allocation slot

The working concept is approximately 25% per ETF slot with unused allocation held in cash.

The proposed trend rule is:

1. Exit an ETF after a daily close below its 200-day moving average.
2. Do not immediately re-enter.
3. Require the ETF to remain above its 200-day moving average for a full week before repurchasing it.

A separate VIX safety mechanism has been proposed, with an initial idea around VIX 28 for broad ETF de-risking. This threshold is a **hypothesis**, not an established optimal value.

## Why the rule needs empirical testing

Leveraged ETFs reset their leverage exposure daily. Their multi-day results therefore depend on the path of the underlying, not simply the underlying's cumulative return multiplied by the leverage factor.

This makes a long-term trend-following rule potentially relevant, but it also creates several risks:

- volatility drag
- path dependency
- large gap losses
- rapid regime changes
- whipsaw around the moving average
- concentration in correlated technology/equity exposures

TQQQ, SPXL and SOXL are also not independent risk sources. A portfolio can appear diversified by ticker while remaining highly exposed to a common equity/technology risk factor.

## Required experiments

The research engine should test at minimum:

### Trend parameters

- 100, 150, 200 and 250 trading-day moving averages
- one-day confirmation vs multi-day confirmation
- one-week re-entry confirmation
- alternative re-entry windows
- close-based vs intraday triggers

### VIX parameters

Test a range rather than hard-coding 28:

- no VIX filter
- low threshold
- medium threshold
- high threshold
- hysteresis: separate exit and re-entry thresholds
- VIX-only filter vs VIX plus trend filter

The exact candidate values should be selected before running the experiment and preserved in the research record.

### Allocation

Compare:

- equal 25% ETF slots
- volatility-scaled allocations
- equal-risk allocations
- cash-heavy defensive variants

The initial production concept remains equal-slot allocation until research changes it.

## Hysteresis requirement

A VIX safety rule should not use a single threshold for both exit and re-entry.

For example, the research design should allow:

- exit when VIX is at/above an upper threshold;
- re-entry only after VIX falls below a lower threshold;
- optionally require the trend condition to be satisfied as well.

This reduces repeated entry/exit around one boundary. The actual thresholds remain experimental.

## Correlation and concentration

The portfolio must measure:

- rolling pairwise correlation
- factor exposure where available
- aggregate equity beta
- technology concentration
- maximum simultaneous ETF exposure

A 75% gross allocation to leveraged ETFs can represent much more than 75% effective directional exposure. The risk engine should therefore track both nominal allocation and an exposure metric.

## Backtest requirements

Every ETF parameter test should include:

- total return
- annualized return
- maximum drawdown
- volatility
- Sharpe / Sortino
- worst day
- longest drawdown
- number of trades
- turnover
- percentage of time in cash
- exposure by ETF
- performance by volatility regime
- sensitivity to small parameter changes

The test must include transaction costs and a conservative execution assumption.

## Out-of-sample discipline

Do not select the final moving-average or VIX threshold solely because it maximizes historical return.

Use a development period to identify candidate rules and a separate holdout period to evaluate whether the behavior survives unseen data. Walk-forward testing should be considered for any parameter that materially changes performance.

## Current status

The following are **working hypotheses only**:

- 200-day moving average
- one-week confirmation before re-entry
- VIX around 28 as a possible defensive trigger
- 25% allocation per ETF slot

No threshold is frozen until tested.

## References

The project should add primary fund-provider documentation for each leveraged ETF before implementation, including daily leverage objective, reset mechanics and stated risks. These facts should be captured from the issuer rather than inferred from ticker names.
