# E2 — Dynamic ETF Family Selection Research

**Status:** Implemented research experiment — 2026-10-02

## Objective

The E1 deterministic leverage controller tested 0x/1x/2x/3x exposure but did not establish that leverage selection alone can produce the return profile required by this project.

E2 isolates another potential source of alpha: **which market family receives the selected leverage?**

Predeclared families:

- SPY → SSO → SPXL
- QQQ → QLD → TQQQ
- SOXX → USD → SOXL

The leverage controller remains unchanged from E1. Only family selection changes.

## Selection methods

Three transparent, non-optimized methods are tested:

1. **raw_60d** — highest trailing 60-session return.
2. **trend_confirmed** — only families above their own 200-DMA are eligible; among eligible families, choose the highest trailing 60-session return.
3. **risk_adjusted_60d** — trailing 60-session return divided by the family's trailing 20-session annualized volatility.

These are a small hypothesis set, not a sweep of dozens of indicators.

## Required comparisons

Each E2 candidate is compared with SPY 1x, SSO 2x, SPXL 3x, 200-DMA/cash controls, and the existing E1 dynamic leverage control.

## Return hurdle

The project is pursuing substantial absolute return, so E2 reporting includes CAGR versus SPY, calendar-year returns, percentage of years beating SPY, annual excess return, rolling 3/5/10-year excess CAGR, maximum drawdown, recovery, and stress-period behavior.

A small Sharpe improvement with little or no absolute-return improvement is not sufficient evidence of progress.

## Validation

Use the existing chronological boundaries:

- train: 2010–2019;
- validation: 2020–2022;
- holdout: 2023–2026 available data.

No holdout result may be used to change the methods.

## Promotion rule

Do not promote a method merely because it has the highest historical CAGR. Require durable unseen-data improvement versus the E1 control and SPY, plus robustness to costs and execution assumptions.

If deterministic E2 methods do not produce meaningful unseen-data improvement, proceed to richer feature engineering and then the AI selector rather than endlessly tuning deterministic thresholds.
