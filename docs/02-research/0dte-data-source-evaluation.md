# 0DTE Data-Source Evaluation

**Date:** 2026-09-28

## Current conclusion

The project does not need to purchase a massive historical archive immediately.

Three credible external paths now exist:

1. **ORATS Intraday Backtester** — easiest immediate independent benchmark; one-minute 0DTE backtesting is exposed as a service.
2. **Option Alpha 0DTE Backtester** — another independent one-minute backtesting benchmark with up to three years of historical data.
3. **Raw Cboe/OPRA-derived data** — strongest long-term choice for complete control of the replay engine, but requires purchasing and managing historical data.

## ORATS

ORATS currently advertises a one-minute intraday backtester with 0DTE support, exact clock-time entries/exits, per-minute stop/profit-target evaluation, and history back to October 2020. Its current individual Trading Tools subscription is advertised at $99/month.

ORATS also sells a one-minute historical data archive from August 2020 onward. The advertised individual historical backfill is $1,500 and the full archive is very large, so purchasing the raw archive is not the preferred first step.

The ORATS intraday backtester is therefore a strong **external benchmark** before buying raw data.

Important limitation: ORATS uses its own Smoothed Market Values methodology and data processing. Its results should not be treated as ground truth or assumed identical to tastylive/Cboe marks.

## Option Alpha

Option Alpha currently advertises a 0DTE/1DTE backtester using one-minute historical options data, with up to three years of testing and detailed trade logs. It supports multiple 0DTE structures including verticals, iron condors, iron butterflies, and related structures.

This is another useful independent benchmark.

Important limitation: its historical dataset and fill methodology are proprietary to the platform, so it is a validation reference rather than the canonical dataset for our own engine.

## Cboe DataShop

Cboe currently offers one-minute or custom N-minute historical option quote intervals derived from OPRA, including NBBO bid/ask and sizes, OHLC, volume, and optional Greeks. Historical availability begins in January 2012.

This is the strongest candidate for the project's eventual canonical data source because it exposes the underlying quote observations rather than only a finished backtest result.

For SPX specifically, Cboe notes that historical full-market purchases do not include underlying bid/ask by default, although a complimentary run can be requested for SPX/OEX underlying bid/ask. The project can also use a separately sourced SPX underlying series if necessary.

## tastytrade

The current public tastytrade backtesting API can independently simulate historical option trades and return time-ordered price points, underlying price, and delta. Its full backtester also returns trials, snapshots, and step-by-step logs.

This is useful for **cross-checking individual historical trades and longer-duration strategy behavior**.

The public API documentation does not establish that its retail backtester exposes the exact minute-level dataset or methodology used in every tastylive 0DTE study. Therefore it should not be treated as the canonical raw 0DTE dataset.

## Recommended acquisition sequence

### Stage 1 — no purchase

Freeze our 0DTE rules and build the replay interface/schema.

### Stage 2 — external benchmark

Use ORATS and/or Option Alpha to run a small set of deliberately simple 0DTE strategies:

- SPY/SPX short put spread
- short call spread
- iron condor
- iron butterfly
- short strangle as a control

Use fixed entry time, fixed delta/width, and simple exits.

Record the external results but do not optimize against them.

### Stage 3 — our own replay engine

Acquire a targeted historical sample rather than the entire market archive.

The first target should be enough SPY/SPX history to cover:

- low-volatility trend;
- sideways/chop;
- volatility expansion;
- major selloffs;
- post-shock normalization;
- multiple expiration regimes.

A targeted sample can validate the engine before a larger archive is purchased.

### Stage 4 — reproduce external results approximately

Run the same rules against our data.

Differences should be investigated through:

- data timestamp;
- quote construction;
- strike selection;
- missing contracts;
- fill model;
- commissions;
- slippage;
- expiration handling.

### Stage 5 — full research

Only after the replay engine passes the cross-validation gate should we run the full OPTIONS-001/0DTE research matrix.

## Why this is preferable

The project's objective is not to obtain the largest dataset possible.

The objective is to establish a reproducible, auditable chain:

**raw historical observations → deterministic replay → independently cross-checked results → held-out validation → paper trading**

That is more valuable than a large backtest number from an opaque platform.

## Current recommendation

Do **not** buy the $1,500 ORATS raw archive yet.

The highest-value next experiment is to use a one-minute commercial backtester as an independent reference, while designing our own engine so it can later ingest Cboe/OPRA-derived data.

If the external benchmark and our eventual replay disagree materially, stop and resolve the discrepancy before trusting either result.
