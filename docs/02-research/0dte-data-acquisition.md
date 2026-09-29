# 0DTE Intraday Data Acquisition and Backtesting Gate

**Status:** Research specification — 2026-09-28

## 1. Purpose

The project's existing daily options dataset is insufficient for validating intraday 0DTE entry, profit-target, stop-loss, time-exit, or path-dependent management rules. The project must not infer the intraday path between daily observations.

This document establishes the data-quality gate and the independent validation plan for the 0DTE research track.

## 2. What the public evidence establishes

The current tastytrade developer backtester is a historical options backtesting service. It accepts an underlying, date range, option legs, entry conditions, and exit conditions, and returns simulated trials, snapshots, and execution logs. The public API also exposes a `simulate-trade` operation that returns a time-ordered series containing timestamp, simulated trade price/effect, underlying price, and delta.

The public API documentation does not establish that the retail backtester exposes the same intraday 0DTE research dataset or sampling methodology used in every tastylive research study. Therefore the project must not claim that tastytrade's public API is identical to tastylive's internal research dataset.

The important finding is that historical intraday option data is commercially available independently. Cboe DataShop offers 1-minute or custom N-minute historical option quote intervals based on OPRA data, including NBBO bid/ask, sizes, OHLC, volume, and underlying bid/ask; optional calculations include IV and Greeks. This is sufficient in principle to construct an independent intraday replay dataset.

Option Alpha publicly states that its 0DTE/1DTE backtester uses 1-minute historical options data and supports up to three years of testing. This is useful as an independent benchmark/reference platform, not as proof of any strategy's profitability.

## 3. Required data resolution

### Minimum credible resolution

10-minute observations are acceptable for reproducing research that explicitly uses 10-minute sampling.

### Preferred resolution

1-minute NBBO observations are the project standard for the first production-quality 0DTE research engine.

### Highest-rigor validation

Tick/quote replay may be used for targeted validation of cases where 1-minute sampling could materially change the result, especially stop/touch events and rapidly changing 0DTE spreads.

The project will not require tick data for every historical run unless 1-minute validation reveals material path sensitivity.

## 4. Required fields

At minimum:

- timestamp
- underlying symbol
- underlying price or NBBO
- option root
- expiration
- strike
- call/put
- bid
- ask
- bid size
- ask size
- trade volume

Preferred:

- implied volatility
- delta
- gamma
- theta
- vega
- open interest

The engine must preserve the original quote rather than storing only a derived midpoint.

## 5. Execution-price policy

For every simulated option leg, retain:

- bid
- ask
- midpoint
- selected fill assumption
- spread width
- timestamp

The research suite must test at least:

1. midpoint;
2. conservative executable-side pricing;
3. midpoint plus explicit slippage;
4. sensitivity to bid/ask spread.

A strategy that only works at midpoint while failing conservative fills is not considered execution-robust.

## 6. 0DTE replay model

The engine must operate on timestamped observations.

For each candidate:

1. Identify the eligible expiration.
2. Determine the underlying state at the entry timestamp.
3. Select strikes using the frozen strategy rule.
4. Verify the actual historical option quotes existed at that timestamp.
5. Construct the multi-leg position.
6. Calculate the fill using the configured pricing model.
7. Advance through subsequent observations.
8. Evaluate every deterministic exit condition at each observation.
9. Close using the historical quote available at the exit timestamp.
10. If no earlier exit occurs, settle/close according to the structure's expiration rule.
11. Record all decisions, skipped opportunities, fills, and exit causes.

No interpolation across unavailable observations is permitted for stop/touch detection.

## 7. Research validation gate

Before using the engine to evaluate OPTIONS-001/0DTE variants:

### Gate A — data integrity

Verify:

- timestamps are correctly timezone-normalized;
- expiration dates are correct;
- same-day expirations are correctly identified;
- option contracts are not duplicated;
- crossed/inverted quotes are handled explicitly;
- missing quotes are represented as missing;
- zero/invalid quotes are not silently converted into valid prices.

### Gate B — deterministic replay

Given the same source data and strategy configuration, repeated runs must produce identical trades and P/L.

### Gate C — known-study reproduction

Attempt to reproduce at least one publicly documented tastylive-style 0DTE study using the same general sampling, entry, exit, and pricing conventions where the source provides enough information.

The objective is not to force numerical equality. Differences must be explained by dataset, symbol, date range, fill assumptions, or undocumented methodology.

### Gate D — resolution sensitivity

Run selected strategies using:

- 10-minute data;
- 1-minute data.

Compare trade count, exit timing, P/L, drawdown, and especially stop/touch events.

If conclusions materially change, 10-minute data cannot be treated as sufficient for that strategy.

### Gate E — out-of-sample validation

Freeze rules before running the final held-out period. Do not tune entry times, deltas, profit targets, or filters on the held-out sample.

## 8. Data-source hierarchy

1. Primary historical exchange/OPRA-derived data with documented quote semantics.
2. A reputable historical options-data vendor with timestamped NBBO.
3. Broker/vendor backtester as an independent cross-check.
4. Published tastylive results as external validation targets.

Published results are evidence for methodology and comparison, not raw data.

## 9. Current candidate sources

### Cboe DataShop

Cboe currently advertises 1-minute and custom N-minute option quote intervals derived from OPRA, with NBBO fields and optional Greeks. This is the preferred source candidate for an independent research dataset.

### Option Alpha

Option Alpha publicly advertises three years of 1-minute historical options data for its 0DTE/1DTE backtester. It is a strong independent benchmark candidate and may be substantially easier to use than assembling raw historical files.

### tastytrade

The current public backtesting API is useful for independent trade-level/backtest cross-checks. Its `simulate-trade` endpoint returns time-ordered historical price points for specified legs, and its backtester provides aggregate results and execution logs. The public documentation does not establish that it provides the exact 1-minute/10-minute raw dataset used by tastylive research.

## 10. No-data shortcut

If a sufficiently granular dataset cannot be acquired, the project must leave the 0DTE profitability result as **UNVALIDATED**.

It must not:

- interpolate between daily observations;
- assume a stop was or was not touched;
- assume an intraday profit target was reached;
- manufacture a 0DTE path from OHLC alone;
- report a simulated 0DTE CAGR/P/L as historical evidence.

## 11. Current decision

The project will continue daily ETF and multi-day options research using the existing validated data.

The 0DTE research track is now explicitly a **data acquisition + replay-engine validation task**, not a missing-analysis task.

The first serious implementation target is a 1-minute historical NBBO replay engine, with 10-minute aggregation available for comparison and study reproduction.

## 12. Relationship to autonomous trading

The 0DTE engine is research infrastructure only.

It does not authorize live 0DTE trading. Before any autonomous 0DTE operation, the strategy must separately pass:

- economic validation;
- account feasibility;
- realistic execution/fill validation;
- walk-forward/held-out testing;
- broker capability validation;
- expiration/settlement testing;
- restart/reconciliation testing;
- operational paper soak testing.

