# ETF-001 vs. Tastytrade-Informed Options — $5,000 Comparative Research Plan

**Status:** Active research gate — 2026-09-29

## Core question

The project must **not assume ETF-001 is superior to OPTIONS-001 merely because the current $2,000 naked-SPY-strangle implementation is infeasible**.

The decision question is:

> At a $5,000 starting NLV, does a rules-based, non-0DTE options portfolio informed by verified tastytrade/tastylive methodology provide better standalone and/or complementary historical economics than ETF-001, after realistic fills, fees, account constraints, and chronological validation?

A result is useful only if the strategy is feasible at the tested account size and survives held-out validation.

## ETF baseline assumptions now under review — 2026-09-29

The existing ETF-001 baseline uses 25% TQQQ, 25% SPXL, 25% SOXL, and 25% cash, with the plain 200-day moving-average exit/re-entry rule. These are **untested design choices**, not established optimal settings. The research must directly answer both whether the moving-average rule adds value relative to holding and whether the standing cash allocation helps.

### Required ETF factorial comparison

Run a controlled comparison over the same historical dates, starting NLV, price/dividend conventions, transaction costs, and execution assumptions:

| Signal | Cash allocation | ETF allocation |
|---|---:|---|
| Buy and hold | 0% | 1/3 each TQQQ, SPXL, SOXL |
| Buy and hold | 10% | 30% each |
| Buy and hold | 25% | 25% each |
| Buy and hold | 50% | 16.667% each |
| 200-DMA | 0% | 1/3 each |
| 200-DMA | 10% | 30% each |
| 200-DMA | 25% | 25% each |
| 200-DMA | 50% | 16.667% each |
| 200-DMA + VIX filter | 0%, 10%, 25%, 50% | Same proportional ETF weights |

Include a 100%-cash reference series. Keep the three ETF weights equal within the invested allocation for this first controlled test; any unequal-weight experiment should be a separate, explicitly labeled follow-up rather than mixed into this comparison.

The core comparison is the paired difference between buy-and-hold and 200-DMA **at each identical cash allocation**. Separately compare cash levels **within each signal**. This isolates the value of the timing rule from the effect of simply holding less leveraged exposure.

### Implementation status — 2026-09-29

The ETF replay now generates buy-and-hold, 200-DMA, and 200-DMA-plus-VIX results at 0%, 10%, 25%, and 50% target cash, plus a 100% cash reference. It writes per-configuration daily paths and a combined summary. The 25% 200-DMA and VIX outputs retain the prior artifact filenames for compatibility.

The implementation uses unadjusted close for the moving-average signal and adjusted close for return accounting when available. Buy-and-hold starts with equal proportional ETF weights and allows those weights to drift. The 200-DMA signal is evaluated separately for each ETF and applied with a one-session lag; active sleeves are rebalanced to equal target weights at each close in this first-pass model. Cash earns 0% in this research model. These rebalancing policies differ by design and must be kept visible when interpreting the comparison.

**Not yet included:** commissions, slippage, spread costs, fractional-share/whole-share execution constraints, or broker-specific fills. Therefore the new output is a controlled first-pass comparison, not yet an execution-realistic result. The GitHub Actions run triggered by these code changes must finish successfully before treating the artifacts as validated.

### Portfolio accounting and implementation controls

- State whether weights are initial weights with buy-and-hold drift or periodically rebalanced weights. Use the existing strategy's actual behavior as the primary baseline and label any alternative rebalancing policy separately.
- For the 200-DMA strategy, specify whether each ETF's signal is evaluated independently or whether one signal controls the whole basket. Preserve the current implementation as the primary case; report individual-ETF signal results as diagnostics.
- Define the 200-DMA calculation, warm-up period, close-to-close signal timing, and next-session execution consistently. Do not use a same-day close that would not have been known at order time.
- Account for cash yield only if the historical data and assumptions support it; otherwise report a zero-yield cash baseline and a clearly separated cash-yield sensitivity.
- Include dividends and splits consistently, and document whether prices are adjusted or unadjusted.
- Include realistic slippage, fees, and turnover from switching. Do not treat a theoretical close-price fill as guaranteed.
- Report time invested, cash exposure, trade count, turnover, and periods in which a rule exits and later re-enters.

### Required metrics and interpretation

For every variant, report total return, CAGR, annualized volatility, Sharpe, Sortino, maximum drawdown, recovery time, worst day, and time invested. Include annual and regime-level returns, plus performance across major drawdown and recovery periods.

The 200-DMA rule should be evaluated on paired metrics, not just CAGR: it may lower drawdown while also missing recoveries or reducing total return. The cash allocation should be evaluated for its effects on both risk and return. A lower drawdown alone does not establish that a variant is preferable, and a higher historical return alone does not establish robustness.

### Validation discipline

Freeze the candidate grid before examining final holdout results. Use chronological development, validation, and untouched holdout periods. Do not tune cash percentage or signal parameters on the final holdout. Include sensitivity to modest execution costs and plausible cash yields. Treat any parameter search as multiple testing and report the full tested grid, not only favorable variants.

No single variant is preselected as the winner. The current 25%-cash 200-DMA result remains a baseline until this direct comparison is complete.

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

## $5,000 implementation progress — 2026-09-29

The first defined-risk challenger is now implemented as **OPTIONS-002**, a 45-DTE SPY iron condor using approximately 16-delta short strikes, 2-point wings, a 50% profit target or 21-DTE exit, and no undefined-risk 2x-credit stop. The research workflow now runs this candidate across ALL_DAYS, BROAD_SIDEWAYS, and TURBULENT_ONLY under both conservative and midpoint fills.

Account feasibility is tested separately at **$5,000** with 3%, 5%, and 7% maximum defined-risk-per-position sensitivity bands, while retaining a 50% aggregate BPR ceiling. This is deliberately a sensitivity study rather than a claim that any one sizing band is authoritative.

The first CI pass caught a test-environment dependency/import issue before the new research result could be considered valid. The dependency and package-import paths have been corrected, and the historical workflow is rerunning. No OPTIONS-002 performance number is being treated as established until that run completes successfully.

## Current conclusion

**Unknown.**

The project has not established that ETF-001 is better than a properly constructed $5,000 tastytrade-informed options portfolio.

It has established only that:

- ETF-001 currently has a complete historical baseline;
- the current $2,000 naked-SPY-strangle implementation is infeasible under the current risk model;
- 0DTE is not currently justified as the options solution;
- a properly constrained $5,000 non-0DTE options comparison is now required.

The next authoritative research step is therefore the **$5,000 options-vs-ETF comparison**, followed by the regime-specific and combined-portfolio test.

### Methodology correction — OPTIONS-002 2-point wings are a capital-feasibility probe, not the final tastytrade-fidelity baseline

The initial OPTIONS-002 implementation uses a 45-DTE SPY iron condor with approximately 16-delta short strikes and 2-point wings. This should **not** be treated as a faithful representation of the broader tastylive/tastytrade iron-condor methodology. Current tastylive research describes 45-DTE SPY iron-condor studies using materially wider wings (including $5/$10/$20 and $10–$20 ranges), and a separate tastylive article specifically reports that $1–$2-wide SPY iron condors historically had weaker profitability characteristics than wider constructions. The same research emphasizes 50% profit management and 21-DTE management. Therefore, the 2-point run is retained as a deliberately capital-constrained feasibility probe, while the next options research pass must test wider, methodology-aligned constructions before drawing conclusions about a $5,000 tastytrade-informed portfolio.

Next frozen-development candidates should include at least: (1) 20-delta shorts with $5 wings, (2) 20-delta shorts with $10 wings, and (3) a dynamic 20/10-delta construction where the long strikes are selected by delta rather than fixed width. These candidates should be evaluated under the same $5,000 account-feasibility gates, conservative/mid execution, 50% profit target, and 21-DTE exit. No candidate should be promoted based on full-sample optimization; development/validation results must be frozen before the untouched holdout is used.

## Superseding $5,000 gate — 2026-10-01

The $2,000 naked-SPY-strangle findings above are retained as historical research only. **$5,000 is now the canonical starting balance.** The active defined-risk research gate is OPTIONS-002, using wider-wing candidates and account-feasibility replay at $5,000 and $10,000. The completed 2023+ artifact shows that $5,000 accepted-trade availability is sparse and concentrated in selected $5-wing turbulent-only configurations; candidate-level P&L is therefore not sufficient evidence of portfolio viability.

The current next step is a capital-equivalent comparison that uses the actual $5,000 account-feasibility acceptance lifecycle and compares it with ETF-001 on the same untouched 2023+ holdout. This comparison is descriptive and does not select a candidate on holdout performance.
