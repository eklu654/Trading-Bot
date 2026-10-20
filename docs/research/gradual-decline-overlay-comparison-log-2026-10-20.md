# Gradual-decline overlay comparison — research log

Updated: 2026-10-20 UTC (review pass 3)
Status: first-pass historical comparison completed; results are preliminary and NOT promotion-ready.

## Goal
Test whether simple trend overlays improve terminal account value versus the frozen B0 shock/recovery control, especially in slow declines where QQQ never falls 4.5% in one session. B0 and F75 production/paper rules remain unchanged. This is a separate, read-only research experiment.

## Artifacts
- Script: `research/backtests/gradual_decline_overlay_comparison.py`
- Deterministic tests: `research/backtests/test_gradual_decline_overlay_comparison.py`
- Workflow: `.github/workflows/gradual-decline-overlay-comparison.yml`
- Completed run: https://github.com/eklu654/Trading-Bot/actions/runs/39371734489
- Results artifact: https://github.com/eklu654/Trading-Bot/actions/runs/39371734489/artifacts/12242020453 (30-day retention)
- Research workflow run succeeded: syntax check, both deterministic tests, historical comparison, and artifact upload all passed.

## First-pass results (run 39371734489)
Period: 2010-10-07 through 2026-10-19, 4,032 overlapping daily sessions. Initial capital $5,000.

| Variant | Final equity | Return | Max drawdown | Invested days | Position changes |
|---|---:|---:|---:|---:|---:|
| B0 shock/recovery reconstruction | $2,418,101.46 | 48,262.03% | -73.64% | 93.20% | 18 |
| B0 + QQQ 100-DMA | $66,444.30 | 1,228.89% | -57.97% | 76.64% | 179 |
| B0 + QQQ 200-DMA | $408,893.70 | 8,077.87% | -60.07% | 82.61% | 84 |
| B0 + QQQ 60-session return | $84,079.83 | 1,581.60% | -49.32% | 73.78% | 174 |

## Interpretation
- None of the three trend overlays beats this reconstructed control on terminal equity. By the user's required criterion, none qualifies as a successful defense in this run.
- The 60-session rule has the lowest reported drawdown, but terminal equity is dramatically lower; this is explicitly NOT success under the project's promotion rule.
- The 100-DMA and 60-session rules generate many more position changes, indicating meaningful whipsaw/re-entry risk.
- The control ends at ~$2.418M, not the earlier reported ~$4.04M B0 figure. This is a major reconciliation gap. These results cannot be described as validated B0 comparisons until the frozen B0 rules, data series, adjustments, execution assumptions, and daily equity curve are reconciled.
- These are first-pass full-period numbers only. Do not select or tune parameters on this entire sample and then claim out-of-sample validation.

## Rules and assumptions
- Control reconstruction: QQQ close-to-close loss of 4.5% or worse latches an exit; re-entry is signaled after QQQ closes 10% above the post-trigger low.
- Candidate A: control plus QQQ close below its 100-session simple moving average.
- Candidate B: control plus QQQ close below its 200-session simple moving average.
- Candidate C: control plus negative QQQ 60-session return.
- Signals are computed at QQQ close and trades occur at the next TQQQ open. Daily equity is marked at adjusted close. Cash earns zero. Placeholder transaction cost is 10 bps per buy or sell.
- QQQ indicator history begins 2009-01-01 to warm up 100/200-session indicators before the 2010-10-07 strategy start.
- Yahoo Finance adjusted OHLC is reconstructed with adjusted-close/raw-close factors; independently validate corporate-action handling and adjusted-open assumptions before trusting absolute balances.

## Separate CI failure observed during this check
The broader `research-tests` workflow run https://github.com/eklu654/Trading-Bot/actions/runs/39371734539 failed in `test_overdue_slot_is_suppressed_instead_of_mislabelled`: expected no title but got `Midday`. The gradual-decline comparison workflow itself passed. This unrelated daily-email test failure is recorded for follow-up and should not be conflated with backtest status.

## Next actions
1. Reconcile this reconstructed control with the prior frozen B0 result (~$4.04M) before making strategy conclusions.
2. Validate adjusted open/close price construction against an independent source or trusted frozen dataset.
3. Add a daily equity/trade ledger and targeted tests for shock latching, trough tracking, rebound re-entry, signal timing, and end-of-period marking.
4. Only after reconciliation, run regime-specific analysis for 2011, 2015–16, 2018, 2020, and 2022, plus walk-forward evaluation.
5. Separate QQQ/SPY regime analysis for 2000–02 and 2007–09; do not fabricate pre-inception TQQQ returns.

## Guardrails
- A defense is successful only if terminal equity exceeds the same-period frozen B0 control after realistic costs; drawdown improvement alone is not enough.
- This script is research-only: no Alpaca or order endpoints, no production strategy changes, no automatic promotion.
- B0 remains frozen; F75 remains shadow-research-only.
- No candidate is promoted based on this run.
