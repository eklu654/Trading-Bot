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


## 2026-10-09 rerun and artifact comparison (after workflow export fix)
Fresh workflow runs on commit `7b7824959ff6602641a64e52c078d046f1f69a13`:
- robustness run 37877619231 (success), artifact 11592489544.
- independent audit run 37877619214 (success), artifact 11593196137.
- structural matrix run 37877619135 (success), artifact 11592718712.

### Recomputed balances
- robustness canonical: $4,040,314.1961; buy-and-hold $2,094,668.8014.
- structural matrix canonical row: $4,040,314.3869 (same shock/recovery baseline, different report implementation).
- independent audit canonical: $4,040,312.7260; buy-and-hold $2,094,668.8014.
- The independent strategy ending balance differs from robustness by about $1.47. This is small relative to $4.04M but not yet an exact daily-curve reconciliation.

### Critical frozen-data comparison
Both artifacts have 4,189 rows and the same date range, 2010-02-11 through 2026-10-07. However, they are NOT identical frozen inputs:
- QQQ adjusted-close maximum absolute difference: approximately 0.000213623, across 3,241 rows.
- TQQQ adjusted-close maximum absolute difference: approximately 0.0000152588, across 3,041 rows.
- QQQ/TQQQ raw Close, Open, High, Low, and Volume columns match exactly in the downloaded CSV comparison; adjusted-close columns do not. This likely reflects separate yfinance adjusted-series calculations/revisions, but the cause is not proven.
- Input file hashes differ. Therefore the user's specific requirement—same frozen inputs and daily curves reconciled—has not passed.
- Both outputs do contain daily equity curves and input CSVs after the artifact-path correction.

### What is now supported
The ~$4.04M result is reproducible to within a few dollars across independent implementations and repeated runs on the available history. This is a solid numerical replication of the reported headline, but not yet a fully identical-input audit. Do not describe it as 100% verified. The common raw OHLC data suggests adjusted-close differences are not driving a large terminal-value discrepancy, but this remains to be established by a same-input replay.

### Historical strategy context recovered
The older user-confirmed remembered baseline was approximately $3.3M: QQQ daily shock -> +10% recovery from the post-shock low, plus an additional anti-fakeout rule intended to avoid re-entry during a bear-market rally. This is NOT the same as the current ~$4.04M baseline, which has no anti-fakeout filter. The exact historical filter and reason the ~$4M was withdrawn remain unresolved.
- The structural-matrix workflow is `tqqq-failed-bounce-structural-matrix.yml`, run 37877619135.
- Its artifact reports canonical_defensive_until_plus10 at $4,040,314.39. It also includes feature-family diagnostics: 60/120/200-day trend and SMA-slope states, price vs SMA, structural damage/repair labels, and candidate flags.
- A documented defect in `research/failed_bounce_structural_matrix.py`: the event builder creates labels using up to 252 future sessions, then signal construction skips censored events based on those future labels. That leaks future observability into portfolio event selection. The matrix's best selected outputs must not be treated as unbiased strategy results.
- The previous Fed/macro/DMA structural composite is documented in `docs/research/tqqq-composite-fed-macro-dma-defense-2026-10-05.md`: 200-DMA below trend + Fed TIGHTENING_PAUSED and/or macro deterioration/crisis; exit only above 200-DMA and MACRO_STRUCTURAL_EXPANSION. It improved the synthetic 1999–2009 path but was classified HISTORICALLY EFFECTIVE, MODERN-ERA OVER-DEFENSIVE. It is not the $4M strategy.
- Fed cycle event study lists 1994–95, 1999–2000, 2004–06, 2015–18, and 2022–July 2023 cycles. MACD/golden-cross feature family has not yet been recovered from the specific historical failed-bounce workflow records inspected here; do not invent its exact rule.

### Next verification action
Create a shared, immutable input artifact once (QQQ/TQQQ raw OHLCV plus one explicit adjusted-price construction), then run both canonical engines against those exact files without downloading again. Assert byte-identical input hashes, matching event/execution dates, and compare every daily equity value. Separately recover and reproduce the exact ~$3.3M anti-fakeout rule from its historical source before treating it as the original strategy.
