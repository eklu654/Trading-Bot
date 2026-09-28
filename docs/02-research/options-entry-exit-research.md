# Options Entry / Exit Research Matrix

**Status:** Research specification — updated 2026-09-28  
**Purpose:** Lock down what is actually supported by official tastylive/tastytrade material before implementation.

## 1. Current evidence

The research no longer supports treating 45 DTE + 16 delta + 50% profit + 21 DTE as a single universal tastytrade rule.

Instead:

- **45 DTE** is a recurring research baseline for short-premium studies.
- **16 delta** appears in official backtests/studies, especially for short premium, but is structure- and study-specific.
- **50% profit / 21 DTE** is documented for several short-premium structures, but exit mechanics vary by structure.
- The project should therefore represent entry and exit as a **strategy-definition matrix**, not as four global constants.

## 2. Verified structure mechanics

Official tastylive mechanics material documents:

| Structure | Entry/Duration evidence | Winner exit | Loss/defense |
|---|---|---|---|
| Short strangle | Commonly studied around 45 DTE | 50% credit or 21 DTE | Defend by rolling untested side, rolling out, and/or inverting |
| Iron condor | 45 DTE appears in research studies | 50% credit or 21 DTE | No loss management required because risk is defined |
| Credit spread | Short-premium structure | 50% credit or 21 DTE | No loss management required because risk is defined |
| Ratio spread | Separate strategy | 30% max profit | Roll out in time if adverse |
| Broken-wing butterfly | Separate strategy | 25% max profit | No loss management due to defined risk |
| Diagonal | Separate strategy | 25% max profit | Roll near-month option forward if adverse |

Source: official tastylive mechanics guide.

## 3. 45-DTE / 16-delta evidence

Official research repeatedly uses 45-DTE short-premium positions.

Examples include:

- 45-DTE 16-delta SPY strangles;
- 45-DTE 16-delta SPY/TLT strangles;
- 45-DTE short-premium backtesting examples.

This supports using 45 DTE and 16 delta as **experimental baseline parameters** for the project's initial short-premium research.

It does not justify freezing them as universal rules across all structures or underlyings.

## 4. 21-DTE evidence

21 DTE is supported by multiple official studies:

- 45-DTE short-premium trades managed at 21 DTE;
- research showing reduced P/L volatility when exiting at 21 DTE;
- probability-of-touch research showing materially different realized touch probabilities when positions are managed at 21 DTE.

The bot should therefore support 21 DTE as a first-class exit parameter, but it must remain structure-specific.

## 5. IV-dependent DTE

Official 2024 research tested:

- 60 DTE when IVR < 30;
- 45 DTE generally;
- 30 DTE when IVR > 30.

The study found similar average daily P/L after adjusting duration for IV and found that 21-DTE management reduced P/L volatility across durations.

Project implication:

DTE selection should be modeled as a function of IVR, structure, and liquidity, rather than assuming 45 DTE is always optimal.

## 6. Proposed initial test matrix

### Entry duration

- 30 DTE
- 45 DTE
- 60 DTE

### Short delta

- 10
- 16
- 20
- 30 where appropriate to the structure

### Winner management

- 25%
- 30%
- 50%
- 75%
- no early profit target

### Time-based management

- 14 DTE
- 21 DTE
- 30 DTE
- expiration

### Volatility-conditioned duration

- fixed 45 DTE
- 60/45/30 DTE by IVR regime
- alternative IVR thresholds

### Required evaluation

Every variant must be evaluated using:

- CAGR / total return where meaningful
- maximum drawdown
- daily/weekly P&L volatility
- return on capital
- win rate
- average winner/loser
- profit factor
- average days in trade
- BPR at entry and peak
- BPR expansion multiple
- beta-weighted Delta
- notional exposure
- correlation concentration
- tail/stress loss
- turnover and transaction costs
- rejected-entry frequency
- small-account feasibility

## 7. Important implementation constraint

The bot must never convert an evidence gap into a hidden default.

Every parameter must have a provenance label:

- primary_source_verified
- documented_example
- project_rule
- experimental
- unresolved

The backtest configuration should expose these labels in generated reports.

## 8. Current unresolved items

- exact production underlying universe;
- exact permitted structures;
- whether naked short options are permitted at the $2,000 research-account level;
- exact delta-selection rules by structure;
- exact IVR thresholds;
- exact undefined-risk loss-defense rules;
- exact portfolio beta-weighted Delta band;
- exact BPR expansion thresholds;
- assignment/expiration handling;
- whether current 2026 tastylive guidance materially differs from the historical framework.

## Sources

- tastylive, “How to Use Options Strategies & Key Mechanics” (2020)
- tastylive, “How Volatility Affects the Selection of Days to Expiration” (2024)
- tastylive, “Options Trading: Exploring the Probability of Touch Across Various Deltas” (2025)
- tastylive, “Costs of Legging Out of Iron Condors” (2023)
