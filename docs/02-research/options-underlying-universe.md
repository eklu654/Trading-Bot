# Options Underlying-Universe Research

**Status:** Research specification — not production-frozen  
**Last reviewed:** 2026-09-28

## 1. Research finding

The project should not begin with an unrestricted list of thousands of optionable stocks.

Official tastylive material emphasizes maintaining a watchlist, monitoring liquidity and bid/ask spreads, and using highly liquid market products as reference points. It also repeatedly distinguishes expensive/high-capital products from lower-priced products that are more practical for smaller accounts.

The underlying universe therefore needs explicit eligibility rules rather than a fixed ticker list alone.

## 2. Evidence relevant to the $2,000 account

Current tastylive research identifies four practical small-account constraints:

- underlying price;
- capital allocation / position count;
- strategy type;
- premium available relative to capital and transaction costs.

Their June 2025 small-account research notes that expensive underlyings can consume a large percentage of a small account when traded naked, while cheaper underlyings may improve premium-to-BPR efficiency. It also warns that lower-priced stocks can have poor liquidity.

A separate 2025 article specifically describes IWM as useful for defined-risk premium selling because of its relatively high IV and diversified underlying exposure.

A 2024 S&P-500 product comparison identifies SPY as having exceptionally high options volume and tight bid/ask spreads, while noting that larger products such as SPX and /ES generally require more capital unless risk is explicitly defined.

## 3. Initial universe architecture

Instead of hard-coding a permanent ticker list, implement three layers.

### Layer A — Core liquid index/ETF universe

Initial research candidates:

- SPY
- QQQ
- IWM
- DIA
- GLD
- TLT
- SLV
- sector ETFs with sufficiently liquid options

These are research candidates, not an approved production list.

### Layer B — Additional liquid ETFs

Candidates are admitted only if they satisfy the quantitative liquidity filters below.

Examples may include:

- GDX
- GDXJ
- XLU
- other broad/sector/commodity ETFs

The system should discover these from market data rather than treating this list as permanently authoritative.

### Layer C — Individual equities

Individual stocks should initially be permitted only after the underlying passes stricter liquidity and event-risk filters.

This is particularly important because individual equities introduce earnings and company-specific event risk that diversified ETFs do not.

The system should initially treat earnings proximity as a separate eligibility constraint.

## 4. Required quantitative eligibility filters

Every candidate underlying must satisfy configurable thresholds for:

### Options liquidity

- minimum option volume;
- minimum open interest;
- maximum bid/ask spread in absolute dollars;
- maximum bid/ask spread as percentage of mid;
- minimum quote quality;
- minimum number of strikes around the target delta.

### Underlying liquidity

- minimum average daily volume;
- minimum dollar volume;
- maximum percentage spread.

### Capital efficiency

Calculate BPR divided by NLV and premium divided by BPR for each candidate structure.

A candidate that technically passes liquidity but consumes disproportionate BPR should be rejected.

### Event risk

For equities:

- earnings date;
- ex-dividend date;
- corporate actions;
- special distributions.

Event-risk rules must be structure-specific.

## 5. Diversification rules

Ticker count must not be treated as diversification by itself.

The risk engine must aggregate:

- beta-weighted Delta;
- sector exposure;
- underlying correlation;
- implied-volatility correlation where data permits;
- BPR concentration;
- notional exposure.

SPY, QQQ and IWM should therefore be treated as related equity-beta exposures rather than three automatically independent positions.

## 6. Initial research universe

The first backtest should use a deliberately small universe:

**SPY, QQQ, IWM, GLD, TLT, SLV**

Why this set?

- It has substantial historical research precedent in tastylive material.
- It provides equity-index, bond and precious-metal exposures.
- It avoids immediately introducing hundreds of individual-company event risks.
- It allows the project to test whether diversification survives correlation aggregation.

This is a **research universe**, not a recommendation or production whitelist.

## 7. Small-account experiment

Run the same strategy across:

- core six-underlying universe;
- expanded liquid-ETF universe;
- liquid-equity universe.

Compare:

- opportunity count;
- rejected trades;
- average bid/ask cost;
- BPR;
- premium/BPR;
- correlation concentration;
- event-risk exclusions;
- drawdown;
- tail loss;
- portfolio diversification.

The purpose is to determine whether expanding the universe improves actual diversification or merely adds symbols representing the same equity-beta risk.

## 8. Important historical evidence

tastylive's 2021 research comparing SPY, IWM and QQQ strangles found that a combined portfolio reduced risk in that particular study while maintaining average gains. This is useful evidence that multiple underlyings can affect portfolio behavior differently from their individual trades.

However, separate 2024 research found very high long-term price correlation among major equity indexes. The project should therefore test portfolio-level correlation rather than assuming ticker diversification.

## 9. Current implementation stance

Do not freeze the six-underlying list as a permanent production universe.

Instead:

1. use the six symbols for initial research;
2. implement quantitative eligibility filters;
3. measure liquidity and capital efficiency;
4. measure correlation and concentration;
5. expand the universe only when data demonstrates a benefit;
6. keep individual-equity event risk separate from ETF/index risk.

## 10. Unresolved questions

- Exact liquidity thresholds.
- Exact earnings/event exclusion window.
- Whether dividends require early-assignment restrictions.
- Whether GLD/SLV/GDX should be grouped as one precious-metals risk bucket.
- Whether TLT deserves a separate macro-rate risk bucket.
- Exact correlation lookback and threshold.
- Whether futures options should ever enter OPTIONS-001.
- Whether $2,000 makes even the core universe too restrictive for undefined-risk positions.

## Sources

- tastylive, “Options Watchlist”
- tastylive, “How to Trade with a $10,000 Account”
- tastylive, “How to Manage Buying Power Risk in Small Option Accounts”
- tastylive, “Why IWM Is My Go-To ETF for Selling Defined Risk Options”
- tastylive, “Four Ways to Trade the S&P 500”
- tastylive, “Managing Strangles in Something Other Than SPY”
- tastylive, “Strangles Across Indices”
