# AI Dynamic Leveraged-ETF Decision Maker

Status: Research specification — not production code
Date: 2026-10-02

The eventual AI/ML system is a required research phase, not an optional idea. The deterministic dynamic-leverage benchmark is its control group.

The AI must choose next-session exposure among cash, 1x, 2x and 3x products and select an underlying ETF family, subject to deterministic hard-risk constraints. It may not invent instruments, override safety limits, or use future information.

## Control hierarchy

Every AI candidate must compete against: cash/unleveraged benchmark; existing ETF-001; static 2x; static 3x; deterministic dynamic leverage; deterministic dynamic ETF plus leverage selection; and finally AI/ML selection.

## Feature groups

Candidate inputs include market trend, moving-average distance and slope, momentum, drawdown, VIX level/percentile/trend, realized volatility, breadth, cross-sectional dispersion, relative strength, volatility-adjusted momentum, and—only when historically complete and timestamp-safe—rates, credit spreads, dollar and commodity proxies.

## Action space

The first AI version should use a small discrete action space: family, leverage 0/1/2/3, and bounded allocation. Continuous optimization comes only after the discrete experiment establishes predictive value.

## Deterministic risk controller

The model output must pass through hard limits for single-position weight, family/sector concentration, effective portfolio leverage, liquidity, data quality, broker/account constraints, turnover, and emergency controls. The AI cannot override these controls.

## Learning targets

Do not train directly on cumulative CAGR. First test predictive targets such as forward 5-session return, forward 20-session return, forward downside deviation, drawdown-event probability, and a declared forward risk-adjusted score. A separate policy layer converts forecasts into allocations.

## Walk-forward protocol

Training is strictly chronological. Each walk-forward step trains only on prior data, selects hyperparameters using a validation slice, freezes the model, evaluates the next unseen period, then advances the window. The final holdout remains untouched until the specification is frozen.

## Leakage controls

Prohibit same-day close trading, centered indicators, future volatility, future ETF availability, survivorship-selected universes, post-hoc feature selection from the final holdout, and tuning on stress periods later presented as independent tests. Every signal affecting day t+1 must be constructed only from information available by the close of day t.

## Model progression

Test constant/majority policy, linear or logistic models, regularized tree/boosting models, constrained ensembles, and only then more complex sequence/deep-learning approaches if justified. Prefer the simplest model with durable out-of-sample improvement.

## Ablations

Compare trend-only; volatility-only; trend plus volatility; trend plus volatility plus relative strength; all approved features; and AI versus deterministic equivalents. This identifies whether complexity actually adds information.

## Promotion criteria

Higher CAGR alone is insufficient. Promotion requires durable improvement across a meaningful combination of Sharpe, Sortino, maximum drawdown, Calmar, recovery time, downside deviation, turnover/cost sensitivity, stress-period robustness, and parameter/model perturbation robustness on untouched chronological data.

## Stress periods

Report 2008, 2011, 2015–2016, February 2018, October–December 2018, 2020, 2022, 2023–2024, and the latest available period separately. Pay particular attention to distinguishing short-lived volatility shocks from persistent trend breakdowns.

## Research principle

The AI exists to discover repeatable conditional relationships that simple rules miss. It does not exist to make the backtest look better. If deterministic dynamic leverage performs as well or better out of sample, the deterministic strategy wins on simplicity and auditability. If AI demonstrates persistent cost-adjusted out-of-sample improvement, it becomes the candidate decision layer for later paper trading.
