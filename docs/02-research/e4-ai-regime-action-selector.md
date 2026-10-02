# E4: AI Regime and Action Selector

## Objective

Test whether a strictly chronological machine-learning policy can improve the
E2 deterministic family/leverage selector while retaining the E3 drawdown
controls where useful.

The project objective is substantial absolute-return improvement versus SPY,
not a small Sharpe improvement. Evaluation therefore includes CAGR, annual
excess returns, rolling excess CAGR, max drawdown, recovery time, downside
risk, turnover/cost sensitivity, and fixed stress periods.

## Initial model

The first AI baseline uses a regularized linear model before tree or sequence
models. Ridge regression is a deliberately simple, deterministic control.

The model predicts forward 20-session returns for each candidate action:
- cash
- SPY 1x / 2x / 3x
- QQQ 1x / 2x / 3x
- SOXX 1x / 2x / 3x

The implementation is `research/backtest_ai_action_selector.py`.
The Ridge regularization parameter is fixed at `alpha=1.0`; no hyperparameter
search is performed.

Features include:
- distance from 20/50/100/150/200-DMA
- 20/60/120/252-session momentum
- 20-session MA slopes
- realized volatility
- VIX level, percentile, and trend
- cross-family relative-strength spreads
- 252-session drawdown

A median imputer and standard scaler are fit inside each training pipeline,
so preprocessing statistics are learned only from the training sample.

## Leakage controls

Every target is strictly forward-looking and every feature is timestamped at
or before the decision close. No centered indicators, same-day return leakage,
future volatility, or future data availability are permitted.

For each prediction year, the model is refit once using an expanding history
through the preceding December 31. Training rows are additionally required to
have their complete 20-session forward target available by that cutoff.

Thus:
- 2020 predictions use data through 2019-12-31
- 2021 predictions use data through 2020-12-31
- 2022 predictions use data through 2021-12-31
- 2023 predictions use data through 2022-12-31
- later predictions continue the same chronological process

The backtest applies the selected action to the next session. A non-cash action
must have a positive predicted 20-session return; otherwise the policy selects
cash. This zero threshold is a predeclared baseline rule, not a tuned holdout
parameter.

## Chronological evaluation

Reporting remains fixed:
- training history: 2010-2019
- validation: 2020-2022
- untouched holdout: 2023 through available 2026 data

The 2010-2019 period is model-training history rather than an out-of-sample AI
performance claim. The first policy performance measurements begin in 2020.
The holdout must not be used to tune features, thresholds, or hyperparameters.

## Decision policy and risk controls

The AI chooses among cash and the nine ETF actions above. This first baseline
does not add discretionary AI sizing: each selected ETF receives 100% of the
portfolio for that session.

The eventual production architecture still requires a hard risk controller
outside the model for leverage, concentration, liquidity, data-quality, broker,
turnover, and emergency constraints. This baseline intentionally keeps that
layer minimal so the experiment measures the predictive/action-selection
question before adding another source of complexity.

## Promotion standard

An AI model is not promoted because it wins one metric or one period. It must
show durable improvement across chronological validation and untouched
holdout data, including meaningful absolute-return improvement versus SPY,
while remaining survivable in 2018, 2020, 2022, and other predefined stress
periods.

A complex model is only justified if it demonstrates incremental out-of-sample
value over the deterministic E2/E3 baselines.

## Current implementation status

The Ridge baseline, unit tests, scikit-learn dependency, and isolated GitHub
Actions workflow are implemented. The workflow rebuilds the historical market
dataset before running the AI backtest and uploads the resulting prediction,
performance, annual-return, and action-frequency artifacts.

The next research gate is empirical: compare the Ridge policy against SPY,
E2 risk-adjusted family selection, and E3 square-root volatility sizing on
validation and holdout. If Ridge has no durable predictive value, the next
step is diagnostic feature/target analysis rather than immediately increasing
model complexity.
