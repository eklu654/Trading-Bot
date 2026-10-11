# Frozen Family-Selector Attribution Audit — Preregistration (2026-10-11)

## Question
Why does the frozen DMA-250/top-2/5-session family rotation retain high drawdown despite excluding families whose benchmarks are below their 250-session moving averages? This is a diagnostic audit of the existing control, not a new strategy search.

## Frozen control
- Families: SPXL/SPY, TQQQ/QQQ, SOXL/SOXX, UDOW/DIA, TNA/IWM.
- Eligible when the prior close of the benchmark is at or above its prior-close 250-session moving average.
- Rank eligible families by benchmark distance above that moving average; equally weight the top two.
- Rebalance every five aligned sessions; long leveraged ETFs or cash only.
- Starting equity $5,000; use the shared aligned ETF return panel and the previously documented 25 bps turnover cost for headline diagnostics.
- Actual family history only, 2010-03-12 through 2026-10-02. No pre-inception leveraged ETF backfill.

## Diagnostics, fixed before inspecting results
1. Full/train/validation/holdout exposure, family weight share, positive and negative additive family contribution, turnover, ending equity and max drawdown.
2. The 12 deepest non-overlapping peak-to-trough drawdown episodes, with peak/trough/recovery dates, family weights and additive return contributions during drawdown, plus the next 63 sessions after trough.
3. The 100 deepest portfolio drawdown sessions, with contemporaneous selected weights, family returns, family contribution, gross/net portfolio return, and turnover.
4. Verify weights are nonnegative, total exposure is at most 100%, and all return/weight axes align. The diagnostic must not alter strategy weights or thresholds.

## Interpretation guardrails
- Additive weighted daily return contribution is attribution, not a separately compounded counterfactual portfolio.
- A family being the largest dollar-loss contributor can reflect its portfolio weight, its underlying return, or both; do not call that evidence of predictive value.
- A 63-session recovery window is a descriptive horizon, not a tuned exit/re-entry parameter.
- Do not use these diagnostics to tune DMA length, top-N, rebalance cadence, or family caps. If results motivate a new architecture, preregister it separately before any performance run.
- Keep the 2000-2002 episode as a distinct synthetic daily-reset stress study, not part of the actual ETF history.

## Outputs
The workflow writes selector_audit_summary.csv, selector_audit_worst_drawdowns.csv, selector_audit_daily_weights.csv, selector_audit_daily_family_contributions.csv, selector_audit_worst_100_days.csv, and a SHA-256 manifest. Workflow success and test results must be recorded in the follow-up report.
