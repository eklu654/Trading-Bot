# Leveraged ETF Research Findings — 2026-10-03

## Completed runs
- Historical ETF workflow run #287 (37108741706, commit 68d59d33b9c2f061dc5720f6502569766b9134bb) completed successfully through ETF-007 and the existing downstream analyses.
- ETF-007 was added specifically as an oracle diagnostic to determine whether directional timing is the main bottleneck.

## ETF-002 directional rotation
The 200-DMA bull/bear directional rotation was not robust across chronological splits.

| Top N | Train annualized | Validation annualized | Holdout annualized | Validation max DD | Holdout max DD |
|---:|---:|---:|---:|---:|---:|
| 1 | -4.27% | -6.54% | 10.87% | -62.21% | -69.99% |
| 2 | 1.62% | -4.39% | 17.33% | -58.11% | -56.94% |
| 3 | 2.21% | -6.21% | 22.73% | -59.27% | -45.88% |
| 5 | 1.53% | -10.54% | 14.72% | -57.12% | -42.69% |

This argues against making the current inverse-side switching rule the primary replacement for cash.

## ETF-003 bull-only / Dow pivot
Replacing TQQQ with UDOW in the fixed three-sleeve structure reduced annualized returns in all three chronological splits tested:

| Strategy | Train | Validation | Holdout |
|---|---:|---:|---:|
| Existing TQQQ/SPXL/SOXL | 22.08% | 14.49% | 50.65% |
| UDOW/SPXL/SOXL | 20.32% | 7.89% | 37.15% |

UDOW remains a valid future bull-only candidate, but the fixed substitution did not improve the tested baseline.

## ETF-004 cash versus bear-side fallback
The initial test used immediate exit below the 200-DMA and five consecutive sessions above the 200-DMA for bull re-entry. Each sleeve either stayed cash or used its corresponding bear ETF; the same-underlying bull and bear sides were never held simultaneously.

| Fallback | Train ann. | Validation ann. | Holdout ann. | Validation max DD | Holdout max DD |
|---|---:|---:|---:|---:|---:|
| Cash | 22.47% | 23.68% | 43.85% | -37.66% | -35.68% |
| Bear ETF | 2.52% | 4.32% | 12.16% | -61.23% | -56.06% |

This shows the tested switching rule favored cash; it does not establish that a better directional signal could not make inverse ETFs useful.

## ETF-005 transaction-cost sensitivity
The corrected cost replay compared the baseline 200-DMA/5-session rule with the locally robust 200-DMA / 2% exit buffer / 1% re-entry buffer / 5-session rule.

The robust candidate had total turnover of 3.75x during validation and 10.25x during holdout. At 0 bps assumed cost its annualized returns were 18.37% validation and 28.20% holdout. At 50 bps per unit turnover they were 17.63% and 26.44%, respectively.

## ETF-006 inverse timing grid
Searching exit confirmation, re-entry confirmation, and DMA buffers materially changed inverse results by period. The best tested validation configuration was approximately 12.34% annualized, while the best holdout configuration reached approximately 41.70% annualized. The winning settings differed materially between validation and holdout, which is evidence against treating one timing configuration as established.

## ETF-007 oracle timing diagnostic
ETF-007 intentionally uses next-day returns and therefore is impossible as a live strategy. Its purpose is to measure the theoretical headroom available if directional timing were perfect.

| Strategy | Train ann. | Validation ann. | Holdout ann. |
|---|---:|---:|---:|
| Oracle: bull vs inverse vs cash | 105.22% | 2381.16% | 422.01% |
| Bull-only oracle: bull vs cash | 11.47% | 55.11% | 27.03% |

The enormous gap between these hindsight upper bounds and the ordinary signal strategies is the strongest evidence so far that timing/regime identification is a major research bottleneck. The oracle is not a candidate strategy and must not be used for live selection.

The result also changes the research framing: we should not conclude that inverse ETFs are inherently unhelpful merely because the first 200-DMA switch underperformed cash. There is demonstrable downside opportunity in hindsight; the unresolved question is how much of it can be captured ex ante without excessive false signals, turnover, or inverse-ETF path-dependence losses.

## Research-integrity correction
The original ETF-001 matrix split evaluator used cumulative full-history portfolio_value when calculating validation/holdout annualized returns. Those earlier matrix validation/holdout annualized figures are not reliable for candidate selection.

The matrix generator has now been corrected in commit 0b360bf8ef66914dffce7bf47c277c7dd47158ed to independently rebase portfolio_value and recompute split drawdown before calculating split metrics. The corrected matrix must be rerun before any parameter is promoted.

## Current direction
1. Rerun the corrected ETF-001 matrix and downstream robustness evaluation.
2. Use only training/validation results from the corrected split calculations for candidate selection; keep holdout untouched until selection is frozen.
3. Test realistic transaction costs and turnover on candidates that survive corrected validation.
4. Build the next directional-signal research around interpretable, ex-ante features: 200-DMA distance, 200-DMA slope, 50/200-DMA relationship, 20/60-day momentum, persistence below trend, cross-market confirmation, and volatility/VIX.
5. Compare the same signal's choices of cash vs inverse exposure rather than comparing unrelated switching rules.
6. Test partial defensive exposure as well as all-or-nothing switching.
7. Only after a candidate survives chronological validation and realistic costs should it become a paper-trading candidate.


## ETF-008 through ETF-010 directional signal research
Three ex-ante signal families were tested chronologically:
- ETF-008 frozen next-day logistic classifier: best validation annualized return about 5.30%, with roughly -58.6% max drawdown.
- ETF-009 frozen multi-horizon classifier: best validation annualized return about 2.35%, with roughly -46.2% max drawdown. Stronger holdout configurations that failed validation were treated as overfit.
- ETF-010 rare-event bear gate: best validation configuration produced about 15.62% annualized return, Sharpe about 0.55, and -48.7% max drawdown.

ETF-010 was the most useful of these signal families because it attempts to identify coordinated deterioration rather than predict every daily return, but it did not beat the corrected ETF-001 baseline.

## ETF-011 partial inverse overlay
ETF-011 kept the normal 200-DMA/5-session bull logic and applied the ETF-010 bear gate only while a sleeve was otherwise defensive. It tested 25%, 50%, 75%, and 100% inverse allocation within each 25% sleeve.

The corrected baseline in this replay was:
- Train: 22.47% annualized, Sharpe 0.897, max DD -29.77%
- Validation: 23.68% annualized, Sharpe 0.745, max DD -37.66%
- Holdout: 43.85% annualized, Sharpe 1.090, max DD -35.68%

The best validation overlay used only 25% of each defensive sleeve for inverse exposure and still reduced validation annualized return to about 23.22% and Sharpe to about 0.731. No partial-inverse configuration beat the baseline on validation Sharpe.

Conclusion: partial inverse exposure did not solve the defensive-side timing problem.

## ETF-012 early bear override
ETF-012 allowed the rare-event bear gate to override the bull state before a 200-DMA exit, testing whether earlier downside positioning could capture more of a decline.

The best validation configuration used:
- 25% of each sleeve in inverse exposure
- bear score threshold 3
- 1-session confirmation
- VIX percentile threshold 0.80
- breadth threshold 0.33

Validation improved to approximately:
- 26.96% annualized return
- Sharpe 0.804
- max DD -35.73%

This was a meaningful validation improvement over the 23.68% / 0.745 baseline. However, the exact validation-selected configuration produced only about 34.32% annualized return and Sharpe about 0.936 in the 2023+ holdout, versus the baseline's 43.85% and 1.090.

Conclusion: early bear override shows real timing potential in one historical validation regime but failed the chronological holdout gate and is not a paper-trading candidate.

## ETF-013 absolute-VIX early bear override
ETF-013 replaced rolling VIX percentiles with absolute VIX thresholds of 20, 22, 25, 28, 30, and 32.

The best validation configuration was still below the baseline: about 21.93% annualized and Sharpe 0.698 versus 23.68% and 0.745. No absolute-VIX configuration established a robust improvement.

Conclusion: the improvement seen in ETF-012 was not reproduced by simply making the volatility threshold more interpretable.

## ETF-014 inverse-instrument leverage grid
ETF-014 tested whether 3x inverse products were the structural problem by comparing:
- 3X: SQQQ / SPXS / SOXS
- 2X: QID / SDS / SSG
- LOW: PSQ / SH / SSG

ProShares documents PSQ as -1x, QID/SDS as -2x, while SOXS is -3x and SSG is -2x. The semiconductor hedge is not perfectly benchmark-matched in the LOW profile because SSG tracks the Dow Jones U.S. Semiconductors Index rather than SOXX's exact benchmark.

The best validation result was the LOW profile with 50% sleeve allocation, score 3, one-session confirmation, VIX percentile 0.80, and breadth threshold 0.33:
- Validation: 26.08% annualized, Sharpe 0.788, max DD -36.59%

But its holdout result fell to roughly 32.03% annualized and Sharpe 0.894, below the baseline's 43.85% and 1.090.

Conclusion: reducing inverse leverage improves some validation risk-adjusted results, but the chronological holdout still rejects the signal/instrument combination.

## Current conclusion on inverse ETFs
The research now covers:
1. Basic 200-DMA cash vs inverse switching.
2. Inverse timing confirmation grids.
3. Partial inverse exposure.
4. Early bear overrides before the 200-DMA exit.
5. Absolute-VIX versions of the early override.
6. Lower-leverage inverse instruments.

None has yet produced a robust validation-to-holdout improvement over the corrected cash-based ETF-001 baseline. The research therefore should **not** promote inverse ETFs to the core strategy yet.

This does not prove inverse ETFs can never add value. The ETF-007 oracle shows that perfect downside timing contains enormous theoretical opportunity. It does show that the currently tested ex-ante signals have not captured enough of that opportunity robustly.

## Workflow/runtime architecture
The expensive options replay pipeline remains separated into manual-only `.github/workflows/options-research.yml`. ETF signal experiments run through the much faster `.github/workflows/etf-signal-research.yml`.

The historical ETF workflow was narrowed to explicit core-research paths so signal-only changes do not launch the full historical suite. This matters because the long historical workflow and AI/dynamic workflows can otherwise overlap and waste Actions time.

## Next research priority
The next useful direction is no longer "try another arbitrary inverse timing grid." The strongest remaining question is whether the portfolio can improve risk-adjusted returns by **better selecting the bull-side exposure itself** while retaining cash as the default defensive state.

Candidate directions:
- robust multi-asset/sector bull selection with strict validation,
- volatility-aware sizing of the existing bull sleeves,
- bull-side momentum/trend confirmation that is simpler and more stable than daily directional classification,
- regime-conditioned selection of which leveraged bull ETF deserves capital,
- and only then revisiting a defensive inverse sleeve if a signal survives a true chronological holdout.

No candidate becomes a paper-trading strategy until it survives validation, holdout, transaction-cost analysis, and account-level execution feasibility.


## ETF-017 canonical accounting correction
A research-integrity audit found that ETF-011 through ETF-014 used a separate replay/accounting path from canonical ETF-001. Their exploratory results should therefore not be used as promotion evidence.

ETF-001/ETF-005 canonical accounting gives the current baseline approximately:
- Train: 18.18% annualized, Sharpe 0.794, max DD -37.35%
- Validation: 20.18% annualized, Sharpe 0.708, max DD -32.82%
- Holdout: 24.18% annualized, Sharpe 0.779, max DD -36.99%

ETF-017 rebuilt the most promising ETF-012 early-bear override using the canonical accounting: common bull-underlying calendar, adjusted-close total returns, next-session execution, 25% sleeves, and 25% permanent cash.

The best validation configuration was:
- 25% of each sleeve in inverse exposure
- bear score 6
- one-session confirmation
- VIX percentile 0.60
- breadth threshold 0.33

It produced:
- Validation: 19.40% annualized, Sharpe 0.681, max DD -36.50%
- Baseline: 20.18% annualized, Sharpe 0.708, max DD -32.82%

The validation-selected configuration therefore failed to improve either return or Sharpe. The corresponding holdout result was about 23.24% annualized and Sharpe 0.756 versus the baseline's 24.18% and 0.779.

ETF-017 is now the authoritative inverse-overlay result. The earlier ETF-011–014 headline improvements are retained only as exploratory diagnostics and must not be cited as evidence that inverse exposure works.

## ETF-015 / ETF-016 bull-side selection
ETF-015 tested raw and volatility-adjusted momentum across TQQQ, SPXL, SOXL, UDOW, and TNA. The best validation-only configuration reached about 33.30% annualized and Sharpe 0.874, but its validation-selected holdout fell to about 40.44% annualized and Sharpe 0.992, below the canonical ETF-001/ETF-005 holdout baseline.

ETF-016 added a stricter consistency gate requiring a candidate to beat the baseline Sharpe on both training and validation before it could be frozen. **No candidate passed both gates.** No holdout result was therefore accepted as a selected strategy.

This is useful evidence against repeatedly searching a large parameter grid and selecting the single best validation winner: the strongest-looking validation configurations can still fail the next period. Time-ordered walk-forward/holdout discipline is therefore being tightened rather than relaxed.

## Current strategy-research status
The current evidence does not support promoting:
- inverse ETF switching,
- partial inverse exposure,
- early bear overrides,
- lower-leverage inverse substitutes,
- or the tested bull momentum rotation variants.

The strongest defensible baseline remains the canonical ETF-001 family with cash as the default defensive state, pending further bull-side research and cost/robustness validation.

The next experiments should use the canonical accounting framework from the start. No exploratory replay with a different portfolio ledger should be used to select a production strategy.


## ETF-018 multi-signal bearish transition

ETF-018 directly tested the hypothesis that the inverse-ETF problem is primarily a signal problem rather than an instrument problem. It combined interpretable ex-ante signal families:
- trend: price vs 200-DMA, 200-DMA slope, and 50/200-DMA relationship;
- MACD: bearish line relationship, negative histogram, and histogram deterioration;
- channels: prior 20/40/60-session Donchian breakdowns;
- momentum: 20/60-session returns;
- volatility: VIX percentile and 5-session change;
- breadth: weakness across QQQ/SPY/SOXX/DIA/IWM.

It also tested hysteresis, confirmation, and 25/50/75/100% inverse sleeve allocation. The same-underlying bull/bear exclusivity rule is enforced: an inverse position replaces that underlying's bull sleeve rather than coexisting with it.

The first canonical run completed successfully. It produced a materially stronger validation result than ETF-017, which confirms that the richer signal collection is worth investigating further, but the improvement did not survive the 2023+ holdout.

The validation leader was the full signal family with threshold 0.60, one-session confirmation, release threshold 0.40, and 25% inverse allocation:
- Validation: **36.21% annualized, Sharpe 1.047, max DD -22.65%**
- Canonical baseline: **20.18% annualized, Sharpe 0.708, max DD -32.82%**

The exact validation-selected configuration then produced in holdout:
- **16.44% annualized, Sharpe 0.602, max DD -39.38%**
- Canonical baseline: **24.18% annualized, Sharpe 0.779, max DD -36.99%**

Other validation leaders also failed to beat the holdout baseline. For example, the trend_macd_channel configuration at threshold 0.70 / confirmation 3 / release 0.40 / 75% inverse produced 21.09% annualized and Sharpe 0.708 in holdout, versus 24.18% and 0.779 for the baseline.

Interpretation: **MACD + channel information appears capable of improving the timing signal in some historical periods, but the first composite implementation is not robust enough to promote.** This is stronger evidence for continuing signal research than the earlier simple 200-DMA inverse tests, while still rejecting the tested configuration as a paper-trading candidate.

The most important next refinement is therefore not another large blind parameter grid. It should examine which signal arrives first and whether that sequence consistently precedes sustained bearish periods: channel breakdown, MACD histogram deterioration/cross, momentum deterioration, breadth confirmation, VIX expansion, and eventual 200-DMA loss. Lead-time, false-trigger, and regime-by-regime diagnostics should be added before another selection grid.

ETF-018 also exposed a runtime optimization opportunity. Its workflow now uses a lightweight data bootstrap containing only the 11 required ETFs/underlyings plus VIX instead of rebuilding the full historical research universe. This keeps focused signal experiments isolated from the slower full historical pipeline.


## ETF-020 supervised technical-indicator synthesis

The research is now moving from hand-authored indicator combinations toward a bounded machine-learning experiment. The motivation is the user's hypothesis that the inverse transition may require a large collection of weak technical signals whose interactions are difficult to encode manually.

ETF-020 builds a broad ex-ante feature library across QQQ, SPY, SOXX, DIA, and IWM, including:
- moving-average distance and slope across multiple horizons;
- ROC/momentum across short, medium, and long horizons;
- RSI;
- multiple MACD parameterizations and histogram slope;
- Bollinger-style channel position, width, and lower-band breaks;
- Donchian channel position, lower-channel breaks, and drawdown from recent highs;
- ATR-normalized movement and volatility;
- stochastic oscillators;
- ADX and directional-index spread;
- volume/OBV-derived features where available;
- VIX level, changes, z-scores, and rolling ranks;
- cross-market breadth and dispersion features.

The model is a deliberately small set of fixed HistGradientBoostingClassifier architectures rather than a massive hyperparameter search. It is trained only on 2010-2019 data. Validation (2020-2022) chooses the probability threshold and inverse allocation fraction; the 2023+ holdout is then inspected without using it for model selection.

The target is a forward 20-session coordinated-market decline of at least 4% in the equal-weight QQQ/SPY/SOXX benchmark. This is a research target, not a claim that the model can forecast prices reliably.

This architecture is important because it tests the user's core hypothesis directly: whether an AI model can synthesize many interacting indicators more effectively than a manually weighted score. It also protects against the most obvious failure mode of this approach—finding an apparently brilliant combination by searching the holdout period.

ETF-020 uses the canonical ETF-001 portfolio ledger and preserves the same-underlying exclusivity rule: when the model activates the defensive side, the corresponding bull sleeve is removed before any inverse exposure is applied.

A lightweight ETF-020 data bootstrap was added so this experiment does not rebuild the entire historical research universe. The focused workflow is therefore isolated from the slower full historical/options pipelines.

The experiment is not yet a paper-trading candidate. A model would need to demonstrate chronological robustness, realistic transaction-cost resilience, stable behavior across market regimes, and account-level execution feasibility before being considered for paper trading.


## ETF-021 multi-horizon ML diagnostics

ETF-021 tested whether the broad ETF-020 indicator library has predictive information at several fixed bearish horizons. The targets were specified in advance as:
- 5 sessions: benchmark decline of at least 2%;
- 10 sessions: at least 3%;
- 20 sessions: at least 4%;
- 40 sessions: at least 6%.

Both fixed HistGradientBoosting models fit the 2010-2019 training period extremely well but lost that separation out of sample. Validation ROC-AUC was approximately 0.39-0.52 across the targets/models, and the 20-session target was below 0.50 for both models. This is important evidence that simply expanding the indicator library and freezing a nonlinear model does not solve the regime-transition problem.

The holdout results were mixed: the 40-session target reached ROC-AUC about 0.73-0.76 in 2023+, while the shorter horizons remained close to chance. Because this holdout strength was not present in validation, it is not treated as a selected signal. The clean conclusion is that the static model is unstable across regimes and should not be promoted.

## ETF-022 walk-forward ML adaptation

ETF-022 tested the next logical hypothesis: perhaps the indicator relationships are non-stationary, so the model must periodically retrain using only information available before each prediction. A fixed shallow HistGradientBoosting model was retrained every 63 trading sessions using an expanding historical training set. The 20-session / -4% target and model architecture were fixed in advance.

Walk-forward predictive diagnostics improved validation ROC-AUC to **0.596**, but holdout ROC-AUC was only **0.516**. Portfolio selection on validation chose a 0.60 probability threshold and 100% inverse allocation within the affected 25% sleeves. That produced:
- Validation: **21.36% annualized, Sharpe 0.736, max DD -32.82%**
- Baseline: **20.18%, Sharpe 0.708, max DD -32.82%**
- Holdout: **25.14% annualized, Sharpe 0.801, max DD -36.99%**
- Baseline holdout: **24.18%, Sharpe 0.779, max DD -36.99%**

However, the model activated on only **1 validation day and 3 holdout days** at the selected threshold. The small number of activations means the apparent portfolio improvement could be driven by a handful of observations rather than a durable predictive edge. It is therefore **not a paper-trading candidate** yet.

Interpretation: walk-forward retraining is more interesting than the frozen ETF-020 model, but the current evidence still does not establish a robust inverse signal. The next test should stress retraining cadence, event attribution, and transaction costs rather than immediately increasing model complexity or searching a large parameter space.


## ETF-023 walk-forward cadence sensitivity

ETF-023 tested retraining every 21, 63, or 126 trading sessions with fixed probability thresholds. The validation-selected configuration remained the **63-session cadence / 0.60 threshold**, with 1 inverse activation day:
- Validation: **21.36% annualized, Sharpe 0.736**
- Baseline: **20.18%, Sharpe 0.708**
- Holdout: **25.14% annualized, Sharpe 0.801**
- Baseline holdout: **24.18%, Sharpe 0.779**

The 21-session cadence produced a separate validation configuration at 0.65 with 6 activation days and Sharpe 0.730, while the 126-session cadence produced no activation at the tested thresholds. The selected 63-session result therefore was not uniquely supported by a broad cadence improvement.

Event attribution also shows why the result must be treated cautiously. The selected model triggered on the 2022-12-28 session, which was a false positive for the following 20-session benchmark return (+11.79%). In the 2023+ holdout it triggered a three-session cluster on July 9-11, 2024; those sessions were followed by benchmark 20-session returns of approximately -11.15%, -13.31%, and -8.69%. The apparent holdout benefit is therefore concentrated in a very small number of events.

Conclusion: walk-forward retraining remains a legitimate research direction, but the current inverse edge is too sparse to promote. The next promotion gate should require robustness across more bearish events and realistic transaction costs, not simply another small threshold/cadence grid.
