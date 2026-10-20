# Gradual-decline overlay comparison — research log

Updated: 2026-10-20 UTC (review pass 2)
Status: implementation committed; historical run result not yet verified in this note.

## Goal
Test whether simple trend overlays improve terminal account value versus the frozen B0 shock/recovery control, especially in slow declines where QQQ never falls 4.5% in one session. B0 and F75 production/paper rules remain unchanged. This is a separate, read-only research experiment.

## Artifacts
- Script: `research/backtests/gradual_decline_overlay_comparison.py`
- Deterministic tests: `research/backtests/test_gradual_decline_overlay_comparison.py`
- Workflow: `.github/workflows/gradual-decline-overlay-comparison.yml`
- Workflow runs on a relevant push and can also be manually dispatched. It syntax-checks the script, downloads daily bars, runs the comparison, and uploads a 30-day JSON artifact.

## Rules compared
Starting capital: $5,000; start date: 2010-10-07; end: latest overlapping daily data returned by Yahoo Finance.
- Control: B0 shock/recovery reconstruction. QQQ close-to-close loss of 4.5% or worse latches an exit; re-entry is signaled after QQQ closes 10% above the post-trigger low.
- Candidate A: control plus QQQ close below its 100-session simple moving average.
- Candidate B: control plus QQQ close below its 200-session simple moving average.
- Candidate C: control plus negative QQQ 60-session return.
- Signals are computed at QQQ close and trades occur at the next TQQQ open. Daily equity is marked at adjusted close. The script assumes cash earns zero and applies a placeholder 10 bps cost per transaction.

## Metrics
For each variant the JSON records terminal equity, return, maximum drawdown, percentage of days invested, and number of position changes. The required promotion criterion remains strict: terminal equity must exceed the same-period B0 control after realistic costs. Drawdown improvement by itself is not sufficient.

## Important limitations / interpretation guardrails
1. This is a reconstruction of the documented B0 shock/recovery concept, not a verified reproduction of the earlier ~$4.04M result. The prior frozen-input/daily-curve reconciliation remains outstanding.
2. Yahoo Finance adjusted OHLC is reconstructed using adjusted-close/raw-close factors. Independently validate data and corporate-action handling before trusting absolute balances. The latest review added QQQ pre-start history (from 2009-01-01) so 100/200-session indicators are warmed up at the 2010-10-07 trading start; this removes an avoidable initial-period blind spot but does not validate the adjusted-price reconstruction.
3. The 60-session negative-return rule and simple MA rules are deliberately unoptimized first-pass candidates. Do not tune them on the full sample and then present the same sample as out-of-sample evidence.
4. The test begins in the TQQQ era; it does not fabricate pre-inception leveraged ETF returns. Separate QQQ/SPY regime studies are needed for 2000–02 and 2007–09.
5. A single full-period result is not enough. Next, report regime-specific performance for the 2011/2015–16/2018/2020/2022 declines and run walk-forward checks (fit/design decisions on earlier periods, evaluate later periods).
6. The script is research-only: no Alpaca or order endpoints, no production strategy changes, no automatic promotion.

## Audit trail
- `142ed34`: initial comparison script added.
- `2e49980`: corrected execution timing so close-generated signals execute at the next session's open.
- `b922287`: added CI workflow to syntax-check, run, and upload the result artifact.
- `fd0832e`: added QQQ indicator warm-up history and clarified that the placeholder cost is 10 bps per transaction (each buy/sell), not a round-trip total.
- `ffa825c`: added deterministic unit tests for SMA window behavior and pre-trade indicator warm-up.
- `03c422c`: wired unit tests into the workflow before downloading/running the historical sample.
- Next required evidence: successful Actions run, passing unit-test output, JSON artifact, and independent sanity checks of B0's terminal value and the data adjustment/execution assumptions. Until then, no numeric result or winning defense is claimed.
