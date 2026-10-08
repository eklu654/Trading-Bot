# TQQQ QQQ Shock/Recovery Reverification Log — 2026-10-08

## Purpose
Re-establish the canonical research state after a context-loss incident. This log is append-only by dated follow-up: do not silently overwrite prior conclusions. Treat this document as the current research checkpoint, not as proof that any strategy is validated.

## User-confirmed research state
- Starting capital: $5,000.
- Current remembered baseline: approximately $3.3M using QQQ daily shock -> +10% recovery from post-shock low, with an additional rule intended to avoid re-entering on a bear-market rally.
- A separate approximately $4.0M result was discussed and may previously have been withdrawn for methodological reasons. The exact historical decision/reason is not yet recovered; do not call it approved.
- Objective: independently verify the actual-TQQQ backtest, benchmark over exactly the same dates, execution timing, signal causality, and the extra anti-fakeout rule before making any strategy decision.
- The synthetic leveraged-QQQ/Fed/DMA result (~$3.7M) is a separate study and is not this baseline.

## Repository files inspected on 2026-10-08
- `research/failed_bounce_structural_matrix.py` (blob SHA `92ed802d5e4c97064cae6191e74b3ba89980d8c4`)
- `research/failed_bounce_robustness.py` (blob SHA `753ecc24f8df11406601495c2427e457fcd7be22`)
- `research/audit_failed_bounce_canonical_independent.py` (blob SHA `740d3bb7f71a9c143efe61b153b91c940cc39c80`)
- `research/failed_bounce_strategy_walkforward.py` (blob SHA `e6f7cd1103ab749b5cc20ca6a97726ad3095e325`)
- `research/causal_execution.py` (blob SHA `caf48a0f64b0485021cf27adf0d822ab795735ae`)

## Confirmed methodological issue in structural matrix
In `failed_bounce_structural_matrix.py`, `build_events()` assigns each event a future outcome label using up to 252 future sessions (`label()`). `signal_for_rule()` then skips events whose label is `censored`. That means whether the strategy acts on a recent shock/recovery event can depend on whether its future outcome is already observable within the 252-session label horizon. This is a look-ahead/sample-selection defect for portfolio evaluation. The $3.337M structural-matrix output therefore cannot be treated as a valid strategy result until the trading signal is rebuilt independently of future labels.
The future label is appropriate for *diagnostic evaluation* of event outcomes, but must never gate whether a live strategy trades that event.

## Other issues requiring explicit audit
1. `failed_bounce_strategy_walkforward.py` uses unadjusted `Close` for both QQQ signals and TQQQ returns. That differs from the adjusted OHLC convention in the robustness/matrix scripts and must not be mixed with those reported balances.
2. The walk-forward loop computes equity for each configuration over the full period before slicing train/test segments. Its position logic uses only past/current QQQ data, but performance initialization and fold accounting must be reconstructed carefully to ensure the test fold starts with the actual training-period ending equity and only frozen parameters selected in training.
3. The structural matrix searches many feature rules, targets, and exposures over the same full sample. Its best row is in-sample selected; it is not an unbiased performance estimate.
4. The independent audit uses a different explicit overnight/intraday position-indexing convention than `causal_execution.py`; reconcile day by day with hand-checked event dates before relying on it.
5. The canonical robustness result (~$4.04M) uses QQQ -4.5% daily shock and +10% recovery, with actual TQQQ adjusted OHLC, but by itself has no additional anti-bear-rally filter. It is a different strategy from the user-confirmed ~$3.3M baseline.
6. The $3.3M exact frozen rule and the historical reason for withdrawing the $4.0M result remain unconfirmed. Do not guess the missing filter or the previous rejection reason.

## Required next steps (fixed order)
1. Freeze a no-look-ahead event builder: trade on every qualifying QQQ shock event regardless of future outcome label. Outcome labels may be joined only after strategy signals and equity are computed.
2. Implement the user-confirmed anti-fakeout rule as a separate named, frozen rule. Recover its exact definition from prior commits/run logs/docs before approximating it.
3. Independently calculate QQQ adjusted-close signals, TQQQ adjusted open/close returns, next-open execution, and TQQQ buy-and-hold on one exact common date index.
4. Produce event-level CSV ledger (shock date, low date, +10% date, anti-fakeout state, next-open position changes, later labels for analysis only) and assert no future label is referenced by signal construction.
5. Reproduce ~$3.3M baseline before comparing the ~$4.0M rule. Explain any difference from historical figures by date range, data basis, execution, costs, or code changes.
6. Run fixed-rule chronological holdouts and sensitivity/cost tests. Do not select a winner on the holdout period.
7. Record every meaningful research action, commit, run ID, result, methodological decision, and next step in this checkpoint before switching tasks or ending a work session.

## Context-preservation protocol proposal
Every meaningful step must leave a durable GitHub trail:
- Update this log after each completed verification/change/run, including exact commit SHA and workflow run ID when available.
- Keep a short `docs/research/CURRENT_STATE.md` as the authoritative pointer to the active strategy, frozen rules, latest verified results, rejected results/reasons, current blockers, and next command/action.
- Each strategy result must have a machine-readable config (thresholds, price columns, execution convention, dates, capital, costs) and a result artifact/CSV.
- Never replace a prior result silently. Mark it VERIFIED, PROVISIONAL, REJECTED, or UNVERIFIED with the specific evidence and reason.
- On resumption, read CURRENT_STATE first, then this log, then inspect the latest commit and workflow run before conducting new experiments.
- Do not say “verified” unless an independent reconstruction with matching dates and execution passes and the benchmark is computed on the identical data window.
