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

## Empirical results: Ridge baseline

The first chronological Ridge implementation completed successfully. It passed
compile and unit tests and used next-session execution timing.

The validation period (2020-2022) produced:
- CAGR: -3.83%
- Sharpe: 0.506
- maximum drawdown: -88.38%
- worst day: -38.59%

The untouched holdout (2023 through 2026-09-25) produced:
- CAGR: 53.27%
- Sharpe: 1.040
- maximum drawdown: -84.25%
- worst day: -18.03%

The model selected 3x actions heavily; SOXX 3x alone represented about 34.5%
of all decision sessions. The large holdout CAGR therefore does not establish
robustness because the validation period was materially weaker and the
drawdown remained extreme.

The Ridge model is **not promoted**.

## Fixed risk-controller diagnostic

Three predeclared overlays were tested without changing the Ridge model:
- SPY 200-DMA gate
- VIX 80th-percentile gate
- both gates together

The combined gate reduced full-period maximum drawdown from about -88.4% to
-68.2%, and reduced the worst day from about -38.6% to -17.0%. Its validation
CAGR was 24.5% with -59.1% maximum drawdown, while its holdout CAGR was 22.2%
with -51.0% maximum drawdown.

The overlay experiment demonstrates that a hard risk controller can materially
change the failure mode, but none of these fixed overlays is being promoted as
the final policy. The holdout remains deeply drawdown-heavy and the controller
was not designed as a tuned solution to the Ridge model.

The stress analysis also shows why a simple trend gate is insufficient by
itself: the AI can remain exposed to severe losses during rapid shocks before
a slow trend signal reacts.

## Empirical results: HGB nonlinear baseline

A second, fixed nonlinear model was tested using
HistGradientBoostingRegressor with predeclared regularization settings. It was
evaluated with the same chronological annual-refit protocol and no holdout
tuning.

Validation (2020-2022):
- CAGR: -3.39%
- Sharpe: 0.476
- maximum drawdown: -82.48%
- worst day: -34.47%

Holdout (2023-2026-09-25):
- CAGR: 82.12%
- Sharpe: 1.195
- maximum drawdown: -77.55%
- worst day: -29.83%

The nonlinear model therefore improves the later-period return substantially,
but it does not fix the validation failure or the catastrophic drawdown
profile. It is **not promoted**.

## Next research direction

The evidence now points away from simply adding model complexity. Both a
regularized linear model and a nonlinear tree model learned raw forward-return
signals that can produce very high leverage exposure and unacceptable
drawdowns.

The next AI experiment should therefore change the **target/decision
objective**, not merely the estimator:
- retain the same leakage-safe chronological feature set;
- predict a risk-aware forward target or multiple forward outcomes;
- explicitly model downside/drawdown risk alongside return;
- keep the hard risk controller outside the learner;
- preserve validation and untouched holdout separation.

Only after a risk-aware objective demonstrates durable validation behavior
should further model complexity be considered.
