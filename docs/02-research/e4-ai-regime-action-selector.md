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

The first AI baseline should use a regularized linear model before tree or
sequence models. Ridge regression is appropriate as a deliberately simple
baseline because it provides L2 regularization and a deterministic,
interpretable control against which more complex models can be compared.

The model predicts forward 20-session returns for each candidate action:
- cash
- SPY 1x / 2x / 3x
- QQQ 1x / 2x / 3x
- SOXX 1x / 2x / 3x

Features are known at the signal close and include:
- distance from 20/50/100/150/200-DMA
- 20/60/120/252-session momentum
- moving-average slopes
- realized volatility
- VIX level, percentile, and trend
- cross-family relative strength
- drawdown
- breadth-style confirmation where historical data supports it

## Leakage controls

Every target is strictly forward-looking and every feature is timestamped at
or before the decision close. No centered indicators, same-day returns, future
volatility, or future data availability are permitted.

Chronological evaluation is fixed:
- train: 2010-2019
- validation: 2020-2022
- untouched holdout: 2023 through available 2026 data

Model parameters are frozen before holdout evaluation. Validation may be used
for model-selection decisions, but the holdout cannot be used to tune features,
thresholds, or hyperparameters.

## Decision policy

The model's predicted forward returns are compared across actions. A hard
risk controller remains outside the model and can prohibit actions that violate
predeclared leverage, concentration, liquidity, or data-quality limits.

The initial AI experiment should not directly optimize historical CAGR. It
should learn forward action returns, then let the backtester evaluate the
resulting policy.

## Promotion standard

An AI model is not promoted because it wins one metric or one period. It must
show durable improvement across chronological validation and untouched
holdout data, including meaningful absolute-return improvement versus SPY,
while remaining survivable in 2018, 2020, 2022, and other predefined stress
periods.

A complex model is only justified if it demonstrates incremental out-of-sample
value over the deterministic E2/E3 baselines.
