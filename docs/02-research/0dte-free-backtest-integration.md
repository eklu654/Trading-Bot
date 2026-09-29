# 0DTE Free Backtest Integration

**Date:** 2026-09-29  
**Status:** Ready for external free-platform validation

## Primary free platform discovered

0DTESPX.com documents a free registered account that provides full historical SPX 0DTE market data at 1-second resolution, historical sessions, strategy backtesting, a strategy builder, portfolios, paper trading, and an API. Its documentation states that there is no paid tier and no payment is required.

The platform also states that the historical option chain can be reconstructed at any moment of any historical session and that its backtests run over the full trading history. This directly solves the main data-resolution problem for SPX 0DTE research without purchasing a dataset.

## Important usage constraint

The platform's acceptable-use rules prohibit bulk extraction of the historical dataset. Therefore the project must **not** attempt to download every second of every contract and create a local copy.

Instead, use the platform as an external deterministic research engine:

1. encode a frozen strategy;
2. run its backtest;
3. collect the aggregate results and permitted session/trade diagnostics;
4. reproduce the same strategy in our own engine where our available data permits;
5. compare results;
6. use discrepancies to identify modeling or execution assumptions.

This is both legally cleaner and methodologically useful.

## Why this is better than our original plan

The original blocker was lack of free historical intraday option quotes. The platform removes that blocker for SPX 0DTE research while preserving the distinction between the platform's backtest and our own independent replay.

It supports:

- 1-second historical market data;
- SPX/SPXW 0DTE chains;
- bid/ask and Greeks;
- delta-based strike selection;
- expected-move selection;
- fixed entry windows;
- profit targets;
- stop losses;
- time exits;
- defined-risk multi-leg structures;
- buying-power/margin simulation;
- fees and slippage settings;
- full-history strategy results;
- paper replay.

## First benchmark suite

Use frozen, simple strategies before attempting any AI/regime optimization.

### Test group A — 0DTE verticals

- 16Δ short put + fixed-width long put
- 20Δ short put + fixed-width long put
- 25Δ short put + fixed-width long put
- matching call versions
- entries at 09:35, 09:45, and 10:00 ET
- exits at 10%, 25%, 50% profit and 16:00 ET
- no discretionary defense.

### Test group B — iron condors

- 16Δ/16Δ
- 20Δ/20Δ
- 25Δ/25Δ
- fixed wings and expected-move wings
- 09:35/09:45/10:00 ET entries
- 10%/25%/50% profit targets
- 16:00 ET time exit.

### Test group C — iron butterflies

- ATM short strike;
- fixed-width wings;
- 09:35/09:45/10:00 ET entries;
- 10%/25%/50% profit targets;
- 16:00 ET exit.

### Test group D — butterflies

- expected-move centered;
- fixed-width;
- multiple wing widths;
- 10%/25%/50% profit targets;
- expiration settlement.

### Test group E — short strangle control

- include only as a research control;
- never treat its historical return as sufficient evidence for deployment;
- compare its capital requirement and tail loss against defined-risk alternatives.

## Tasty-style timing tests

tastylive has published research comparing early-session and late-session 0DTE short-premium behavior. One published study examined the first 90 minutes versus the last 30 minutes and reported materially different behavior, including a warning about initiating short premium with only 30 minutes remaining.

Therefore timing is a first-class test dimension rather than a parameter to optimize after seeing results.

Test:

- 09:30–09:35;
- 09:35–09:40;
- 09:45–09:50;
- 10:00–10:05;
- 90-minute hold/management window;
- 12:00 ET;
- 14:00 ET;
- last 60 minutes;
- last 30 minutes.

## Profit-target tests

tastylive has published 0DTE research discussing 10%, 25%, and 50% profit targets at different times. These should be treated as independent hypotheses, not as a reason to pick the target that produces the highest historical result.

Every target must be tested across the same chronological train/validation/holdout framework.

## Cost and execution tests

Every candidate should be run under at least:

- platform default fee schedule;
- conservative fee schedule;
- added slippage;
- worse-than-mid entry;
- worse-than-mid exit;
- no profit target / hold to close;
- explicit max-loss or time exit where supported.

## Regime segmentation

Every surviving candidate must be broken down by:

- VIX level;
- VIX change;
- expected move;
- opening gap;
- trend state;
- weekday;
- major event day where identifiable;
- high-volatility versus low-volatility sessions.

Do not allow the regime model to choose the best bucket on the same data used to claim performance. Regime selection must be trained only on prior data and evaluated chronologically out of sample.

## Independent project test

The platform result is an external benchmark. Our own Trading-Bot implementation must still enforce:

- account NLV;
- maximum risk;
- aggregate BPR;
- beta-weighted Delta;
- concentration;
- stale-data behavior;
- duplicate-order prevention;
- fill uncertainty;
- restart recovery;
- broker reconciliation.

An external backtest cannot override these gates.

## Current blocker

The only remaining external dependency is account access to the free platform. Historical arbitrary-date access requires a free registered account. No payment is required according to the platform documentation.

Once a free account is available, the benchmark suite can be run without purchasing historical data.