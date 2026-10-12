# Adaptive LEAPS + Short-Call Overlay Research

**Status:** Specification / data-feasibility gate; no strategy result or candidate promotion  
**Opened:** 2026-10-12  
**Scope:** Independent options strategy research. This track is separate from ETF-001, B0, F75, OPTIONS-001, and OPTIONS-002.  
**Underlyings:** QQQ and SPY, tested separately with identical rules where contract mechanics permit.  
**Starting-account reference:** $5,000, with feasibility reported separately from theoretical one-contract economics.

## 1. Research question

Can a long-dated call combined with a conditionally activated, repeatedly managed short-call overlay improve total ending equity versus simply holding the long call, while retaining enough upside participation and avoiding catastrophic option-position/account outcomes?

The hypothesis is not that premium is free protection. Short calls can cushion a decline, but cap gains during rebounds and can become expensive to close. Rolling is a close plus a new trade; it does not erase a loss or guarantee maximum profit.

## 2. Strategy anatomy and terminology

- **Long leg:** one long-dated call on QQQ or SPY, initially researched in the 270–540 calendar-day DTE region, subject to available historical contracts.
- **Overlay:** optionally sell one nearer-dated call while the long call is held. The overlay is inactive in the baseline state.
- If the short call has a different expiry from the long call, the position is generally a **diagonal call spread**, not a stock-covered call. It is not necessarily fully riskless or fully covered in broker/account terms.
- The long call's maximum loss is its premium. The short call's loss is theoretically unlimited in isolation; the long call may offset some but not necessarily all of its exposure at every time/strike combination.
- All results must include the combined position marked to market, not premium received as a standalone profit measure.

## 3. Frozen initial research variants

A. **LONG_CALL_HOLD:** buy the long-dated call and manage only using the common predeclared long-leg expiry/exit rule. No short calls.

B. **ALWAYS_SELL_SHORT_CALL:** sell a short-dated call on a fixed cadence, regardless of regime. This measures the opportunity cost of persistent upside caps.

C. **RISK_TRIGGERED_SHORT_CALL:** keep the long call uncapped in normal conditions; open a short call only after a causal risk detector activates.

D. **RISK_TRIGGERED_DELTA_ROLL:** as in C; when a short call meets the predeclared profit/roll condition, close it and sell a replacement call targeting a configured absolute delta. Re-evaluate on each observation date while the risk regime remains active.

E. **ROLL_WITH_REBOUND_EXIT:** as in D, but close the short call when a separate rebound-risk/unwind rule activates. Do not immediately re-open merely because the prior short was closed.

F. **LONG_LEG_RISK_EXIT:** as in E, with a separately specified rule to reduce or close the long call in extreme-risk conditions. Keep this separate from the short-call overlay to attribute value correctly.

No variant is presumed superior. The long-call baseline is essential because a strategy that collects premium but underperforms long-call hold may not be useful.

## 4. Initial parameter matrix (exploratory, not optimized/promoted)

### Long-call candidates
- DTE target: 270, 365, and 540 calendar days where chain coverage permits.
- Delta targets: 0.70, 0.80, and 0.90; choose the closest valid call by absolute delta distance at entry.
- One contract for theoretical mechanics; separately model whether premium fits the $5,000 account and what fraction of NLV it consumes.

### Short-call candidates
- DTE target: 21 and 35 days, selected from a predeclared eligible range of 14–45 DTE.
- Absolute delta target: 0.10, 0.16, and 0.25.
- Roll/profit capture triggers: evaluate closing at 50% and 75% of maximum short-call premium decay; also evaluate a fixed delta trigger as a separate policy. Do not conflate profit capture and delta targeting into one unexplained trigger.
- When rolling, close the old contract using an executable quote-side assumption, then open a distinct replacement contract selected from information available on that date. Record the net debit/credit and realized P/L separately.
- Only roll when the short-call risk overlay remains enabled, the replacement passes quote/liquidity checks, and the order is feasible. Otherwise close/hold per the frozen policy; never silently skip an adverse roll without logging it.

The matrix is intentionally bounded. First test the main mechanics and data quality; do not grid-search every combination against the full history.

## 5. Causal regime and position-management rules

The first implementation should compare:
1. an always-on short-call control;
2. a simple causal risk gate using only data available at the prior completed close;
3. an independently defined rebound/unwind rule.

No future close, future realized volatility, future option Greek, or future chain row may influence a current decision. Signals computed from close t are executable no earlier than the next observation/session unless the dataset supports a correctly timestamped later execution.

Do not choose a risk gate by maximizing full-sample return. Freeze the candidate gate on development data, then validate chronologically and preserve an untouched holdout. Record every activation, deactivation, opening, closing, roll, expiry, assignment proxy, and rejected trade with reason codes.

## 6. Data feasibility: current project evidence

The existing project specification documents a public SPY end-of-day option-chain dataset with yearly Parquet files for 2008–2025, approximately 24.7 million contract-day rows, and fields including bid/ask/mark, volume, open interest, IV, delta, gamma, theta, vega, strike, expiry, type, and underlying price. The documented source is a preservation mirror of a MIT-licensed dataset. The source was originally used for OPTIONS-001, not validated for this LEAPS design.

The current documentation does **not** establish that QQQ chains are available in the same source, nor that 270–540 DTE calls have sufficient quote/liquidity coverage. These are hard data gates, not assumptions. Next steps:
1. inspect the dataset schema and available symbols;
2. count QQQ and SPY rows by year, DTE bucket, call delta bucket, and quote quality;
3. quantify missing dates, stale/zero bids, spread widths, open interest, and long-DTE coverage;
4. verify source license, mirror immutability/version, and file hashes;
5. if QQQ or long-DTE coverage is inadequate, locate an equivalent documented source or explicitly narrow the test. Never synthesize option prices from ETF prices and label them historical observations.

The existing dataset is EOD-only. The first replay therefore represents a once-daily decision/quote model, not intraday execution. Any trigger that depends on an intraday touch is out of scope unless supported by suitable intraday data.

## 7. Fill, valuation, and accounting requirements

- Preserve raw source bid, ask, mark, IV, Greeks, volume, open interest, underlying close, strike, expiry, and contract identifier.
- For buys, conservative fill starts at ask; for sells, at bid. Midpoint is sensitivity only, never the sole reported result.
- Closing a short call is a buy at ask in the conservative model; selling the replacement call receives bid. Long-call liquidation uses bid.
- Include commissions/fees and an explicit slippage sensitivity. Do not use the mark as if it were always executable.
- Mark all legs on each observation date; include cash, option market value, realized/unrealized P/L, and total equity.
- Do not double-count collected short-call premium as profit while the short liability remains open.
- Expiry, exercise, and assignment must be handled explicitly. If the EOD source cannot resolve exercise/assignment reliably, label that case as a limitation and use conservative deterministic handling.
- Report theoretical one-contract strategy economics separately from account-feasible returns. A $5,000 account may be unable to buy a high-delta LEAPS contract on either underlying; fractional option contracts are not allowed.
- The overlay is not automatically “covered” for broker margin/assignment purposes merely because a LEAPS call exists.

## 8. Required controls and metrics

For each underlying and variant report:
- starting/ending equity and net P/L;
- CAGR only when account-equity accounting and dates make it meaningful;
- maximum drawdown and recovery duration;
- worst day/trade and largest loss from a short-call roll;
- long-call premium at risk and long-leg time-to-expiry at each decision;
- gross short-call premium collected, buyback cost, net overlay P/L, fees/slippage;
- percentage of time the upside was capped and missed upside during sharp rebounds;
- number of rolls, average net credit/debit per roll, roll win/loss distribution;
- assignment/expiry events and any account-feasibility failures;
- conservative versus midpoint sensitivity;
- performance by volatility/trend regime and major stress periods;
- QQQ vs SPY comparison on the same dates, with no cross-underlying pooling that hides differences.

Required controls: long-call hold; always-sell overlay; no-roll short-call overlay; delta-roll overlay; risk-gate placebo or shuffled activation control where feasible. Report failed and rejected trades, not only completed positions.

## 9. Acceptance gates

Do not call the strategy validated unless:
1. symbol and DTE coverage are proven from source rows;
2. chain data passes documented quality checks;
3. entry/exit/roll decisions are causal and reproducible;
4. conservative bid/ask results are primary, with midpoint only as sensitivity;
5. all variants share the same date/underlying and long-call selection basis;
6. total equity includes open option liabilities and realistic closing costs;
7. account feasibility is separated from theoretical P/L;
8. results are split chronologically into development, validation, and untouched holdout;
9. adaptive results beat relevant controls after costs, without the result depending on a small number of hand-selected episodes;
10. no candidate is promoted solely on in-sample terminal wealth.

## 10. Immediate next implementation steps

1. Inspect current option dataset schema, source URLs, and GitHub workflow download pattern.
2. Implement a small data-coverage audit before implementing strategy P/L.
3. Freeze source hashes and write coverage results for SPY and QQQ by DTE/quote quality.
4. If coverage passes, implement deterministic one-long-call lifecycle and then short-call overlay state machine.
5. Add unit tests for expiry boundaries, short-call buyback/roll accounting, rebound close, missing quotes, no replacement contract, and account-feasibility rejection.
6. Add an on-demand GitHub Actions workflow only after the runner is reproducible locally/CI and runtime is bounded.

## Audit log

### 2026-10-12 — Initial specification created
- User requested a standalone LEAPS investigation, independent from B0/F75 and the main ETF strategy.
- Both QQQ and SPY are in scope.
- Core concept: long-dated call is normally uncapped; in deteriorating markets the bot sells shorter-dated calls, can repeatedly roll profitable shorts toward a target delta, and can roll out in time when instability persists.
- Research emphasis: test if dynamic short-call management adds net value after bid/ask costs while preserving rebounds. Rolling is not treated as free profit or automatic risk reduction.
- Data gate: existing project docs establish SPY EOD options data 2008–2025, but QQQ availability and LEAPS-length coverage remain unverified.
- No backtest result exists yet. No strategy is selected, approved, or connected to paper/live trading.
