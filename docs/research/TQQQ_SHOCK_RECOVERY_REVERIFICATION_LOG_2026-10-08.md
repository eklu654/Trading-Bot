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


## 2026-10-09 continuation: latest workflow sweep and three-layer reality check

### Latest CI / research sweep
All following runs completed successfully on main at commit `b6d8e24c486de2dcb4925398580438f84167ddf7` (UTC 2026-10-09 03:52):
- Research tests: [37881243283](https://github.com/eklu654/Trading-Bot/actions/runs/37881243283)
- Canonical shock/recovery robustness: [37881243286](https://github.com/eklu654/Trading-Bot/actions/runs/37881243286), artifact 11595175078
- Structural matrix: [37881243310](https://github.com/eklu654/Trading-Bot/actions/runs/37881243310), artifact 11593689207
- Partial DMA matrix: [37881243315](https://github.com/eklu654/Trading-Bot/actions/runs/37881243315), artifact 11594611426
- Actual-TQQQ three-layer validation: [37881243323](https://github.com/eklu654/Trading-Bot/actions/runs/37881243323), artifact 11595025449
- Independent canonical audit: [37881243328](https://github.com/eklu654/Trading-Bot/actions/runs/37881243328), artifact 11594243817
- Feature audit: [37881243337](https://github.com/eklu654/Trading-Bot/actions/runs/37881243337), artifact 11593574579
- Three-layer event attribution: [37881243276](https://github.com/eklu654/Trading-Bot/actions/runs/37881243276), artifact 11594870800

### Latest canonical result (still provisional, not 100% verified)
- Latest robustness artifact: $4,040,313.07 final from $5,000; TQQQ buy-and-hold $2,094,668.95; max drawdown -73.53% vs -81.66%.
- Independent audit from the same sweep: $4,040,314.45 vs buy-and-hold $2,094,668.80. This implementation's strategy terminal balance differs from robustness by about $1.38, but inputs still come from separately downloaded adjusted-price series. No exact same-input/daily-curve equality assertion has been demonstrated; therefore status remains PROVISIONALLY REPRODUCED, NOT FULLY VERIFIED.
- Cost stress on the robustness run: estimated terminal wealth is $4.0018M at 5 bps, $3.9637M at 10 bps, $3.8513M at 25 bps, and $3.6706M at 50 bps per exposure transition. These are modeled costs, not broker fill evidence.
- The simple rule is not consistently better by era: 2025-current return is about +100.2% for the rule vs +114.4% buy-and-hold, though the rule materially improved 2022-2024 (+42.3% vs -1.36%). Its observed max drawdown remains very large at roughly -73.5%.

### Critical discovery: the huge synthetic three-layer result does not survive actual TQQQ
- The synthetic leveraged-QQQ three-layer artifact reports approximately $204.86 billion from $5,000 for its three-layer variant (base $128.31B; conditioned $183.10B). This is a separate synthetic proxy backtest starting in 1999, not a real TQQQ result and not the shock/recovery strategy.
- The actual-TQQQ validation on the available 2010–2026 TQQQ history reports:
  - 100-DMA base: $84,635.24
  - Fed-conditioned: $106,887.61
  - Three-layer: $91,784.61
  - Actual TQQQ buy-and-hold: $2,029,288.82
- Thus the three-layer architecture, as currently specified, fails badly against actual TQQQ buy-and-hold. The $128B/$205B synthetic figures must not be used as strategy performance or as evidence that the rule beats TQQQ. Treat the synthetic study as REJECTED FOR PERFORMANCE CLAIMS until the synthetic return model and regime rule are rebuilt and the actual-instrument validation is explained.
- The event-attribution artifact is also internally suspicious: its summary says conditioned minus base is -$96,938.73 and three-layer minus conditioned is -$20,155.01, whereas its synthetic terminal values claim conditioned and three-layer greatly exceed base. This is a direct reconciliation inconsistency between artifact summaries and needs a code/data audit before using that attribution.
- Current code's synthetic proxy is based on applying a 3x multiple to QQQ returns with a daily loss floor, rather than actual TQQQ OHLC/adjusted-open returns; it omits real fund path/tracking/fee behavior. That is a likely model limitation, but not by itself a complete explanation for the scale of the gap.

### Structural and feature diagnostics are too small to establish a reliable anti-fakeout rule
- The latest canonical feature audit produces only nine canonical shock/recovery events; the resolved outcome sample in the separation table is one failed vs seven successful events. These counts are too small to validate a multi-feature classifier or optimize a threshold without severe overfitting risk.
- The structural matrix's best exploratory rows report about $3.763M and -70.23% max drawdown, but they were selected from many rules/targets/exposures over the same sample. They are exploratory, not an out-of-sample result and not proof of the user's remembered ~$3.3M baseline.
- The 2018/2020/2022 event labels are diagnostic future outcomes only. No feature rule is approved until frozen, causal, chronological holdout results show robust improvement and the event ledger is independently reconciled.

### Historical-period scope correction
- Actual QQQ data begins in 1999 and actual TQQQ begins in 2010. Any proposed tests for 1987 or 1971 cannot be actual QQQ/TQQQ strategy backtests. They must be explicitly labeled as broad-market signal-only studies using a long-history index (e.g., S&P 500 series), with different claims and no invented TQQQ terminal balance. The 2000–2002 study can use QQQ as a signal source but must still label TQQQ performance as synthetic if projecting a leveraged instrument that did not yet exist.
- Repo code search did not recover an exact existing failed-bounce report for 1971/1987, so those historical test definitions/results remain UNRECOVERED rather than assumed completed.

### Next actions, in order
1. Implement one immutable shared dataset artifact and deterministic replay: download once, store QQQ/TQQQ raw OHLCV plus adjusted close (and explicit adjusted-open formula), record SHA-256 hashes, and feed the exact same arrays to both canonical engines.
2. Add an automated assertion comparing event dates, executed exposure by session, daily returns, and daily equity across engines; test at least one shock/recovery transition and the first overnight/intraday after each transition.
3. Recover the exact ~$3.3M anti-fakeout rule from git history and old run artifacts. Do not infer it from the current matrix's top row.
4. Audit synthetic three-layer model: reconcile the contradictory attribution artifact, inspect daily return construction and date alignment, then either repair or explicitly retire synthetic wealth figures.
5. Run long-history signal diagnostics for 1971, 1987, 2000–2002, and 2022 with the same causal feature definitions where the data supports them. Keep signal-only evaluation separate from actual TQQQ portfolio returns.
6. Keep the initial benchmark non-AI. Do not advance to AI selection or paper trading until the original baseline, exact-input replay, and stress/holdout evidence are resolved.
