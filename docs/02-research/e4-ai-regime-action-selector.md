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

## Empirical results: E4c risk-aware target

The next experiment changed the learning objective while keeping Ridge and the
same leakage-safe feature set. Each action target is its forward 20-session
cumulative return divided by the annualized realized volatility of those same
future 20 sessions. The future volatility is used only to construct the
training label.

Validation (2020-2022):
- CAGR: +6.23%
- Sharpe: 0.469
- maximum drawdown: -70.08%
- worst day: -38.59%

Holdout (2023-2026-09-25):
- CAGR: +26.97%
- Sharpe: 1.329
- Sortino: 1.691
- maximum drawdown: -56.79%
- worst day: -9.31%

This is a substantial improvement in robustness over raw-return Ridge and
shows that the objective function matters more than simply increasing model
complexity. However, the result still does not reproduce the large absolute
return edge of the deterministic E2 selector, and drawdown remains much larger
than the E3 square-root sizing benchmark.

E4c is therefore a **promising research candidate, not a promoted final
strategy**. The next comparison should test whether the risk-aware target can
be combined with a bounded action/risk controller without turning into
holdout-driven tuning.

## Fixed leverage-cap and control diagnostics

The E4c risk-aware policy was evaluated with predeclared leverage ceilings:
- 3x ceiling (unmodified E4c)
- 2x ceiling
- 1x ceiling

The 2x ceiling improved validation CAGR from 6.23% to 8.58% and reduced
validation maximum drawdown from -70.1% to -66.7%. Holdout CAGR was 25.88%
with -56.3% maximum drawdown.

The 1x ceiling produced a much lower-risk profile:
- validation CAGR: 11.19%
- validation maximum drawdown: -39.8%
- holdout CAGR: 17.30%
- holdout maximum drawdown: -31.3%
- holdout Sharpe: 1.12
- holdout worst day: -5.85%

Transaction-cost sensitivity remained positive. At 10 basis points per action
change, the 1x policy produced 9.20% validation CAGR and 15.46% holdout CAGR;
the 2x policy produced 5.05% validation CAGR and 23.50% holdout CAGR.

The fixed 200-DMA/VIX controls were also tested on the capped policies. The
combined gates reduced drawdown further, but at a substantial return cost. For
example, the 1x-plus-both-gates policy produced 9.30% validation CAGR and
9.40% holdout CAGR with -21.7% and -29.7% maximum drawdowns respectively.
The 2x-plus-both-gates policy produced 10.66% validation CAGR and 13.34%
holdout CAGR with -35.3% and -41.4% maximum drawdowns.

These results indicate that the risk-aware learner plus a leverage ceiling is
more useful than stacking multiple slow risk gates. The 1x and 2x capped
variants should remain research candidates for deeper rolling/stress analysis,
but neither is promoted as the final strategy yet.

## Current E4 research position

The AI experiments have now tested:
1. raw forward-return Ridge;
2. nonlinear HGB forward-return model;
3. risk-aware forward-return/volatility Ridge;
4. fixed leverage ceilings;
5. fixed 200-DMA and VIX controls;
6. transaction-cost sensitivity.

The strongest evidence so far is that **objective design and bounded leverage
matter more than estimator complexity**. The raw AI models generated enormous
returns in the recent holdout but failed badly in the 2020-2022 validation
period and carried unacceptable drawdowns. The risk-aware objective produced
positive validation performance, and the 1x/2x ceilings materially improved
the stability of that policy.

Before any promotion decision, the next research stage should compare the
capped E4c candidates against E2 and E3 on:
- rolling 3/5/10-year metrics;
- every predefined stress period;
- calendar-year SPY-relative returns;
- recovery time and time underwater;
- turnover and transaction-cost sensitivity;
- parameter/model perturbation;
- an untouched final holdout after the candidate specification is frozen.

No holdout result is being used to tune the leverage ceiling.

## Corrected rolling/annual/stress diagnostics

The capped-policy diagnostics were corrected to use only dates actually covered
by the AI backtest; earlier diagnostic output that implicitly filled 2010-2019
with zero returns was discarded.

For the available 2020-09-25 through 2026-09-25-style common history, both capped
policies trail SPY on rolling windows:
- 1x cap: mean 3-year excess CAGR -6.65%, mean 5-year excess CAGR -5.36%;
- 2x cap: mean 3-year excess CAGR -9.67%, mean 5-year excess CAGR -7.85%.

There are not enough observations for a valid 10-year rolling window because the
AI backtest starts in 2020.

Calendar-year results show both capped policies beating SPY in 2020 and 2021,
underperforming in 2022, 2023, 2024, and 2025, and beating SPY through the
available portion of 2026. Thus the AI cap variants do not currently establish
a durable multi-year return advantage over SPY.

Stress diagnostics:
- 1x cap: COVID -9.84%, maximum drawdown -32.3%; 2022 -29.3%, maximum drawdown
  -39.8%.
- 2x cap: COVID -15.2%, maximum drawdown -51.2%; 2022 -55.5%, maximum drawdown
  -66.6%.

The 1x cap is therefore the materially more controlled AI candidate, but its
rolling relative-return profile is not strong enough for promotion. The 2x cap
retains more upside but still carries severe bear-market exposure.

**Current decision:** E4c remains a research result rather than the production
strategy. The evidence does not justify replacing the deterministic E2 engine
with the current AI selector. Future AI work should therefore focus on using AI
as a meta-regime selector around proven strategy sleeves, rather than asking a
single model to directly choose highly leveraged ETFs every day.

## E5 meta-selector result

E5 changed the AI's role from direct ETF selection to selecting among four
predefined sleeves:
- E2 risk-adjusted dynamic family/leverage selection;
- E3 square-root volatility sizing;
- SPY 1x;
- cash.

The learner used the same chronological Ridge framework and a forward
20-session sleeve return divided by future sleeve volatility as the target.

Results:
- validation CAGR: **11.43%**
- validation maximum drawdown: **-40.6%**
- validation Sharpe: 0.489
- holdout CAGR: **6.42%**
- holdout maximum drawdown: **-62.5%**
- holdout Sharpe: 0.370

The selector spent approximately 65.3% of decision sessions in SPY, 13.1% in
E2, 7.5% in E3-square-root, and 14.2% in cash.

E5 is **not promoted**. Its validation behavior looked materially better than
the direct ETF models, but the holdout result demonstrates that the learned
regime mapping did not generalize. This is exactly why the validation/holdout
separation is being preserved.

## E4/E5 research conclusion

At this stage, the AI experiments have answered an important architectural
question: directly optimizing or selecting leveraged ETF exposure is not
producing a sufficiently stable out-of-sample edge.

The strongest deterministic engine remains E2:
- approximately 24.47% full-period CAGR;
- approximately -62.33% full-period maximum drawdown;
- approximately 39.10% CAGR in the 2023-2026 holdout.

The strongest lower-risk deterministic sizing candidate, E3 square-root,
reduced the drawdown substantially but gave up much of E2's return advantage.

The strongest AI risk-aware capped variant, E4c 1x/2x, produced more controlled
profiles but trailed SPY over rolling relative-return windows. E5 then showed
that a simple AI meta-selector over E2/E3/SPY/cash can still fail to generalize.

**No AI variant is promoted.**

The next phase should therefore not be another unconstrained model search. If
AI development continues, it should be treated as a tightly constrained
overlay around a frozen deterministic baseline, with the baseline's historical
edge preserved and the AI required to demonstrate incremental out-of-sample
value. The next candidate architecture should explicitly ask whether AI can
reduce E2's drawdowns without sacrificing its return engine, rather than asking
AI to discover the entire strategy from scratch.


## E6: binary AI overlay around frozen E2

E6 changes the AI question again. Instead of asking the model to choose a
leveraged ETF or among multiple sleeves, it can make only one binary decision:
**run the frozen deterministic E2 engine or hold cash**.

The E2 engine itself is unchanged. Its family-selection rule, leverage rule,
200-DMA condition, VIX-percentile controls, and underlying ETF choices remain
outside the learner. The learner predicts the E2 sleeve's forward 20-session
return divided by the same period's annualized realized volatility. The
predeclared decision threshold is zero:
- predicted score > 0: E2;
- predicted score <= 0: cash.

Training remains chronological with annual expanding refits and the same
leakage controls used by E4/E5. The first eligible out-of-sample year is 2020;
2020-2022 remains validation and 2023 onward remains the untouched holdout.

This experiment is specifically designed to answer whether AI can **reduce
E2's drawdown by selectively standing aside**, without giving AI permission to
change E2's underlying return engine. The implementation records both the E6
overlay equity curve and an unmodified E2 baseline equity curve on the same
trading dates, allowing incremental value to be measured directly.

E6 is not a promotion by construction. It must demonstrate incremental
out-of-sample benefit versus frozen E2, with particular attention to:
- validation and holdout CAGR;
- maximum drawdown and recovery;
- Sharpe/Sortino;
- time spent in cash;
- turnover between E2 and cash;
- predefined stress periods including 2020 and 2022;
- whether the apparent benefit survives the untouched holdout.

A result that merely lowers drawdown by spending large portions of the period
in cash is not sufficient evidence of an improved return engine. The primary
question is whether the overlay improves the risk/return profile of the
already-established E2 strategy without sacrificing its historical return
character unnecessarily.

No E6 result is promoted until the generated validation and holdout artifacts
have been reviewed.


## E6 empirical result: binary E2-or-cash overlay

The completed E6 walk-forward run does **not** show incremental value over the
frozen E2 engine.

Validation (2020-2022):
- E6 CAGR: -2.58%, Sharpe: 0.110, maximum drawdown: -51.72%.
- Frozen E2 CAGR: +5.96%, Sharpe: 0.356, maximum drawdown: -51.72%.

Untouched holdout (2023-2026-09-25):
- E6 CAGR: +18.32%, Sharpe: 0.595, maximum drawdown: -62.47%.
- Frozen E2 CAGR: +39.10%, Sharpe: 0.863, maximum drawdown: -62.33%.

E6 spent about 42.5% of decision sessions in cash. That reduced exposure, but
it did not improve maximum drawdown in either evaluation period and materially
reduced CAGR and Sharpe.

Stress behavior reinforces the result:
- COVID 2020: E6 returned 0.0% while E2 returned -19.33%.
- 2022 rate-hike period: both E6 and E2 returned -41.77%, with essentially the
  same maximum drawdown and worst day.

The binary overlay is therefore **not promoted**. The experiment provides
evidence against using a generic AI timing layer simply to decide when the
deterministic E2 engine should be switched off.

## E4c fixed-control comparison

The latest fixed-control diagnostics tested the risk-aware E4c Ridge selector
under 1x and 2x leverage ceilings, with optional SPY 200-DMA and VIX
80th-percentile gates. The controls were predeclared rather than fitted to the
holdout.

The raw capped policies remain stronger on return than the gated versions:
- 1x raw: 11.19% validation CAGR / 17.30% holdout CAGR, with -39.82% /
  -31.33% maximum drawdown.
- 2x raw: 8.58% validation CAGR / 25.88% holdout CAGR, with -66.74% /
  -56.33% maximum drawdown.
- 1x + both gates: 9.30% validation CAGR / 9.40% holdout CAGR, with -21.71% /
  -29.72% maximum drawdown.
- 2x + both gates: 10.66% validation CAGR / 13.34% holdout CAGR, with -35.34% /
  -41.37% maximum drawdown.

The 2022 stress period remains particularly informative:
- 1x cap: -29.28% return, -39.82% maximum drawdown.
- 2x cap: -55.52% return, -66.64% maximum drawdown.

The capped AI policies also trail SPY on the available rolling 3- and 5-year
windows. This means the current evidence supports bounded leverage as a useful
risk-control research mechanism, but does not establish an AI return advantage.

## Updated research position

The E6 experiment closes an important hypothesis: **AI has not yet
demonstrated that it can improve E2 merely by deciding between E2 and cash.**
The direct-selector experiments likewise have not demonstrated durable
out-of-sample superiority.

The next AI work should therefore remain incremental and tightly constrained.
A promising question is whether a model can identify a small, explicitly
bounded set of conditions in which reducing E2 exposure adds value, while
leaving E2's underlying engine untouched. Any such overlay must beat the frozen
E2 baseline on both chronological validation and the untouched holdout without
being tuned to those results.
