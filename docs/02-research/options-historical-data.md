# Historical Options Replay Data Acquisition

**Status:** Research implementation specification  
**Last reviewed:** 2026-09-28

## 1. Objective

OPTIONS-001 cannot be validated from underlying-price and VIX data alone. The next backtest requires historical option-chain observations so that entries, fills, exits, credit received, defensive adjustments, and contract feasibility can be reconstructed.

The first replay source will be the public SPY end-of-day historical options dataset covering 2008–2025.

## 2. Primary research dataset

Candidate source:

- Repository: anahatsingh-ui/options-dataset-hist
- Coverage: SPY 2008–2025
- Observation: 4:00 PM ET daily chain
- Format: yearly Parquet files
- Size: approximately 24.7 million SPY contract-day rows
- Fields include bid, ask, mark, volume, open interest, IV, delta, gamma, theta, vega, rho, strike, expiration, option type, and underlying price.

The repository describes the dataset as a preservation mirror of the MIT-licensed dataset originally published by Philipp Dubach.

The project will not commit the raw option dataset to Trading-Bot. It is too large and is external market data.

## 3. Required replay fields

At minimum:

- observation date
- underlying symbol
- underlying price
- expiration
- strike
- call/put
- bid
- ask
- mark
- volume
- open interest
- implied volatility
- delta
- gamma
- theta
- vega

The replay engine should preserve the raw source values and record the source/version hash in every generated research report.

## 4. Initial replay universe

The first complete replay target is:

- underlying: SPY
- structure: short strangle
- entry target: approximately 45 DTE
- short strike selection: approximately 16 delta on each side
- winner management: close at 50% of initial credit or 21 DTE, whichever occurs first
- loss-management benchmark: 2x initial credit for undefined-risk positions
- defensive-management variants: close, roll untested side, roll out, and inversion where the historical chain makes the action reconstructible.

The 45-DTE/16-delta values are experimental project baselines, not universal rules.

## 5. Execution assumptions

The first replay must test at least two fill models:

### Conservative

- opening short legs: bid
- closing long legs: ask

### Midpoint sensitivity

- opening and closing: mark/mid

A result should not be accepted as robust if it only works under an unrealistically favorable fill assumption.

Transaction costs and any available liquidity constraints must be explicit.

## 6. Regime gating

The replay must use only information available at the entry date.

Initial candidate gates:

1. current classifier — retained only as a diagnostic baseline;
2. stricter volatility candidate;
3. broader sideways candidate;
4. turbulent-only candidate.

No candidate is currently frozen as SWITCH-001.

The historical research already shows that the current classifier marks approximately 91.6% of sessions as options-eligible, which is inconsistent with the project's intended ETF-default architecture.

## 7. Account-feasibility model

The first account case is $2,000.

The replay must separately record:

- theoretical position size;
- actual one-contract economics;
- NLV sizing constraint;
- per-underlying concentration;
- estimated buying-power requirement where a broker-specific formula is available;
- rejected-entry reason;
- simultaneous-position count.

The historical tastytrade/tastylive framework must not be silently altered to make a contract fit the account.

## 8. Important limitation

End-of-day chain data is sufficient for a daily management approximation, but it does not reproduce intraday execution.

Therefore the first replay is a daily historical reconstruction, not a tick-perfect execution simulation.

For any trade whose management depends on an intraday breach, the engine must label the event as ambiguous unless the source provides sufficient intraday data.

## 9. Data-quality checks

Before any P/L result is accepted:

- verify unique (date, expiration, strike, type) keys;
- verify bid <= ask where both exist;
- reject negative prices;
- identify zero-bid/zero-ask contracts;
- identify stale or zero-volume contracts;
- verify expiration ordering;
- verify DTE calculations;
- compare underlying prices with the project's market dataset;
- check for missing observation dates;
- preserve source hash/version.

## 10. Cboe reference source

If the public dataset proves insufficient, Cboe DataShop provides historical Option EOD Summary and Option Quotes products with bid/ask, OHLC, volume, open interest and optional IV/Greeks. Cboe states that its historical options datasets extend to at least January 2012 for these products.

Cboe should be treated as the higher-fidelity reference source, but it is not required for the first research pass if the public dataset passes the quality checks.

## 11. Acceptance gate

OPTIONS-001 historical replay will not be considered validated until:

1. trade selection is reproducible;
2. no look-ahead bias is present;
3. both fill models are tested;
4. structure-specific exits are deterministic;
5. defense variants are separately measured;
6. $2,000 feasibility is reported independently from raw strategy P/L;
7. results are split chronologically into development, validation, and holdout periods;
8. the same rules survive the holdout without being re-tuned to it.

## Sources

- Public historical dataset: anahatsingh-ui/options-dataset-hist
- Cboe DataShop Option EOD Summary
- Cboe DataShop Option Quotes
