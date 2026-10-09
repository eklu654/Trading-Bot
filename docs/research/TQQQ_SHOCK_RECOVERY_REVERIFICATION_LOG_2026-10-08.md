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


## 2026-10-09 follow-up: synthetic three-layer cost-stress timing bug corrected

### Failure and root cause
The first attempt to freeze the cost-stress inputs introduced a Python syntax/indentation error in the event-attribution script. The failed run was [37883273299](https://github.com/eklu654/Trading-Bot/actions/runs/37883273299); its failure was inspected from the job log, corrected, and is not being treated as a strategy result. The subsequent successful run is [37883372240](https://github.com/eklu654/Trading-Bot/actions/runs/37883372240).

The substantive bug was in the old `tqqq_three_layer_cost_robustness.py`: it used the same day's signal for that day's intraday return and the prior day's signal for the overnight return. That violates the required close[t] -> open[t+1] execution model and introduces look-ahead into the intraday leg. This was the cause of the absurd $128B-$205B synthetic cost-stress results. Those figures are invalid and must be retired, not quoted as strategy outcomes.

### Corrective implementation and validation
- Commit `ed95b70bf7bac5ecbd5ccf555fca8691a6390dab` changed cost stress to the shared causal execution helper and added a zero-cost consistency assertion.
- Commit `533525a0ad4946ca8e918098ab077d0736e7d061` added an export of the exact QQQ-derived synthetic return streams and frozen signals.
- Commit `6b3e1ab75b4f2b5b68171c321b8723eed346826d` changed cost stress to consume frozen inputs instead of downloading a second price series.
- Commit `e88a3ac17c67a1725f0acd86ef0b90551b088337` corrected the export block indentation/syntax.
- The latest attribution run succeeded, with artifact 11594948023 (SHA-256 `033b29012dc57634d7cf7002c2224c02627a4f776deb9a0f1141a3016bcb981c`). The artifact includes `tqqq_three_layer_frozen_inputs.csv`, `tqqq_three_layer_attribution_summary.csv`, and `tqqq_three_layer_cost_robustness.csv`.
- The zero-cost balances agree on identical frozen inputs to numerical tolerance:
  - base: attribution $207,067.983120 vs cost audit $207,067.983120;
  - Fed-conditioned: $110,128.569156 vs $110,128.569156;
  - three-layer: $89,973.174122 vs $89,973.174122.
- The causal synthetic result is therefore about $207k / $110k / $90k—not $128B / $183B / $205B. With modeled costs, the three-layer terminal balance declines to about $76.5k at 5 bps, $65.0k at 10 bps, $39.9k at 25 bps, and $17.6k at 50 bps per exposure transition.
- Research-tests [37883372312](https://github.com/eklu654/Trading-Bot/actions/runs/37883372312) and actual-TQQQ validation [37883372269](https://github.com/eklu654/Trading-Bot/actions/runs/37883372269) also passed on commit `e88a3ac17c67a1725f0acd86ef0b90551b088337`.

### Updated conclusion
The synthetic three-layer study is now REJECTED FOR PERFORMANCE CLAIMS on two independent grounds: (1) its prior cost script leaked same-day signal information into intraday returns, creating the extraordinary wealth claims; and (2) after correcting timing, the causal synthetic variant still performs poorly and the actual-TQQQ version remains far below actual TQQQ buy-and-hold. Keep the Fed-layer hypothesis as a research question, not as a validated strategy.

The separate ~$4.04M shock/recovery candidate is unaffected by this particular synthetic-script defect, but remains only provisionally reproduced until the canonical implementations run on one immutable shared dataset and their daily curves match. The remembered ~$3.3M anti-fakeout strategy is still unrecovered.


## 2026-10-09 continuation: exact common-input replay passes; long-history rally cases recovered

### Canonical same-input audit — PASS
The dedicated workflow [37883989658](https://github.com/eklu654/Trading-Bot/actions/runs/37883989658) passed after adding a second, independently coded event-state builder in addition to the independent daily execution loop. Artifact 11594464513 contains the frozen common input, full daily curve, event ledger, and manifest.
- Window: 2010-02-11 through 2026-10-07, 4,189 aligned sessions.
- Initial balance: $5,000.
- Canonical rule: QQQ adjusted-close daily return <= -4.5% triggers defense; remain defensive through the post-shock low until the first close >=10% above that low; TQQQ trades at the next open.
- Frozen input SHA-256: `fa28ea933475d843cb8daf6bdd8d7aeca3c4ed20b9a0e55f8bec5eaaf68f7d00`.
- Independent event builders agree on all nine events and the full signal series.
- Maximum absolute daily-return difference: 0.0. Maximum absolute equity-curve difference: 0.0.
- Strategy final: $4,040,311.69; TQQQ buy-and-hold on the exact same data: $2,094,668.80. CAGR: 49.487% vs 43.705%; maximum drawdown: -73.53% vs -81.66%.
- A prior frozen dataset/run produced $4,040,312.84, so separate fresh yfinance downloads still vary by roughly a dollar due adjusted-price revisions/precision. The precise claim is: **the ~$4.04M headline is verified for a frozen dataset with exact independent event/signal/return/equity agreement; the exact terminal dollars are data-snapshot-dependent.**

### Historical anti-rally audit results
Two signal-only S&P 500 studies were run from 1970-01-02 through 2026-10-07. They are explicitly not QQQ/TQQQ portfolio backtests.
1. Daily shock rule (S&P 500 daily close return <= -4.5%, then +10% from the post-shock low) generated 18 events: 10 failed, 6 successful, 2 censored. It produced no events in the 1970s because the trigger is a single-day shock threshold; this does not cover the prolonged 1970s bear by itself.
2. Complementary drawdown rule (cross below -10% from a 252-session high, then +10% from the trough; rearm only after regaining 95% of the trigger peak) generated 24 events: 12 failed, 9 successful, 3 censored. Key examples:
   - 1971-08-04 trigger; +10% recovery on 1971-12-16; outcome censored within the 252-session horizon.
   - 1973-04-27 trigger; recovery decision 1973-10-11; failed 28 sessions later.
   - 1987-10-15 trigger; recovery decision 1987-10-21; failed 3 sessions later.
   - 2000-04-14 trigger; recovery decision 2000-07-12; failed 65 sessions later.
   - 2000-10-11 trigger; recovery decision 2001-04-18; failed 98 sessions later.
   - 2022-02-22 trigger; recovery decision 2022-03-29; failed 22 sessions later.
   - 2022-04-22 trigger; recovery decision 2022-07-28; failed 41 sessions later.
   - 2020's two recovery events in this broad-market signal study were labeled successful; 2023-10 and 2025-03 drawdown episodes also labeled successful.
- The new workflow is [37883989726](https://github.com/eklu654/Trading-Bot/actions/runs/37883989726), artifact 11595481898. Daily-shock study: [37883989671](https://github.com/eklu654/Trading-Bot/actions/runs/37883989671).
- These are outcome labels, not proof that the currently defined MA/MACD features can predict the labels. The event sample is small, the index differs from QQQ, and feature separation is diagnostic only. The 1971 case is censored rather than classified as a failed rally under this specific 252-session definition.

### Historical ~$3.3M figure: a plausible but not equivalent artifact found
Old workflow artifact 11537006525 from run [37748373915](https://github.com/eklu654/Trading-Bot/actions/runs/37748373915) reports `baseline_10pct` at $3,270,343.84 from $5,000. It does **not** identify an additional anti-fakeout rule; the code at that revision uses unadjusted QQQ Close for signals and unadjusted TQQQ Close-to-close returns, not the current adjusted OHLC / close-to-next-open method. Another exploratory variant, `slow_18_target25`, reports $3,782,916.98 but is also selected from a full-period grid. Therefore this old $3.27M result is a candidate source of the remembered number, not a recovered or verified version of the user's remembered anti-fakeout strategy.

### Updated next steps
1. Preserve the same-input audit artifact/hash as the reference snapshot; do not compare runs from fresh data pulls as if the raw adjusted series were immutable.
2. Recover the exact old anti-fakeout strategy/rule from the historical run that the user remembers, with particular attention to its code revision, price basis, and execution convention. Do not relabel `baseline_10pct` as that strategy.
3. Evaluate the fixed MA/MACD/trend features against the historical failed/successful labels only with chronological separation; do not fit or select a rule on the same events used to report success.
4. Keep all pre-2010 conclusions signal-only. No TQQQ balance may be attributed to 1971, 1973, or 1987.


### Further forensic note on the ~$3.3M candidate and ret60 anti-fakeout code
A separate historical artifact, [bear-discriminator walk-forward run 37743825884](https://github.com/eklu654/Trading-Bot/actions/runs/37743825884), contains the same `baseline_10pct` result of $3,270,343.84. The `ret60_ret-10_target15` full-period row is $3,138,436.81, not ~$3.3M. More importantly, the older `bear_discriminator_walkforward.py` recomputes the override target on every defensive day rather than locking the stricter target once the +10% recovery decision is reached. If the 60-day-return condition turns false before the larger target is hit, it falls back to the 10% target. That is not a valid implementation of a persistent anti-fakeout delay. Its walk-forward rows also select the baseline in both chronological folds. Therefore neither that row nor the $3.27M baseline resolves the remembered strategy. The corrected persistent-target implementation in `failed_bounce_strategy_walkforward.py` is the better starting point for reconstruction, but its grid-selected variants remain in-sample until their exact rule is frozen and replayed with adjusted OHLC next-open execution.
