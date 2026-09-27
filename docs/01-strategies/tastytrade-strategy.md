# Options-Selling Strategy Specification

**Status:** Research draft — not yet frozen for implementation  
**Last reviewed:** 2026-09-27

## 1. Purpose

This document defines the rules for the options-selling strategy used by the project.

The strategy is intended to model a disciplined, rules-based short-premium approach informed by current tastytrade/tastylive educational material. It separates:

1. **Verified methodology** — supported by primary tastytrade/tastylive documentation.
2. **Project interpretation** — how source material is translated into system behavior.
3. **Project-specific rules** — choices made for this bot that are not claimed to be universal tastytrade rules.
4. **Open research questions** — items requiring verification before the strategy is frozen.

A project rule must never be presented as an official tastytrade rule unless the source establishes it.

## 2. Portfolio objective

The strategy seeks to systematically sell option premium while controlling buying-power usage, directional exposure, concentration, volatility-driven margin expansion, tail risk, time-to-expiration risk, and execution risk.

The strategy is intended to be managed mechanically. AI may help identify eligible opportunities, but it cannot override hard entry, sizing, risk, or exit rules.

## 3. Verified methodology — current research baseline

Current tastytrade/tastylive materials and the official tastytrade backtester document mechanics including option selection by delta, defined DTE ranges, entry conditions, VIX-based entry filters, take-profit conditions, stop-loss conditions, maximum days in trade, DTE-based exits, and strategy legs.

Research examples commonly use approximately **45 DTE** entries, relatively low short-strike deltas such as **16 delta**, and management around **50% of maximum profit** and/or approximately **21 DTE**. These values are treated here as a research baseline, not as an assertion that every tastytrade strategy universally uses identical parameters.

Each parameter must be verified against the specific current source before the strategy is frozen.

## 4. Portfolio-level directional exposure

The project intends to maintain a substantially delta-balanced portfolio rather than making an uncontrolled directional bet.

Both bullish and bearish option structures may be held simultaneously.

Before coding, define:

- whether delta is measured raw or beta-weighted;
- the benchmark for beta weighting, if used;
- the permitted aggregate-delta band;
- whether individual positions have delta limits;
- how correlation between underlyings is handled; and
- how the system behaves when neutrality cannot be restored without violating position-size or buying-power limits.

The bot must not assume exact zero delta is always achievable.

## 5. Position sizing

### Project requirement

The preferred position size is approximately **1–3% of account buying power** per position.

For accounts below $10,000, the project permits a controlled exception because whole option contracts create granularity. The current working proposal is that a position may exceed the preferred range, with an approximate **5–7% upper working range**.

This is a **project-specific rule**, not currently claimed as an official universal tastytrade position-size rule.

The final specification must define whether the percentage is measured against net liquidation value, available buying power, total buying power, or a strategy-specific risk budget.

## 6. Volatility and VIX allocation

The project's core hypothesis is that higher implied volatility can provide richer option premiums and can therefore justify allocating more risk budget to systematic premium selling, while recognizing that high volatility can also increase losses and buying-power requirements.

A current authoritative numerical VIX-to-buying-power schedule has **not yet been established**.

> No numerical VIX allocation table is authoritative at this stage.

Any schedule used during research or backtesting must be explicitly labeled a project hypothesis and tested rather than presented as a tastytrade rule.

## 7. Entry framework — provisional

The working research baseline is:

- prefer liquid underlyings;
- prefer approximately 45 DTE for core positions;
- consider approximately 16-delta short strikes for low-delta premium structures;
- require sufficient implied-volatility opportunity;
- respect portfolio-level delta constraints;
- respect buying-power allocation;
- reject trades that create excessive concentration or correlated exposure.

These are provisional until source research is reconciled into a final strategy specification.

## 8. Exit framework — provisional

The strategy will use deterministic exits.

The current research baseline includes:

- profit-taking around 50% of maximum profit;
- management/exit around 21 DTE where applicable;
- additional strategy-specific exits where required;
- no AI discretionary override.

The exact interaction between profit target, DTE, stop loss, expiration, assignment, and portfolio-risk exits must be defined before implementation.

## 9. Existing positions during regime changes

A regime change does **not** automatically liquidate existing options positions.

When the regime switcher determines that the options strategy is no longer eligible for new entries:

- existing positions remain under the options strategy;
- the options strategy's own exit rules continue to govern them;
- no AI-generated regime signal may forcibly close them merely because the preferred regime changed.

Hard portfolio-wide risk controls remain authoritative.

## 10. Small-account constraints

Initial paper testing uses a $2,000 account per strategy instance.

This creates important implementation constraints:

- whole-contract sizing;
- potentially large percentage exposure from a single contract;
- limited ability to maintain perfect delta neutrality;
- substantial buying-power impact from some naked options;
- possible inability to diversify normally.

The backtester must report when an ideal trade cannot be executed because of account-size constraints rather than silently relaxing the rules.

## 11. Hard risk hierarchy

The execution architecture is:

**Research / AI layer → Quantitative regime and opportunity signals → Strategy eligibility → Risk engine → Execution engine**

The risk engine has absolute authority over maximum position size, aggregate buying-power allocation, portfolio exposure, delta limits, concentration, prohibited trades, expiration/assignment safeguards, and account-level loss controls.

AI cannot bypass these controls.

## 12. Backtesting requirements

Before paper trading, this strategy must be tested historically under reproducible assumptions.

Required metrics include:

- total return;
- CAGR where meaningful;
- maximum drawdown;
- Sharpe ratio;
- Sortino ratio;
- volatility;
- time invested;
- time in cash;
- trade count;
- turnover;
- win rate;
- average winner/loser;
- profit factor;
- buying-power utilization;
- maximum buying-power expansion;
- assignment/expiration events;
- transaction costs;
- realistic option fill assumptions; and
- performance by volatility regime.

The test must distinguish in-sample development from out-of-sample validation.

## 13. Source policy

Primary sources take precedence:

1. official tastytrade documentation;
2. official tastylive research/education;
3. official tastytrade API/backtester documentation;
4. secondary sources only for discovery or contextual comparison.

No third-party rule becomes authoritative merely because it is widely repeated.

## 14. Open questions before implementation

- Exact current VIX-to-buying-power allocation schedule, if tastytrade publishes one.
- Exact definition of portfolio delta neutrality.
- Underlying universe.
- Naked versus defined-risk option structures.
- Exact entry frequency.
- Exact liquidity thresholds.
- Exact stop-loss policy.
- Exact 21-DTE behavior by strategy type.
- Assignment and expiration policy.
- Treatment of dividends, corporate actions, and early assignment.
- Exact small-account sizing exception.
