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

IMPORTANT TIMING-AUDIT STATUS (2026-10-07): the synthetic wealth figures below were produced by an execution implementation that applied the close decision to the same day's intraday leg. That is look-ahead under the project's close-to-next-open convention. The affected synthetic wealth figures, including approximately $128.32B and $204.86B, are therefore **invalid/provisional and must not be used for strategy selection**. Corrected causal replays were committed on 2026-10-07 and are the authoritative rerun path.

The actual-TQQQ validation from approximately 2010 through 2026-10-05 produced (the dedicated actual-TQQQ replay was also corrected to the same causal convention on 2026-10-07):
- actual TQQQ + 100-DMA: **$93.89M**, 80.66% CAGR, -35.38% max DD
- actual TQQQ + Fed exception: $80.55M, 79.00% CAGR, -41.92% max DD
- actual TQQQ + three-layer shock override: $91.18M, 80.34% CAGR, -35.38% max DD
- actual TQQQ buy-and-hold: $2.10M, 43.76% CAGR, -81.66% max DD

Therefore the **specific frozen three-layer architecture failed the prior actual-TQQQ validation**, but this does **not** prove that 60-day trend or Fed context is useless. The corrected actual replay is now the version that must be used for final validation; no old synthetic wealth result may override it. It proves only that this particular architecture did not improve actual TQQQ.

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


## 2026-10-07 timing-audit correction

A systematic audit identified a look-ahead implementation error in several newly added synthetic next-open replay scripts. The intended convention is:

**decision at today's close → execution at tomorrow's open**

For a day (t), the overnight move into the open belongs to the position already held before that open, while the intraday move after the open belongs to the decision made at the prior close.

Corrected commits on `main`:
- `8b2fafba08fd8ac89de3d5bb60c758a4921ae320` — dot-com survivability
- `36a7b4be0e1ae2dcc4ffee5d89ec7cd6f45cd40b` — Fed-conditioned 100-DMA
- `72b1ffe9dea2274d797265ebde4590c5e47d8094` / `3b5318b9ce7c54355141cc4273f440bbf1112621` — three-layer shock
- `20c559c39b3de9b570c0310d0740daba03d72529` — frozen regime strategy
- `86f346d89a191af5605323054864530042224aef` — canonical reconciliation
- `d0b3bbc2ec95c97e7870a2d9ec1202daa692eaa2` — actual three-layer validation

The corrected dot-com implementation explicitly shifts execution state before applying the intraday leg. Existing actual-TQQQ partial-exposure and dedicated next-open DMA/re-entry research already uses the causal prior-close state convention and was not rewritten merely because of this audit.

The old synthetic $128.3B/$183.1B/$204.9B results, and any other wealth results produced by the affected implementation, are now historical/provisional only. They must be rerun before being cited.



## Corrected replay results available as of 2026-10-07

The first completed post-audit artifacts materially change the TQQQ conclusions:

- **Synthetic dot-com survivability, causal next-open replay:** synthetic buy-and-hold ends at approximately **$58.7K**; the prior synthetic **100-DMA/0%-below result falls from $128.3B to about $207.1K**. The strongest row in the tested 100–300 DMA / 0–100% below-DMA grid is currently **300-DMA / 0% below at about $872.1K**, with approximately **-62.8% max drawdown**. This is still synthetic and descriptive, not production evidence.
- **Causal Fed-conditioned 100-DMA:** full-period baseline is approximately **$207.1K** versus **$110.1K** for the Fed/60-day exception. The exception therefore fails this causal synthetic replay rather than improving it.
- **Causal three-layer synthetic replay:** full-period baseline approximately **$207.1K**, Fed-conditioned approximately **$110.1K**, three-layer approximately **$90.0K**. The three-layer shock override does not rescue the architecture in the corrected full-history replay.
- **Macro-aware post-exit reentry:** causal baseline approximately **$207.1K** versus approximately **$97.4K** for the frozen macro-reentry veto. This rejects the current frozen macro-reentry implementation as an improvement.
- **Canonical synthetic-vs-actual reconciliation:** for the same three-layer signal over 2010–2026, corrected synthetic final is approximately **$165.9K** and corrected actual-TQQQ final approximately **$91.8K**. The signal itself is therefore not producing the prior spectacular synthetic wealth when executed causally.
- **Corrected actual-TQQQ main validation:** causal 100-DMA QQQ-signal final is approximately **$84.6K**, Fed-conditioned approximately **$106.9K**, three-layer approximately **$91.8K**, versus approximately **$2.03M** for actual TQQQ buy-and-hold over this validation window. This specific frozen architecture is therefore not a return-maximizing winner on actual TQQQ.

The actual-TQQQ cost-stress diagnostic was subsequently found to contain a second look-ahead implementation in its stress-only calculation and was corrected in commit `f9fb321970e6cfe54d154edaa6add916f17e083c`. Its rerun is pending. The causal headline table above does not use that flawed stress calculation.

These corrected results supersede the old synthetic $128B/$183B/$204B wealth figures for research decisions.
