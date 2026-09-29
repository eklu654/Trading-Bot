# 0DTE Free-Only Data Plan

**Status:** Active research plan  
**Date:** 2026-09-29  
**Constraint:** No paid historical datasets or subscriptions.

## Decision

The project will not purchase Cboe DataShop, ORATS, TickData, Historical Option Data, ThetaData, or similar historical options datasets for 0DTE research.

A paid 1-minute options dataset would improve replay fidelity, but it is not required to continue the research program.

## What free sources can and cannot provide

### 1. Public/open-source historical research

Public GitHub projects can provide reproducible strategy code, published trade logs, published entry/exit rules, historical benchmark results, and occasionally small sample datasets.

They generally do **not** provide a complete OPRA-quality historical option quote stream.

A useful example is the public SPX_0DTE_Options_Selling_Public project. Its repository includes code and a historical trades.csv covering a 0DTE credit-spread strategy. The project documents a 9:45 AM ET entry, VIX1D expected-move strike selection, $5 wings, and expiration settlement. Its published trade log can serve as an independent benchmark/control, but it is not raw quote data and must not be treated as such.

### 2. HistoricalData.net free sample

HistoricalData.net publishes a free sample containing real options CSV data. This is useful for validating parsers, contract identifiers, field mappings, and EOD-chain handling.

The sample is **not sufficient for full 0DTE intraday replay** because it does not provide the historical minute-by-minute option quote path needed for arbitrary intraday stops/targets.

### 3. Cboe public delayed data

Cboe provides public delayed quote interfaces and historical volume/statistics pages. These are useful for current/forward data collection and validation, but the detailed historical 1-minute option-quote product is a commercial DataShop product.

The project must not scrape Cboe delayed quote tables in violation of Cboe's stated restrictions.

### 4. Free commercial trials

A service may offer a genuinely free trial with 1-minute historical options data. A trial may be used for a bounded external benchmark if it requires no payment and the terms permit the intended research use.

A trial is **not** treated as a durable project data source. We will not design the system around continued access to a paid service.

## Free-only test hierarchy

The research engine will use the strongest free evidence available in this order:

1. **Raw free intraday option data** if a legitimate public source is found.
2. **Public reproducible 0DTE trade logs + source code** for independent benchmark replication.
3. **Historical EOD option chains + intraday underlying data** for expiry-only strategies.
4. **Synthetic option-pricing replay** for parameter sensitivity and robustness analysis when observed entry quotes are unavailable.
5. **Forward paper-data collection** using public/delayed sources to accumulate a real intraday dataset for future validation.

## Critical distinction: expiry-only vs path-dependent strategies

A 0DTE strategy that enters once and holds to expiration does not require the complete option price path after entry.

For such a strategy we can validly test entry-time strike selection, expiration payoff, maximum defined loss, win/loss frequency, sensitivity to entry premium, VIX/VIX1D regime, underlying intraday high/low containment, and account feasibility.

However, if the strategy contains intraday profit targets, stop losses, touch exits, rolling, dynamic defense, or time-based exits before expiration, an observed intraday option path is required for a high-fidelity historical replay.

We must never infer that a stop or target was hit merely because the daily high/low crossed a derived level.

## Synthetic replay rules

If observed historical option quotes are unavailable, synthetic replay may be used only as a **model study**, never as an observed-market backtest.

The synthetic engine must use only information available at simulated entry; model option value from explicit assumptions; vary IV, spread, slippage, and entry premium; report assumptions alongside every result; perform pessimistic, base, and optimistic scenarios; never label synthetic P/L as historical realized P/L; and never use synthetic results as the sole deployment gate.

## Forward collection

Because the project is intended to become autonomous, we can also collect real intraday 0DTE observations prospectively.

The collector should record, where legally and legitimately available: timestamp, underlying price, option contract, expiration, strike, call/put, bid/ask, bid/ask size, last trade, volume, implied volatility, Greeks, VIX/VIX1D, and session state.

The collector must be append-only, timestamped, restart-safe, and checksum/audit friendly.

This creates a genuine project-owned historical dataset without purchasing a historical archive. It cannot retroactively solve the missing past data, so it is a supplementary validation path.

## No-data fallback

If no legitimate free historical intraday option dataset can be obtained, the project will **not stop**.

Instead:

1. finish all non-0DTE ETF and multi-day options research;
2. independently reproduce public 0DTE studies using their published trade logs/results where possible;
3. test expiry-only defined-risk 0DTE structures using observed or conservatively modeled entry economics;
4. run synthetic sensitivity analysis across premium, IV, slippage, and loss assumptions;
5. collect real intraday data prospectively;
6. hold 0DTE-specific deployment authorization closed until observed intraday validation exists.

This preserves research progress without pretending synthetic or daily data is equivalent to minute-level option quotes.

## Research integrity rule

**No paid data means no downgrade in evidentiary standards.**

The project may use less precise tests, but it must label them correctly and retain the distinction between observed historical replay, independently published benchmark, synthetic model study, and prospective paper-data validation.

Only the first category can support the strongest historical claims about path-dependent 0DTE execution.