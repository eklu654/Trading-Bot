# Options-Selling Strategy Specification

**Status:** Research draft — historical portfolio framework reconstructed; production rules not yet frozen  
**Last reviewed:** 2026-09-28

## 1. Purpose

This document defines the rules for the options-selling strategy used by the project.

The strategy is intended to model a disciplined, rules-based short-premium approach informed by tastytrade/tastylive educational material. It separates:

1. **Verified methodology** — supported by primary tastytrade/tastylive documentation.
2. **Project interpretation** — how source material is translated into system behavior.
3. **Project-specific rules** — choices made for this bot that are not claimed to be universal tastytrade rules.
4. **Open research questions** — items requiring verification before the strategy is frozen.

A project rule must never be presented as an official tastytrade rule unless the source establishes it.

## 2. Portfolio objective

The strategy seeks to systematically sell option premium while controlling buying-power usage, directional exposure, concentration, volatility-driven BPR expansion, tail risk, time-to-expiration risk, and execution risk.

AI may help identify eligible opportunities, but it cannot override hard entry, sizing, risk, or exit rules.

## 3. Historical portfolio framework — now verified

A primary-source tastytrade presentation, **From Strategy to Practice — India 2020**, provides a coherent portfolio framework:

- market volatility determines the percentage of capital used;
- individual trade sizing is measured as a percentage of **net liquidation value**;
- no more than **15% of net liq in any single underlying**;
- undefined-risk trades: **3–7%**;
- defined-risk trades: **1–3%**;
- VIX-based maximum allocation of buying power;
- 75% allocated to undefined-risk strategies;
- 25% allocated to defined-risk strategies.

Primary-source presentation:
https://s3.amazonaws.com/tastytradepublicmedia/website/cms/tastytrade_TomSosnoff_India2020.pdf/original/tastytrade_TomSosnoff_India2020.pdf

The user's screenshot also preserves the VIX table. **Screenshot_20210413-175727.png**. fileciteturn2file0

This is now treated as **verified historical methodology**, not as a universally current 2026 requirement.

## 4. Historical VIX allocation

| VIX | Maximum allocation of buying power |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| >40 | 50% |

The important metric distinction is:

- **VIX table:** maximum aggregate allocation of **buying power**;
- **individual trade sizing:** percentage of **net liquidation value**.

These are not interchangeable.

The VIX figure is a ceiling, not a required deployment amount.

## 5. Historical strategy-type allocation

The recovered presentation places the following strategy mix immediately after the VIX allocation framework:

- **75% of the allocated options portfolio → undefined-risk strategies**
- **25% → defined-risk strategies**

Historical examples include:

### Undefined risk
- Straddles in higher IV Rank environments
- Strangles in lower IV Rank environments

### Defined risk
- Iron condors
- Debit spreads
- Credit spreads

For this project's historical-framework reconstruction, the 75/25 split is modeled **inside the VIX-derived aggregate options allocation**.

This nesting is a project interpretation of the presentation's slide sequence and wording; it is not being represented as a current universal tastytrade rule.

## 6. Individual trade sizing

The primary-source presentation states:

| Position type | Historical sizing |
|---|---:|
| Undefined risk | 3–7% of net liq |
| Defined risk | 1–3% of net liq |

It also states:

**No more than 15% of net liq in any single underlying.**

This supersedes the previous draft's treatment of 5–7% as merely a project-specific small-account exception.

The project may still need a small-account execution policy, but the historical 3–7% undefined-risk range is directly documented.

## 7. Project-specific $2,000 account

Initial paper testing uses a $2,000 account per strategy instance.

At $2,000, the historical ranges translate to:

- undefined-risk trade: $60–$140 net-liq equivalent;
- defined-risk trade: $20–$60 net-liq equivalent;
- maximum single-underlying sizing: $300 net-liq equivalent;
- VIX allocation ceiling: $500–$1,000 depending on VIX.

These are mathematical translations of the historical framework, not instructions to deploy those amounts.

The bot must reject or flag trades when contract granularity makes the historical framework infeasible. It must not silently increase size merely to make a trade possible.

## 8. Entry framework — provisional

The current research baseline is:

- prefer liquid underlyings;
- prefer approximately **45 DTE** for core short-premium positions;
- consider approximately **16-delta** short strikes for low-delta premium structures;
- require sufficient implied-volatility opportunity;
- respect portfolio-level Delta constraints;
- respect VIX/BP allocation;
- respect 75/25 strategy-type allocation;
- respect individual net-liq sizing;
- respect 15% underlying concentration;
- reject excessive correlation or tail exposure.

The 45-DTE/16-delta values are research baselines rather than universal rules for every strategy.

## 9. Exit framework — provisional

The strategy uses deterministic exits.

Research evidence supports:

- management around **50% of maximum profit** for several short-premium structures;
- management around **21 DTE** for several 45-DTE short-premium studies and strategy guides.

For example, tastylive's 2020 strategy-mechanics material describes short strangles, iron condors, and credit spreads as managed at 50% of credit received or 21 DTE, whichever comes first. A 2024 tastylive study also found 21-DTE management materially reduced volatility and downside losses in the tested SPY setups.

These remain strategy-specific research baselines until the exact trade universe is frozen.

## 10. Portfolio directional exposure

The project intends to maintain a substantially delta-balanced portfolio rather than making an uncontrolled directional bet.

Both bullish and bearish option structures may be held simultaneously.

SPY beta-weighted Delta is the primary standardized directional-exposure metric.

However, beta-weighted Delta is not a complete tail-risk measure. The risk engine must also monitor unit/notional exposure, BPR, correlation, and maximum loss.

Before implementation, define:

- aggregate beta-weighted-Delta band;
- individual position delta limits;
- correlation handling;
- stress behavior;
- neutrality restoration rules.

Exact zero Delta is not required if achieving it would violate a more important risk constraint.

## 11. Risk-metric reconciliation

Recent tastylive research changes how the risk engine should treat BPR.

BPR remains a hard capital constraint, but it must not be treated as a standalone loss forecast. A 2024 comparison found that higher-BPR strangles did not automatically produce larger realized losses than lower-BPR iron condors, while 2025 research describes BPR as a useful risk gauge for undefined-risk positions and documents substantial BPR expansion during adverse moves. citeturn0search6turn0search5

Therefore the bot separately tracks:

- current BPR;
- BPR expansion from entry;
- NLV allocation;
- beta-weighted Delta;
- unit/notional exposure;
- correlation;
- defined-risk maximum loss;
- stress scenarios.

This is especially important at $2,000, where a relatively small number of contracts can make a large percentage of the account dependent on one position.

## 12. Hard risk hierarchy

The execution architecture is:

**Research / AI layer → Quantitative regime and opportunity signals → Strategy eligibility → Risk engine → Execution engine**

The risk engine has absolute authority over:

- aggregate BP allocation;
- strategy-type allocation;
- individual sizing;
- per-underlying concentration;
- beta-weighted Delta;
- unit/notional exposure;
- correlation;
- BPR expansion;
- defined-risk maximum loss;
- assignment/expiration safeguards;
- account-level loss controls.

AI cannot bypass these controls.

## 13. Existing positions during regime changes

A regime change does **not** automatically liquidate existing options positions.

When the regime switcher makes the options strategy ineligible for new entries:

- existing positions remain under the options strategy;
- the options strategy's own exit rules continue to govern them;
- the regime signal cannot forcibly close them merely because the preferred regime changed.

Hard portfolio-wide risk controls remain authoritative.

## 14. Backtesting requirements

Before paper trading, test the strategy historically under reproducible assumptions.

Required metrics include:

- total return;
- CAGR where meaningful;
- maximum drawdown;
- Sharpe;
- Sortino;
- volatility;
- time invested;
- trade count;
- turnover;
- win rate;
- average winner/loser;
- profit factor;
- BP utilization;
- maximum BPR expansion;
- assignment/expiration events;
- transaction costs;
- realistic option fills;
- performance by VIX/IVR regime;
- rejected-entry frequency;
- constraint-infeasibility frequency.

Tests must distinguish in-sample development from out-of-sample validation.

## 15. Open questions before implementation

- Whether the historical framework should be used unchanged for the $2,000 paper account.
- Exact broker definition of BPR and how it maps to the historical BP allocation.
- Exact underlying universe.
- Naked versus defined-risk structure eligibility.
- Exact entry frequency.
- Liquidity thresholds.
- Exact aggregate beta-weighted-Delta neutrality band.
- Correlation/stress thresholds.
- Exact 21-DTE behavior by structure.
- Stop-loss policy for undefined-risk positions.
- Assignment and expiration policy.
- Corporate-action handling.
- Whether current 2024–2026 material materially modifies the historical framework.
- Whether the SWITCH-001 regime layer should use VIX allocation directly or combine it with IVR, realized volatility, and market-regime signals.

## 16. Source policy

Primary sources take precedence:

1. official tastytrade documentation;
2. official tastylive research/education;
3. official tastytrade API/backtester documentation;
4. secondary sources only for discovery/context.

No third-party rule becomes authoritative merely because it is widely repeated.
