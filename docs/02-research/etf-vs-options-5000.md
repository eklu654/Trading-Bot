# ETF-001 vs. Tastytrade-Informed Options — $5,000 Comparative Research Plan

**Status:** Active research gate — 2026-09-29

## Core question

The project must **not assume ETF-001 is superior to OPTIONS-001 merely because the current $2,000 naked-SPY-strangle implementation is infeasible**.

The decision question is:

> At a $5,000 starting NLV, does a rules-based, non-0DTE options portfolio informed by verified tastytrade/tastylive methodology provide better standalone and/or complementary historical economics than ETF-001, after realistic fills, fees, account constraints, and chronological validation?

A result is useful only if the strategy is feasible at the tested account size and survives held-out validation.

## Important distinction

The current ETF result and the current options result are not directly comparable yet.

ETF-001 has a complete historical replay from 2010-03-11 through 2026-09-25. The plain 200-day trend version currently reports 19.53% annualized return and approximately 37.5% maximum drawdown in that historical model.

The current OPTIONS-001 naked-SPY-strangle replay is not account-valid at $2,000: all 929 candidate entries were rejected under the current modeled 50%-of-NLV BPR ceiling.

Therefore neither of these facts establishes that ETF-001 is the superior strategy at $5,000.

## $5,000 options candidates

Test the following as separate strategy candidates rather than silently modifying OPTIONS-001:

1. **OPTIONS-001A — 45-DTE short strangle**
   - approximately 45 DTE baseline
   - approximately 16-delta short strikes
   - structure-specific profit/time management
   - documented undefined-risk loss-management benchmark
   - portfolio Delta/BPR/concentration controls

2. **OPTIONS-002 — 45-DTE iron condor**
   - approximately 45 DTE
   - defined risk
   - approximately 16-delta short strikes as the initial baseline
   - identical portfolio-level controls

3. **OPTIONS-003 — 30–60 DTE defined-risk credit-spread portfolio**
   - bullish and bearish verticals
   - approximately 16-delta baseline where data permits
   - portfolio-level Delta balancing
   - structure-specific exits

4. **Duration sensitivity**
   - test approximately 30, 45, and 60 DTE
   - do not optimize beyond the frozen candidate set until chronological validation is complete

The historical tastytrade framework documented in the project distinguishes aggregate VIX-based buying-power allocation from individual NLV sizing and distinguishes undefined-risk from defined-risk trade sizing. Project rules must remain explicitly separate from claims about current universal tastytrade requirements.

## Regime tests

Every candidate must first be tested **unconditionally across the full common historical sample**.

Then segment results into:

- trending / favorable ETF regime;
- sideways/choppy regime;
- elevated-volatility regime;
- turbulent regime;
- ETF drawdown periods;
- ETF recovery periods.

The purpose of the regime test is not to find a convenient subset that makes options profitable. It is to determine whether options have a repeatable contribution specifically where ETF-001 is weak.

## Common-account constraints

For the $5,000 case, the authoritative replay must enforce the same hard constraints used elsewhere in the project:

- NLV-based position sizing;
- aggregate BPR ceiling;
- stress-loss ceiling;
- underlying concentration;
- beta-weighted Delta;
- correlation exposure;
- concurrent-position limits;
- expiration concentration;
- realistic contract granularity;
- conservative and mid execution assumptions;
- transaction fees and slippage.

No constraint may be relaxed merely to increase trade count.

Record every rejected candidate and the rejection reason.

## Comparison metrics

For each standalone strategy and the combined switcher, record:

- total return;
- CAGR where meaningful;
- annualized volatility;
- Sharpe;
- Sortino;
- maximum drawdown;
- worst day/trade;
- profit factor;
- expectancy;
- trade count;
- time invested;
- turnover;
- fees/slippage;
- BPR utilization;
- maximum BPR expansion;
- stress loss;
- rejected-entry rate;
- account-feasibility rate;
- performance by regime.

Most importantly, measure **joint ETF/options behavior**:

- correlation of daily returns;
- overlap of drawdowns;
- options return during ETF drawdowns;
- combined maximum drawdown;
- combined Sharpe/Sortino;
- return retained versus ETF-only;
- drawdown reduction versus ETF-only;
- switching frequency;
- performance after switching costs/transition assumptions.

## Chronological validation

Do not select a strategy from the full sample and then call the same sample validation.

Use chronological development and holdout periods.

At minimum:

1. development period;
2. validation period;
3. untouched final holdout.

The candidate rules must be frozen before the final holdout is evaluated.

A strategy that is positive only because of a small number of favorable historical periods is not sufficient.

## Decision framework

No numerical winner/ranking is assigned in advance.

The evidence should answer four independent questions:

### A. Is ETF-001 viable by itself?

If not, improve/reject ETF-001 before adding options complexity.

### B. Is a $5,000 options candidate viable by itself?

If not, options do not automatically become useful simply because they diversify ETF-001.

### C. Does the options candidate perform differently when ETF-001 is weak?

This is the critical complementarity test.

### D. Does switching improve the actual portfolio?

The combined strategy must be compared with ETF-only and options-only using the same dates, costs, account size, and risk constraints.

The switcher earns a place only if the evidence demonstrates a sufficiently robust improvement in the actual portfolio objective. This is a research conclusion, not a predetermined expectation.

## Current external evidence

Cboe's long-running PUT index demonstrates that systematic index put writing can have a persistent historical volatility-risk-premium component, but it also demonstrates that option writing is not automatically superior to equities. As of March 31, 2026, Cboe reports 6.8% annualized return, 10.8% annualized volatility, -32.7% maximum drawdown and 0.49 Sharpe for the PUT index since 2007, versus 10.3%, 15.4%, -50.9% and 0.57 respectively for the S&P 500 Total Return Index.

Those benchmark results are useful evidence that options deserve serious testing, but they are **not substitutes for testing our specific $5,000 rules**.

## Current conclusion

**Unknown.**

The project has not established that ETF-001 is better than a properly constructed $5,000 tastytrade-informed options portfolio.

It has established only that:

- ETF-001 currently has a complete historical baseline;
- the current $2,000 naked-SPY-strangle implementation is infeasible under the current risk model;
- 0DTE is not currently justified as the options solution;
- a properly constrained $5,000 non-0DTE options comparison is now required.

The next authoritative research step is therefore the **$5,000 options-vs-ETF comparison**, followed by the regime-specific and combined-portfolio test.
