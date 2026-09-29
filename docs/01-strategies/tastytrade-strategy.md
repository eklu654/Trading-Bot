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


## 2A. Role within SWITCH-001

OPTIONS-001 is not expected to be the portfolio's default state.

The project-level regime hypothesis is:

- **ETF-001 is the primary/default regime** and is expected to hold the portfolio for the majority of normal market conditions.
- **OPTIONS-001 becomes eligible for new risk when the market enters a regime that is unfavorable or less attractive for the leveraged-ETF trend strategy**, particularly sustained sideways/choppy conditions or elevated/turbulent volatility.
- **SWITCH-001 controls eligibility for new options risk**; it does not automatically liquidate existing options positions merely because the preferred regime changes.
- The switch decision must be based on quantitative regime signals rather than a single VIX threshold.

This is a **project-specific architecture rule**, not a claim that tastytrade/tastylive prescribes switching between leveraged ETFs and options.

VIX is treated as a portfolio-level volatility/regime input. Underlying-specific IV/IVR remains a separate trade-level opportunity filter. High VIX or high IV can improve premium-selling opportunity, but does not by itself authorize a trade.

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

## 9. Exit framework — structure-specific research baseline

The research now supports treating exit mechanics as **strategy-specific**, rather than applying a single 50%/21-DTE rule to every options structure.

An official tastylive mechanics guide documents:

| Structure | Winner management | Loss management |
|---|---|---|
| Short strangle | 50% of credit received **or 21 DTE** | May defend by rolling the untested side, rolling out, and/or inverting |
| Iron condor | 50% of credit received **or 21 DTE** | No loss management required because risk is defined |
| Credit spread | 50% of credit received **or 21 DTE** | No loss management required because risk is defined |
| Ratio spread | 30% of max profit | Roll out in time if it moves against the position |
| Broken-wing butterfly | 25% of max profit | No loss management due to defined risk |
| Diagonal | 25% of max profit | Roll near-month option forward if needed |

The same source describes these as mechanics for commonly used strategies, not as a universal rule for all options.

Separate official research supports the 45-DTE/21-DTE pairing for SPY short-premium studies. A 2024 study also found that adjusting DTE with IV can preserve similar daily P/L: 60 DTE in low IVR, 45 DTE generally, and 30 DTE in higher IVR, with 21-DTE exits reducing P/L volatility across tested durations.

For the project, therefore:

- **50% / 21 DTE is not one universal exit rule.**
- The exact exit rule belongs to the structure definition.
- Undefined-risk loss management must be explicitly specified; it cannot be inferred from the defined-risk rules.
- Exit rules must be deterministic and must not be overridden by the AI layer.
- The backtester must test structure-specific management rather than applying one generic exit to all trades.

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


## 10A. Position-sizing research for small accounts

Current tastylive guidance published in 2024 states that defined-risk positions are generally sized at 1–3% of account value for average-sized accounts, while accounts below $20,000 may need to use a higher upper end, including 5–7% or higher in some cases. The same source describes 3–7% as a general undefined-risk range for average-sized accounts and notes that smaller accounts may require an upper bound above 7%. This is source evidence, not an automatic project rule.

For the project's two feasibility cases:

| Account | 1% | 3% | 5% | 7% | 10% | 15% |
|---|---:|---:|---:|---:|---:|---:|
| $2,000 | $20 | $60 | $100 | $140 | $200 | $300 |
| $5,000 | $50 | $150 | $250 | $350 | $500 | $750 |

The project must test the historical sizing bands against actual contract granularity.

For a defined-risk vertical:

`max_loss = (spread_width - credit) × 100 × contracts`

For a multi-leg neutral portfolio, each candidate must also be evaluated for its **incremental** effect on:

- portfolio beta-weighted Delta;
- theta/NLV;
- BPR;
- maximum defined loss;
- underlying concentration;
- correlation concentration;
- expiration concentration;
- stress loss.

A trade that cannot fit the intended risk band at one contract is **infeasible**, not a reason to increase size.

The bot must record the reason for rejection so $2,000 versus $5,000 can be evaluated by constraint-infeasibility rate.


## 10B. Undefined-risk loss management and emergency exits

The project explicitly incorporates the documented tastytrade/tastylive **2× initial-credit loss-management benchmark** for undefined-risk premium-selling positions.

Example:

- initial credit = $1.00/share;
- original credit = $100/contract;
- a 2× credit loss = $200 loss;
- therefore the position's closing cost is approximately $3.00/share more than the original credit, or $4.00/share total buyback value.

This is a **strategy-level management benchmark**, not the only risk control.

The risk engine can close a position before the 2× threshold when a harder portfolio/account constraint is breached.

Defensive rolling is not automatic. If a roll is considered, the resulting position must be re-evaluated from scratch against the same risk controls. A roll cannot be used to evade a position-size, BPR, Delta, concentration, drawdown, or other hard limit.

### Emergency-exit hierarchy

1. **Normal strategy exit** — structure-specific profit/time management.
2. **Strategy loss management** — e.g. 2× initial credit for qualifying undefined-risk positions.
3. **Portfolio risk intervention** — excessive Delta, BPR, concentration, stress exposure, or drawdown.
4. **Hard emergency exit** — immediate risk-engine override when a non-negotiable account or portfolio limit is breached.

Emergency exits are deterministic and cannot be overridden by AI or the regime classifier.

For multi-leg positions, the risk engine must monitor the spread/position itself and generate an appropriate closing multi-leg order; it must not assume that a conventional single-leg stop order protects an entire spread.


## 10C. Portfolio construction: directional positions, balanced portfolio

Individual positions do not need to be Delta-neutral.

The portfolio may construct approximate neutrality by combining independent directional positions across different underlyings, for example:

- bull put credit spread on Underlying A;
- bear call credit spread on Underlying B;
- additional bullish or bearish positions only when they improve portfolio exposure and remain within hard constraints.

The primary standardized directional metric is **SPY beta-weighted Delta**.

Candidate selection therefore evaluates both:

1. **standalone candidate quality**; and
2. **incremental portfolio usefulness**.

A candidate can be rejected even when it is individually attractive if adding it would create excessive directional, volatility, correlation, concentration, or expiration exposure.

The portfolio target is **approximately Delta-balanced**, not necessarily exact zero Delta.

Portfolio construction should consider:

- beta-weighted Delta;
- Delta/theta relationship;
- theta as % of NLV;
- underlying correlation;
- beta exposure;
- vega;
- gamma;
- BPR;
- maximum loss;
- expiration clustering;
- stress scenarios.

## 10D. 0DTE research track

0DTE is now a separate research candidate, not an assumption that the core 45-DTE short-premium strategy should simply be compressed into one trading day.

Primary tastylive research describes materially different 0DTE behavior:

- 0DTE has substantially higher gamma than longer-dated options, with gamma increasing as the session progresses. tastylive's SPY research showed roughly 50x the ATM straddle gamma of a 45-DTE comparison in the cited sample. citeturn1search6
- tastylive research found that adding long wings can reduce capital requirements dramatically for 0DTE positions; its 2023 study reported roughly 80% lower capital requirements for defined-risk versions than comparable undefined-risk positions. citeturn0search2
- A tastylive study comparing entry windows reported that selling 0DTE short strangles near the open and managing after roughly 90 minutes was profitable in the tested sample, while late-day short-premium entries performed poorly; this is research evidence, not a universal trading rule. citeturn0search3
- tastylive's 2025 programming studied multiple 0DTE profit targets, including 10%, 25%, and 50% targets, and later programming continued to examine target selection by IVR. These are research variants rather than a single permanent "tastytrade 0DTE rule." citeturn1search9turn3search0turn3search1
- tastylive's current general DTE guidance still describes approximately 25–50 DTE, with 45 DTE as a common target, for its core short-premium framework. 0DTE is therefore treated as a distinct strategy family rather than a replacement for the core framework. citeturn0search1

### 0DTE project test matrix

The project will test, where the historical data permits:

1. **Defined-risk iron condor**
2. **Defined-risk iron fly**
3. **Defined-risk butterfly**
4. **Defined-risk verticals**
5. **Undefined-risk short strangle as a control only**, not as an assumed production candidate

Each structure will be tested with:
- entry-time delta/expected-move selection;
- realistic bid/ask execution;
- multiple mechanical profit targets (10%, 25%, 50%);
- time-based intraday exits;
- hard maximum-loss controls for defined-risk structures;
- portfolio-level Delta/BPR/concentration limits;
- VIX/IVR stratification;
- opening-window versus later-entry sensitivity;
- event-day exclusions/segmentation where the data supports them.

### Data-quality gate

The repository's current external SPY option dataset is daily-granularity in the existing replay architecture. A genuine 0DTE test of opening-window entries, 90-minute management, late-day behavior, or intraday profit targets requires timestamped intraday quotes/trades.

Therefore:

**No 0DTE profitability number will be generated from the current daily dataset by pretending the daily observation represents an intraday path.**

The workflow now audits the dataset for same-day expirations and timestamp fields. If timestamped data is unavailable, the 0DTE track remains a data-acquisition gate rather than a fabricated backtest.

This distinction is important because 0DTE gamma and execution behavior are strongly time-dependent. citeturn0search3turn1search6

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
- Whether the SWITCH-001 regime layer should use VIX allocation directly or combine it with IVR, realized volatility, trend/chop measurements, and market-regime signals.
- Exact emergency-loss thresholds for each structure beyond the documented 2× undefined-risk benchmark.
- Minimum contract economics and spread-width feasibility at $2,000 versus $5,000.
- Whether expiration staggering materially improves portfolio-level risk versus concentrated 45-DTE entries.
- Exact candidate-ranking function for portfolio usefulness versus standalone trade quality.

## 16. Source policy

Primary sources take precedence:

1. official tastytrade documentation;
2. official tastylive research/education;
3. official tastytrade API/backtester documentation;
4. secondary sources only for discovery/context.

No third-party rule becomes authoritative merely because it is widely repeated.
