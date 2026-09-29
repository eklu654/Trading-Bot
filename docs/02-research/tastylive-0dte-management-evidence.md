# Tastytrade/tastylive 0DTE Management Evidence

**Date reviewed:** 2026-09-29  
**Status:** Research inputs; not yet encoded as authoritative bot rules

## Purpose

Record the documented 0DTE management approaches relevant to the Trading-Bot research. tastylive publishes multiple studies and examples; these should not be collapsed into one universal "tastytrade 0DTE rule." Individual studies use different structures, entry times, targets, and holding periods.

## Source-derived findings

### 1. Profit targets are strategy- and study-dependent

A tastylive 2025-12-29 study description reports comparisons of 10%, 20%, and 25% profit targets against holding to expiration for iron flies and iron condors. It describes a tradeoff: smaller targets tend to raise win rates and consistency, while larger targets can produce higher average profits with greater risk and variability.

The same study also compared $10–$30-wide put spreads entered at the open or shortly afterward; it reports that wider spreads had higher average profits and larger drawdowns, while entry timing had little impact in that particular study.

Source: https://www.youtube.com/watch?v=VGjjNll86-4 (tastylive, 2025-12-29; study description and chapter outline).

**Bot implication:** test targets as predeclared alternatives. Do not hard-code 50% as a universal 0DTE exit merely because it is common in longer-DTE premium-selling examples.

### 2. Aggressive management and re-entry have been discussed as a 0DTE approach

A tastylive article dated 2024-01-20 describes its evolving 0DTE work, including daily butterflies, directional vertical spreads, and "aggressive management." It says repeatedly re-entering winning 0DTE trades had produced larger profits in the research discussed. The article also notes elevated gamma exposure in 0DTE spreads compared with its 45-DTE reference approach.

Source: https://www.tastylive.com/news-insights/pros-share-proven-tactics-trading-0dte-options

**Bot implication:** re-entry should be a separate, explicitly tested strategy dimension with a hard daily trade cap, aggregate loss limit, and cooldown. It must not be inferred to be safe or profitable from the article's qualitative summary.

### 3. There is no blanket rolling rule for all structures

tastylive's rolling guidance describes rolling as a defensive tactic when the original assumption remains intact. It discusses probability of profit below 33% or a position reaching one to two times its profit target as possible prompts to consider rolling for duration. It also says defined-risk trades are generally not rolled in most cases, though exceptions are discussed when a short strike is near/inside the money and the long strike remains out of the money.

Source: https://www.tastylive.com/definitions/rolling-options

**Bot implication:** do not automatically roll 0DTE positions. Same-day expiration, gamma, limited remaining time, and the possibility of widening losses require a separate, bounded roll policy if rolling is tested at all. A roll must be modeled as closing the old trade and opening a new one, including both legs' costs and risk.

### 4. General defense guidance is not itself a 0DTE-specific mandate

tastylive's defense overview discusses closing trades at multiples of initial credit, including a 2x-credit loss threshold as a result that its research found could be optimal in some premium-selling contexts. It also emphasizes that smaller accounts have less flexibility to hold or roll losing trades.

Source: https://www.tastylive.com/concepts-strategies/defending-positions

**Bot implication:** the existing 2x-credit loss benchmark may be included as a comparison where the platform supports it, but it must not be assumed to be validated for 0DTE. It also cannot override a defined maximum-loss or account-level kill switch.

### 5. Backtesting must specify entry and exit mechanics

tastylive's 2024-10-07 backtesting tutorial describes configurable strategy, delta, quantity, DTE, active-trade cap, and exit conditions including profit realized and DTE remaining. It also describes reviewing summary, per-trade details, and execution logs.

Source: https://www.tastylive.com/news-insights/backtesting-options-trades-learn-use-tastytrade-backtesting-tool

**Bot implication:** preserve full configuration and trade-level logs for every comparison. Aggregate win rate alone is insufficient.

## Proposed 0DTE test matrix

Keep these as separate hypotheses:

| Dimension | Frozen comparison candidates |
|---|---|
| Structures | put credit spread; call credit spread; iron condor; iron butterfly; butterfly |
| Profit exits | 10%; 20%; 25%; 50%; no target/close by a specified time |
| Entry | 09:35 ET baseline; 09:45 and 10:00 ET comparisons |
| Time exits | 12:00 ET; 15:55 ET; expiration settlement only where appropriate |
| Loss controls | defined max loss; 2x initial credit as a research comparison where meaningful |
| Re-entry | disabled baseline; separately tested capped re-entry |
| Fills | platform default; conservative/adverse fill sensitivity |
| Capital | $2,000; $5,000; $10,000; $20,000, with actual risk/BPR constraints |

This is a test matrix, not a recommendation to trade each variant. Because the first 0DTE benchmark shows large loss asymmetry and cost sensitivity, variants must be judged on net expectancy, drawdown, tail losses, risk-adjusted return, and account feasibility—not win rate alone.

## Current implementation decision

1. Retain the initial 16Δ put-credit spread only as a comparison/control.
2. Run the mirrored call-spread and defined-risk iron-condor benchmarks before expanding into more complex structures.
3. Treat 10%, 20%, 25%, and 50% targets as competing hypotheses; avoid selecting a target from the full sample and then reporting that same sample as validation.
4. Do not add automatic rolling or repeated re-entry to the autonomous system until they pass independent tests.
5. Preserve hard risk controls regardless of any tastylive-inspired management rule.
6. Keep all 0DTE candidates research-only until execution assumptions, account feasibility, and out-of-sample behavior have been independently reviewed.
