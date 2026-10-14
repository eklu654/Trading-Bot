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


## Second candidate screened: HistoricalOptionData.com / DeltaNeutral LLC

Its public documentation says its end-of-day records come from OPRA/NBBO and include bid, ask, expiration, strike, and quote date. It advertises monthly/yearly archive files going back to 2002 and an SPY-specific archive beginning in 2005. Published product pages list the SPY archive at $455 and the full-market 2002-present Level 1 archive at $1,150; these prices are not a quote for the minimum data needed here.

- Overview / stated OPRA provenance: https://historicaloptiondata.com/overview-of-our-historical-option-prices-data/
- SPY-specific and full-market product list: https://historicaloptiondata.com/product-category/level-2-csv-option-data-including-greeks-stocks-and-option-statistics/
- File structure: https://historicaloptiondata.com/data-structure/

This may be a better targeted inquiry than buying HistoricalData.net's full archive because it explicitly describes OPRA NBBO as the data source and offers an SPY-specific product. Still ask for exact contract coverage, a minimum-scope price, and a sample row before paying. Public documentation does not prove the two flagged contract histories are present or that missing/zero-bid rows are retained. No purchase or contact has occurred.


### Preferred low-cost route: ONESYMBOL monthly archive

HistoricalOptionData.com also publishes an ONESYMBOL order assistant for selected symbols/date ranges. Its public pricing formula is **$4.95 × (symbol-months)^0.846**, with a partial month counted as a full month. For full contract-lifecycle coverage, a rough planning count is 9 SPY months (January–September 2008) plus 11 QQQ months (November 2013–September 2014), or 20 symbol-months. Applying the posted formula gives an indicative estimate of **$62.41**, before any special-order/labor charges or changes in actual coverage/pricing. This is not a quote and does not confirm that either contract's rows are present.

- ONESYMBOL order assistant: https://preorder.dnfilevault.com/
- Public pricing explanation: https://historicaloptiondata.com/product-category/level-1-bare-bones-data/

Request a quote/coverage confirmation first. If the provider can supply the two exact contracts for the relevant periods at close to this price, that is preferable to buying a $455 SPY-specific archive or a $1,150 full-market archive. Keep all quote rows from the first available contract observation through nominal expiration so absent rows can be distinguished from rows with blank/zero bids.


## Third candidate screened: OptionsDX (potentially low-cost QQQ-only cross-check)

OptionsDX publicly lists QQQ EOD option-chain files for 2014 and shows a displayed product range of $0–$20; files are monthly CSVs with bid/ask/last and underlying price. Its SPY archive starts in 2010, so it cannot cover the flagged 2008 SPY contract. Public product pages:

- https://www.optionsdx.com/product/qqq-option-chains/
- https://www.optionsdx.com/product/spy-option-chains/
- https://www.optionsdx.com/faq/

This is a possible low-cost QQQ cross-check, but the selected 2014 EOD variation's actual price, exact contract presence, handling of absent/zero-bid rows, and source provenance have not been confirmed. Do not treat the dataset as independent market-data validation until provenance is clarified. No account was created, no checkout was submitted, and no data was purchased or downloaded.


## Additional QQQ price-basis verification request

Please confirm that historical QQQ option bid/ask values are raw, as-traded premiums and that strike values are the original listed strike, not dividend-adjusted or otherwise rescaled. For `QQQ140920C00077000` on 2014-03-11, the preserved dataset reports bid $6.70 / ask $7.67; public QQQ unadjusted close is $90.22, making the standard $77 call's intrinsic value $13.22. The source's separate adjusted close is $82.135, which would make the quote appear above intrinsic if incorrectly compared against the raw strike. The provider should confirm the correct contemporaneous underlying close, contract deliverable/strike, and NBBO bid/ask basis for both 2013-12-23 and 2014-03-11.

This is a targeted data-integrity check in addition to confirming the missing post-2014-03-12 contract rows. No price adjustment should be assumed from the request alone.
