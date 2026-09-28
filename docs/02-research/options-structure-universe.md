# Options Structure-Universe Research

**Status:** Research specification — initial scope proposed, not production-frozen  
**Last reviewed:** 2026-09-28

## 1. Purpose

Define a tractable first structure set for OPTIONS-001. The goal is not to implement every structure described in tastytrade education. Each additional structure creates distinct entry, sizing, execution, adjustment, assignment and backtest requirements.

The $2,000 account is a feasibility experiment. A structure is not eligible merely because it is part of the historical methodology; it must pass capital, liquidity, exposure and operational constraints.

## 2. Proposed initial research set

| Structure | Risk class | Directional profile | Research role | Initial status |
|---|---|---|---|---|
| Short strangle | Undefined | Neutral at entry; can become directional | Primary short-volatility benchmark; supports existing replay work | Include in research; production eligibility unresolved |
| Iron condor | Defined | Neutral at entry | Compare capped risk against strangle economics | Include in research |
| Put/call credit vertical | Defined | Directional | Test as a directional alternative or controlled portfolio-balancing instrument | Include as separate directional family |

This is a proposed test set, not an approved live-trading whitelist. It deliberately prioritizes structures with clear mechanics and direct research precedent.

## 3. Evidence and implications

### Short strangle

A short strangle sells an out-of-the-money put and call in the same expiration. It collects premium and benefits from time passing and/or implied volatility contraction, but has undefined upside risk and substantial downside exposure. tastylive describes a recurring target timeframe around 45 DTE and a general 50%-of-credit profit target. Its documented defensive approaches include rolling the untested side closer to the underlying, rolling out in time, and inversion.

**Project implication:** retain as the primary undefined-risk benchmark, but do not permit it in a $2,000 account until contract-level BPR, stress expansion, tail loss, and account sizing all pass explicit constraints. The initial replay's results are not proof that a naked strangle is feasible or robust.

### Iron condor

An iron condor combines an out-of-the-money put credit spread and call credit spread in one expiration. It is a neutral, defined-risk alternative to a short strangle. The long wings cap loss; maximum expiration loss is the width of the wider side less the net credit. tastylive's current strategy material describes a common entry-credit heuristic of roughly one-third of spread width and a 50% profit-taking approach. These are educational heuristics to test, not hard-coded rules.

**Project implication:** compare against a strangle using matched underlying, entry date, DTE, short-strike delta, and risk budget where possible. Compare both equal-contract and equal-maximum-loss sizing; report that these answer different questions. Wing width must be a configurable experimental parameter, and all-in execution costs for four legs must be modeled.

### Credit verticals

A short put vertical is bullish; a short call vertical is bearish. Each has defined maximum loss at entry, and the long option limits exposure. tastylive describes selling premium in elevated-IV conditions and generally not defending losing defined-risk verticals; a tested spread near or inside 21 DTE may be rolled to a later cycle if a credit is available in some documented mechanics.

**Project implication:** keep directional verticals distinct from neutral premium-selling structures. They should not be presented as delta-neutral substitutes. Evaluate whether their use improves portfolio-level directional balance only after including the risk of adding directional exposure, and compare a no-adjustment baseline against explicitly defined roll variants.

## 4. Structures deferred from the first implementation

- **Short straddle:** undefined-risk, ATM variant with materially different gamma and breakeven behavior. Defer until the strangle benchmark is stable.
- **Iron butterfly:** defined-risk, centered structure with a narrower profitable range and different strike-selection mechanics. Defer until iron-condor comparisons are complete.
- **Broken-wing butterfly:** different payoff geometry and structure-specific profit management; defer.
- **Ratio spread:** asymmetric risk profile and distinct defense; defer.
- **Diagonal/calendar:** long-vega, multi-expiration exposure and distinct management; defer, especially while the core project focuses on short premium.
- **Jade lizard and other hybrids:** defer until their risk constraints and account feasibility are explicitly specified.

Deferral is a sequencing decision, not a conclusion that these structures are inferior.

## 5. Required comparisons

For each included structure, compare:

1. Fixed 45 DTE against 30- and 60-DTE variants where the data supports them.
2. Short-leg delta variants where applicable; do not force the same delta definition onto structures with different geometries.
3. Profit exits at 25%, 30%, 50%, 75%, and no early target where economically meaningful.
4. Time exits at 14, 21, and 30 DTE, plus expiration only as a controlled benchmark.
5. IVR-conditioned duration against fixed duration.
6. Midpoint, conservative bid/ask, and slippage/fee assumptions.
7. Equal-contract, equal-BPR, and equal-maximum-loss comparisons where applicable.
8. Regime-conditioned entry versus an all-session benchmark.

Report P/L alongside max drawdown, worst trade, tail/stress loss, BPR at entry and peak, BPR expansion, notional exposure, beta-weighted Delta, correlation concentration, trade count, rejection rate, and transaction costs. Win rate alone is not an adequate selection metric.

## 6. $2,000 feasibility gates

A candidate trade must be rejected if any hard constraint fails, even if it has positive modeled expectancy. At minimum, evaluate:

- broker- and structure-specific BPR;
- per-trade NLV sizing and historical sleeve allocation;
- 15% single-underlying concentration constraint from the historical framework;
- maximum defined loss for defined-risk trades;
- undefined-risk stress loss and BPR expansion;
- quote quality and realistic multi-leg fills;
- minimum premium after commissions and fees;
- assignment, exercise and expiration exposure;
- portfolio-level directional, gamma, notional and correlation risk.

Do not widen spreads, increase contracts, relax NLV sizing, or bypass allocation ceilings merely to force a trade through the $2,000 feasibility test. Record rejected opportunities as results.

## 7. Preliminary scope recommendation

Use short strangles and iron condors as the core neutral comparison. Include credit verticals as a separate directional family, but do not let them silently substitute for neutral entries. Keep other structures out of the first implementation until the core replay and feasibility work establishes a need.

No production structure is approved by this document. The historical short-strangle replay and its defense variants remain a separate, unfinished validation track.

## Sources

- tastylive, “How to Use Options Strategies & Key Mechanics” (2020): https://www.tastylive.com/news-insights/how-to-use-options-strategies-amp-key-mechanics-takeaways
- tastylive, “Strangle Option Strategy: Long & Short Strangle”: https://www.tastylive.com/concepts-strategies/strangle
- tastylive, “Iron Condor: Everything You Need To Know”: https://www.tastylive.com/concepts-strategies/iron-condor
- tastylive, “Vertical Spread: What are Vertical Spread Options?”: https://www.tastylive.com/concepts-strategies/vertical-spread
- tastylive, “What to do When Your Short Vertical Spread Gets Tested” (2024): https://www.tastylive.com/news-insights/what-to-do-when-your-short-vertical-spread-gets-tested
- tastylive, “Mechanics for Defined Risk” (2018): https://www.tastylive.com/shows/best-practices/episodes/mechanics-for-defined-risk-08-27-2018
