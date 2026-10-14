# Independent LEAPS Quote-History Coverage Request

**Purpose:** Resolve two missing-exit-quote cases before accepting any LEAPS replay return. This is a coverage inquiry only; do not purchase or subscribe until the provider confirms the exact records are available.

## Request to provider

Subject: Historical end-of-day quote coverage for two expired ETF call contracts

Hello,

I am validating a historical options backtest and need to establish whether your archive contains complete end-of-day bid/ask observations for these exact contracts, including dates on which one or both quote sides may be blank or zero:

1. **SPY 2008-09-30 call, strike $148** — OSI-style symbol `SPY080930C00148000`. Please confirm coverage from the first listed observation through expiration, especially 2008-08-11 through 2008-09-30.
2. **QQQ 2014-09-20 call, strike $77** — OSI-style symbol `QQQ140920C00077000`. Please confirm coverage from the first listed observation through expiration, especially 2014-03-11 onward through the contract's final trading/expiration date. Please confirm the exact expiration and last-trading-date convention represented by your symbol.

For each contract, could you confirm:

- Whether the exact contract is present and the date range of available rows.
- Whether the archive retains a row when a contract has no positive bid, a blank bid, or no quote; distinguish a missing row from a present row with a missing/zero bid.
- Whether bid and ask are end-of-day standing quotes, last trades, midpoint marks, or another measure; include any available quote timestamp and bid/ask sizes.
- Whether contract symbols, expiration dates, strikes, and multipliers follow standard OSI conventions, and how adjusted/nonstandard contracts are represented.
- The smallest product/license that includes these dates, the total cost, and whether a sample or limited paid extract can be checked before purchasing a full archive.

I only need these two contract histories for the first validation pass. Please do not interpret a blank/zero bid as proof that an executable sale was impossible; I am comparing the recorded quote histories and will separately document execution assumptions.

Thank you.

## Acceptance checklist

Do not classify a source as a successful independent check until all are true:

- [ ] Provider confirms both exact contract histories and date ranges in writing.
- [ ] Source provenance is distinguishable from the preserved `data-v1` mirror; it is not merely another copy of the same upstream dataset.
- [ ] Raw rows include contract identifier, quote date, expiration, strike, call/put, bid, ask, and preferably sizes/timestamps.
- [ ] Original files are retained with retrieval date, provider/version, license notes, and SHA-256 hashes.
- [ ] Comparison reports missing rows separately from present rows with blank/zero bids, and reports exact quote disagreements.
- [ ] Any observed quote is treated as market-data evidence, not automatic proof that a hypothetical order would have filled.

## Current candidate screened

HistoricalData.net documents an end-of-day US options archive beginning in February 2002 and lists a full archive at $590 one-time. Its public options coverage lookup only verifies a latest-session snapshot; it does not establish historical coverage for these contracts. Do not purchase the full archive until the provider confirms the exact contract/date coverage. See:

- https://historicaldata.net/options.html
- https://historicaldata.net/options/SPY.html
- https://historicaldata.net/api.html

**Current status:** coverage not confirmed; no external dataset downloaded; no purchase authorized or made.
