# Project State Recovery — 2026-10-07

## Purpose

This document restores the authoritative research context after a context-loss event. It is a **state ledger**, not a strategy-selection document. No candidate is promoted by appearing here.

## Canonical project

Repository: `eklu654/Trading-Bot`

The project is a regime-switching automated trading system with independent ETF, options, and switching research. The research principle is:

**source evidence → reconciled specification → deterministic strategy/risk rules → execution**

AI is intended as a later research/regime-classification layer. It may not override hard risk controls or strategy exits.

Current canonical starting balance: **$5,000**. The earlier $2,000 feasibility work is legacy research.

Profitability is the primary objective. Drawdown is a measured tradeoff unless a specific survival, broker, operational, or predeclared risk constraint makes it a veto.

No strategy is currently approved for paper/live trading.

## Major research branches

### ETF-001 and early leveraged-ETF research

ETF-001 is the original leveraged-ETF trend-following benchmark. The plain 200-DMA version is the canonical early control.

The historical 2010-03-11 through 2026-09-25 replay produced approximately:
- 19.53% annualized return
- -37.5% maximum drawdown
- 0.75 Sharpe

The DMA+VIX variant was worse on the canonical comparison. Later inverse-overlay work did not establish a robust inverse advantage.

ETF-011–014 had accounting problems and are not selection evidence. ETF-015 showed a strong validation result but failed to generalize. ETF-016 had no train+validation Sharpe-gate passes. ETF-017 rebuilt the inverse benchmark and remained below the baseline.

### ETF-018 through ETF-030

ETF-018 tested multi-signal transitions using 200-DMA, 50/200, MACD, Donchian channels, momentum, and breadth. Some validation periods improved, but the approach did not survive the 2023+ holdout.

ETF-020–024 tested broader technical-indicator ML, walk-forward retraining, retraining cadence, and transaction-cost stress. The walk-forward improvement was small and event-sparse.

ETF-025 showed that the walk-forward holdout improvement was concentrated around a few activation dates, motivating placebo and event diagnostics.

ETF-026/027/028/029/030 investigated bearish event archetypes, signal transitions, pre-event trend/breadth context, lag robustness, and temporal stability. ETF-030 did **not** establish a stable predictive class. These diagnostics do not constitute a forward trading rule.

### Bull/cash/bear family switching

The research then pivoted toward family-level switching rather than treating the inverse branch as solved.

The switching matrix covers SP500, NASDAQ100, semiconductors, Dow 30, and Russell 2000 families. A family may never hold its bull and bear ETF simultaneously; different families may have different directional states.

The frozen **250-DMA / top-2 / 5-session family rotation** candidate across SPXL, TQQQ, SOXL, UDOW, and TNA showed high historical return but roughly 65–68% drawdown.

Risk-overlay research then tested prior-close realized-volatility targeting and drawdown de-risking. A robustness region around **30% volatility target / 20-session lookback / 20–30% drawdown trigger** remained positive across four calendar eras and under 25 bps stress. The $5,000 whole-share replay also remained positive across train/validation/holdout, with materially lower drawdown than the raw rotation.

The raw high-return strategy is not automatically rejected merely because of drawdown; the return-first re-audit explicitly preserves aggressive leveraged controls as first-class benchmarks.

### OPTIONS-001 / OPTIONS-002

OPTIONS-001 is the rules-based short-premium branch based on documented tastytrade/tastylive methodology.

The key feasibility discovery was that the $5,000 account is constrained by buying-power capacity under the modeled 50%-of-NLV BPR ceiling. Unconstrained historical option P/L is therefore not automatically realizable.

Required option research includes all-market, turbulent-only, broad-sideways, defined-risk structures, $5,000/$10,000 feasibility, broker/BPR validation, and 0DTE when data quality is sufficient.

OPTIONS-002 freezes three wider-wing candidates without historical-performance selection:
- 20-delta shorts / $5 fixed wings
- 20-delta shorts / $10 fixed wings
- 20-delta shorts / 10-delta long wings

It tests ALL_DAYS, BROAD_SIDEWAYS, TURBULENT_ONLY, conservative/midpoint fills, $5k/$10k accounts, and 3/5/7% defined-risk ceilings.

The common-date holdout comparison found positive aggregate P/L for the dynamic 20Δ/10Δ candidate in the tested files but slightly negative normalized P/L per defined loss on average; this is **not deployment evidence**. The $5,000 capital-equivalent holdout was sparse and concentrated in $5-wing turbulent-only configurations.

### Defense/replay branch

The options defense/replay work is a separate research track and must not be collapsed into the ETF research.

The defense replay tested stop/adjustment/roll behavior using historical option quotes. The previously tested **2× initial-credit stop** was rejected; the no-stop baseline was materially better in that replay.

The later optimized defense replay remained a pending research gate around the comparison of **NO_ADJUSTMENT vs ROLL_UNTESTED**, followed by regime/tail/challenge analysis. This branch is not closed merely because TQQQ produced a strong result.

### 0DTE research

The free 0DTESPX benchmark is a separate control branch, using 0dtespx.com rather than Alpaca.

The first frozen 0DTE benchmark covered 1,012 sessions from 2022-06-16 through 2026-09-28:
- 16Δ/6Δ put-credit spread: +1.04% total, 0.07 Sharpe, -16.57% max DD
- 20Δ/10Δ put: -15.55%
- 25Δ/15Δ put: -18.83%

The mirrored call benchmark was also negative. The symmetric iron-condor benchmark produced +14.01% total for 16Δ/6Δ, while wider variants were negative.

These are $100,000 platform previews, not $5,000 account results, and none is deployment-approved. The next frozen 0DTE direction is management timing across bullish and bearish defined-risk structures rather than unconstrained strike optimization.

### SWITCH-001

SWITCH-001 is the regime-performance analysis branch. It is part of the project architecture and was not superseded by the later TQQQ experiments.

## TQQQ / 60-day / Fed research

This later branch is a **research extension**, not the definition of the whole project.

The key insight is that **QQQ 60-day trend/return is a meaningful contextual variable**. It distinguishes sudden shocks inside a still-healthy medium-term trend from persistent deterioration.

Example: during COVID, QQQ's 60-day return remained approximately +2.2% while the 100-DMA was still rising. In the high-rate analysis, high-rate + negative 60-day return produced persistent exits around 28.1% of the time, while high-rate + positive 60-day return produced 0/17 persistent exits.

Therefore:
- market trend is primary;
- Fed/macro state supplies context;
- shock/volatility helps distinguish abrupt dislocation from persistent deterioration.

The frozen contextual rule tested:
`QQQ < 100-DMA AND Fed target > 3.5% AND QQQ 60-day return >= 0`

A shock override used either VIX 20-day change >= +100% or QQQ 20-day realized-volatility change >= +100%.

In the synthetic daily-reset 3x QQQ framework this produced approximately $204.86B from $5,000 over 1999-03-10 through 2026-10-05 versus $128.32B for the immediate 100-DMA baseline. That synthetic result is **not production evidence**.

The actual-TQQQ validation from approximately 2010 through 2026-10-05 produced:
- actual TQQQ + 100-DMA: **$93.89M**, 80.66% CAGR, -35.38% max DD
- actual TQQQ + Fed exception: $80.55M, 79.00% CAGR, -41.92% max DD
- actual TQQQ + three-layer shock override: $91.18M, 80.34% CAGR, -35.38% max DD
- actual TQQQ buy-and-hold: $2.10M, 43.76% CAGR, -81.66% max DD

Therefore the **specific frozen three-layer architecture failed actual-TQQQ validation**, but this does **not** prove that 60-day trend or Fed context is useless. It proves only that this particular architecture did not improve actual TQQQ.

The 60-day trend remains an unresolved candidate feature for broader regime/AI research.

## Synthetic versus actual data

Do not conflate:
- synthetic daily-reset 3x QQQ results beginning in 1999, and
- actual TQQQ results beginning in 2010.

The approximately $128B/$204.86B figures are synthetic-framework results. The approximately $93.89M figure is an actual-TQQQ validation over roughly 2010–2026.

## Current research hierarchy

1. Preserve the full ETF/options/switching research program.
2. Preserve aggressive controls and return-first evaluation.
3. Treat 100-DMA actual-TQQQ as a **validated control/candidate**, not the final system.
4. Preserve 60-day trend as an important contextual feature.
5. Preserve Fed/macro research as context, while rejecting the specific frozen macro exception after actual-TQQQ failure.
6. Continue family-rotation/risk-overlay and options/defense gates rather than abandoning them.
7. Keep AI/regime selection as a later layer; the initial benchmark explicitly does not use AI.
8. No paper/live promotion until economic robustness, realistic execution/account constraints, and autonomous operational safeguards all pass.

## Context-loss correction

The prior reconstruction incorrectly elevated the latest TQQQ actual-validation result into the apparent project center and omitted or underweighted the earlier ETF, family-switching, options, defense/replay, 0DTE, SWITCH-001, and 60-day-trend research.

This document exists to prevent that collapse from happening again.
