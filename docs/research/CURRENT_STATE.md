# Trading-Bot Research — Current State

**Last updated:** 2026-10-08 (latest verification activity extends into 2026-10-09 UTC)  
**Active investigation:** Reverify the QQQ shock/recovery TQQQ strategy family.  
**Starting capital:** $5,000.

## Active baseline (user-confirmed, exact rule still being recovered)
The user's remembered current baseline is approximately **$3.3M**, based on a QQQ daily-drop trigger and +10% recovery from the post-shock low, plus an additional anti-bear-rally rule. The exact anti-fakeout rule must be recovered from prior source history/logs before treating any matrix row as the original frozen baseline. Do not substitute the simple ~$4.04M strategy for this baseline.

## Results status
- **Original ~$3.337M structural-matrix result: INVALID AS ORIGINALLY IMPLEMENTED.** The original code skipped events labelled `censored`, where that label depended on up to 252 future sessions. This made future outcomes gate whether a qualifying event was traded.
- **Look-ahead gate fixed:** commit `773c06b0621562497c6e47394fb267f214b788e6` removed the censored-label skip from `signal_for_rule()`; future outcome labels are now diagnostics only and no longer gate trading signals.
- **Corrected exploratory matrix:** run [37862580078](https://github.com/eklu654/Trading-Bot/actions/runs/37862580078) passed. It reports the simple binary canonical shock/+10% strategy at **$4,040,314**, buy-and-hold at **$2,094,669**, and top structural configurations around **$3,763,076** (repair_damage/120_200_bear-style filter, +15% higher target, 75% exposure). This is a post-fix exploratory matrix result, not the frozen baseline and not out-of-sample validation.
- **~$4.04M canonical result: REPRODUCED, STILL PROVISIONAL.** The aligned robustness run [37862580103](https://github.com/eklu654/Trading-Bot/actions/runs/37862580103) reports $4,040,313; independent audit [37862580071](https://github.com/eklu654/Trading-Bot/actions/runs/37862580071) reports $4,040,312. The one-dollar-scale discrepancy is rounding/data arithmetic, not evidence of a material difference. Both use 9 qualifying events. Correction to an earlier note: the independent audit DOES intersect QQQ and TQQQ date indexes before generating events; the earlier claim that its event indices were misaligned was wrong. The explicit overnight/intraday loop appears consistent with close[t] signal -> open[t+1] execution, but exact daily-curve equality has not yet been asserted in a test.
- **Remembered ~$3.3M baseline: NOT YET REPRODUCED.** The original exact anti-bear-rally rule and matching frozen configuration are still not identified. Do not assume the current matrix's best row is that baseline.
- **~$3.7M Fed/DMA synthetic-history result: SEPARATE STUDY.** Do not use it as evidence for actual-TQQQ shock/recovery performance.
- **Historical reason the ~$4M result was previously withdrawn:** not recovered yet; do not invent it. What is now confirmed is that the result is numerically reproduced by aligned implementations, but its parameter-selection/generalization evidence is insufficient.

## Latest code/test activity
- Code fix commit: `773c06b0621562497c6e47394fb267f214b788e6`.
- Regression test added: `tests/test_failed_bounce_no_lookahead.py`, commit `c862803ffa4d539bd64541bd467908f7150fcbbe`.
- First test run failed during collection because `research` was not on `sys.path`; corrected in commit `87e74d008884d475248263a9510fa39ef300517c`.
- The rerun `research-tests` workflow is [37862742592](https://github.com/eklu654/Trading-Bot/actions/runs/37862742592); status was in progress at last inspection. Do not mark regression tests passed until its final logs show that.
- The fixed matrix passed at [37862580078](https://github.com/eklu654/Trading-Bot/actions/runs/37862580078); duplicate workflow [37862580116](https://github.com/eklu654/Trading-Bot/actions/runs/37862580116) also passed.
- Robustness run: [37862580103](https://github.com/eklu654/Trading-Bot/actions/runs/37862580103).
- Independent audit: [37862580071](https://github.com/eklu654/Trading-Bot/actions/runs/37862580071).
- Feature audit: [37862580158](https://github.com/eklu654/Trading-Bot/actions/runs/37862580158), successful as diagnostic output, not strategy validation.

## Source files inspected
- `research/failed_bounce_structural_matrix.py` — blob `0ffb403cb29609a0ba4ade92ec9517ec11d722f1` after fix
- `research/failed_bounce_robustness.py` — blob `753ecc24f8df11406601495c2427e457fcd7be22`
- `research/audit_failed_bounce_canonical_independent.py` — blob `740d3bb7f71a9c143efe61b153b91c940cc39c80`
- `research/failed_bounce_strategy_walkforward.py` — blob `e6f7cd1103ab749b5cc20ca6a97726ad3095e325`
- `research/causal_execution.py` — blob `caf48a0f64b0485021cf27adf0d822ab795735ae`
- Detailed checkpoint: `docs/research/TQQQ_SHOCK_RECOVERY_REVERIFICATION_LOG_2026-10-08.md`

## Mandatory next steps
1. Inspect final regression-test run [37862742592](https://github.com/eklu654/Trading-Bot/actions/runs/37862742592); fix any failures and record passing evidence.
2. Add a test comparing the independent audit's day-by-day equity to `causal_execution.py` on a deterministic fixture, including the first shock and recovery transitions.
3. Recover the exact frozen anti-bear-rally rule and prior ~$3.3M run from git history/workflow artifacts; do not infer it from the best current matrix row.
4. Reconstruct baseline and simple $4M candidate on one aligned QQQ/TQQQ frame, identical dates, price basis, $5,000 start, and close-to-next-open execution.
5. Generate a dated event/trade ledger and assert no future label is referenced by signal construction.
6. Run chronological holdouts only after rules are frozen; no winner selection on the holdout period.
7. Record every meaningful research action, exact outputs, commit SHA, workflow run ID, result status and next step here before switching tasks or ending a work session.

## Context-preservation rule
Before any new experiment, read this file and the detailed checkpoint. After every meaningful step, commit the current rules, exact output/result, status (VERIFIED / PROVISIONAL / REJECTED / UNVERIFIED), reason, commit SHA, workflow run ID, and next step. Never silently replace prior findings. At the end of every work session, update this file first.

## Forensic follow-up — October 8 execution-timing concern (added 2026-10-09 UTC)
A review of the repository commit chronology surfaced specific, contemporaneous execution-timing fixes that must be investigated as the likely source of the user's remembered open/close discrepancy:

- `b813c898fdd7f54b88618a44ed89a3ba284fcd0d` (2026-10-08 19:23:08 UTC): “Fix failed-bounce signal timing: re-entry executes next open after recovery close”. In `research/failed_bounce_structural_matrix.py`, changed defensive/re-entry slice boundaries around `decision_i`; also changed canonical defensive control from `decision_i + 1` endpoint to `decision_i`. This is a real timing correction, not merely a datetime precision issue.
- `ea1e01c08d2ab3905fa946a6e8128b5aa6d4a843` (2026-10-08 19:25:12 UTC): “Correct independent audit overnight position timing”.
- `c0387408f85c788fc66d817372474de17f5ef35e` (2026-10-07 10:06:05 UTC): “Correct close-to-next-open overnight exposure accounting”, modifying `research/tqqq_signal_source_audit.py` so overnight return is attributed to the position held before the open execution, while intraday return uses the executed position.
- `ab27e7bc73bcfa9d472f392371b55c3675a5f2d0` (2026-10-06): “fix: derive adjusted open for actual TQQQ validation”, adding `adj_open = open * adj_close / close`.
- Earlier, `f2c048a37eaf283e755678b301904b0ecd8861f7` (2026-09-29) explicitly separated adjusted-close total-return accounting from unadjusted-close DMA signals.

These commits strongly support that close/open timing and adjusted-open accounting are relevant to the historical audit. They do NOT alone establish that the canonical ~$4.04M figure is wrong: need map the exact $4M run to the code revision and compare the old/new daily equity series. Also distinguish the datetime-resolution merge errors (Fed/market join failures) from genuine return-accounting timing bugs; these are separate classes of defect.

### Exact next forensic tasks
1. Fetch the workflow run history around the 2026-10-08 19:22–19:27 UTC commits and map each run's head SHA to the above fixes; record whether the ~$4.04M run predates or follows them.
2. Inspect full patches for `ea1e01c` and `b813c89`, plus `research/failed_bounce_robustness.py`, `research/audit_failed_bounce_canonical_independent.py`, and `research/causal_execution.py` at each relevant commit.
3. Recompute the canonical strategy before and after the timing fixes on identical aligned raw OHLC + adjusted-close inputs. The recovery close signal must execute at next open; overnight return belongs to the position held before that open; intraday return belongs to the position after execution.
4. Compare the resulting event ledger, per-day holdings/returns/equity, final balance, and TQQQ buy-and-hold control. Do not call $4.04M verified until this reconciliation passes.


## 2026-10-08 evening follow-up: execution accounting vs result rejection
- The user correctly raised that the assistant may have mistakenly said the ~$4M candidate was rejected. Current evidence supports reopening it; no source-backed record yet proves the original rejection reason.
- Exact timing fixes identified:
  - `b813c898fdd7f54b88618a44ed89a3ba284fcd0d`: structural matrix changed defensive slice from `[event_start_i:decision_i+1]` to `[event_start_i:decision_i]` and re-entry from `decision_i+1` to `decision_i`. Since the shared engine executes `signal[t]` at open[t+1], these are signal-close indices, so corrected slices are consistent with the next-open convention.
  - `ea1e01c08d2ab3905fa946a6e8128b5aa6d4a843`: independent audit corrected overnight position from `signal[i-1]` to `signal[i-2]`; intraday position remains `signal[i-1]`. This matches the shared engine's execution lag.
- Canonical robustness and independent audit use the same intended event definition: QQQ adjusted-close daily return <= -4.5%; track the lowest QQQ adjusted close from the shock onward; first close >= 10% above that low ends defense; TQQQ traded returns use adjusted OHLC reconstructed from Open * Adj Close / Close. Both use 2010-01-01 through 2026-10-08, $5,000 initial equity, and yfinance source. Thus they are independent calculations, but not independent market-data sources or event definitions.
- Results from post-fix runs were close: robustness/independent audit approximately $4,040,3xx with buy-and-hold approximately $2,094,669. This supports numerical reproduction but does not by itself prove the daily equity curves are identical or data source is flawless.
- Important open issue: `failed_bounce_robustness.py` computes `years` using requested START/END, while its equity array ends at the last actual downloaded TQQQ date. Need record actual last observation and ensure comparison dates identical. Also independently compare event date lists and every daily return/equity value between the two implementations.
- Classification: ~$4.04M = REOPENED / PROVISIONALLY REPRODUCED, NOT REJECTED, NOT YET FULLY VERIFIED. Do not claim a known execution bug invalidated it without a quantified before/after replay.
- Next actions: (1) obtain workflow logs/artifacts containing exact event dates and summary values for run 37862742569 and 37862742593; (2) add shared fixture test for event equivalence and daily equity equality; (3) download one frozen OHLC/Adj Close dataset once and run both engines on it; (4) produce pre-/post-fix replay for commits b813c89 and ea1e01c; (5) compare baseline ~$3.3M only after its anti-fakeout rule is recovered.


## Artifact-level reconciliation started — 2026-10-09 02:16 UTC continuation
Downloaded and inspected actual GitHub Actions artifacts from run SHA `87e74d008884d475248263a9510fa39ef300517c`:
- Robustness run 37862742569 artifact `tqqq-failed-bounce-robustness` (SHA-256 `c5f0e3ed49dff871e030b41744cac8bc9ac2ec313212f7a04d834be16af3194b`).
- Independent audit run 37862742593 artifact `tqqq-failed-bounce-independent-audit` (SHA-256 `a0fc76889d38fc187c75c80552c18446f7c2c5204015e1de3de04c218ca27b0d`).

The actual event ledger from the artifact confirms nine events:
1. shock 2011-08-04; low 2011-08-19; recovery decision 2011-08-31.
2. 2018-10-24; low 2018-12-24; decision 2019-01-07.
3. 2020-02-27; low 2020-03-16; decision 2020-03-26.
4. 2020-06-11; low 2020-06-11; decision 2020-07-06.
5. 2020-09-03; low 2020-09-23; decision 2020-10-12.
6. 2022-05-05; low 2022-06-16; decision 2022-07-19.
7. 2022-09-13; low 2022-11-03; decision 2022-11-11.
8. 2025-04-03; low 2025-04-08; decision 2025-04-09.
9. 2026-06-05; low 2026-07-29; decision 2026-08-13.

Artifact summaries:
- Robustness: canonical $4,040,316.234; TQQQ buy-and-hold $2,094,668.953; CAGR 49.4874% canonical / 43.7047% buy-and-hold; max DD -73.5343% / -81.6598%.
- Independent audit: canonical $4,040,313.235; buy-and-hold $2,094,668.953; CAGR 49.0757% / 43.3478%; max DD agrees to within ~0.000013 percentage points.
- These artifacts are only 3 dollars apart in terminal balances and use the same nine event dates. However, CAGR differs by ~0.41 percentage points despite nearly identical terminal balances. Investigate CAGR annualization/end-date convention before quoting CAGR as validated; terminal value agreement alone does not resolve it.
- Robustness event counterfactuals show the defense helps materially in Feb-Mar 2020 and both 2022 events, but hurts in June/Sept 2020 and April 2025; it is not universally beneficial. These event counterfactual effects are overlapping-path counterfactuals and must not be added as if independent.
- Cost stress in robustness artifact: at 50 bps per exposure change, ending balance ~$3.671M vs ~$4.040M with zero costs; strategy still above reported buy-and-hold but this does not validate other assumptions.
- The scripts use `yfinance.download(... auto_adjust=False)` and reconstruct adjusted open as `Open * Adj Close / Close`. The independent audit computes overnight return with `signal[i-2]` and intraday with `signal[i-1]`; this aligns with close signal -> next-open execution.
- Important caveat: each script independently downloads QQQ and TQQQ, rather than sharing one frozen input snapshot. Dates align in the event ledger but this is not the requested frozen-dataset test. Next fix: persist both exact downloaded tables with index and adjustment columns, hash them, and feed those same files to both engines.
- Classification remains: result is provisionally reproduced. Event ledger recovered. Still not fully verified until frozen-data, daily-curve, event-index, and CAGR conventions reconcile. Original conversation rejection message still not recovered.


### CAGR discrepancy resolved at code level
At artifact SHA `87e74d008884d475248263a9510fa39ef300517c`, the two scripts annualize over different durations:
- `failed_bounce_robustness.py` computes the main summary CAGR using `(t.index[-1] - t.index[0]).days / 365.25` (actual TQQQ data endpoints).
- `audit_failed_bounce_canonical_independent.py` computes CAGR using `(END_DATE - START_DATE).days / 365.25`, i.e. requested 2010-01-01 to 2026-10-08, regardless of actual first TQQQ observation.
This explains why ending balances and drawdowns agree while CAGR differs. Do not treat CAGR difference as evidence of a return-path mismatch; standardize CAGR to actual first/last observation dates and disclose that period. The user requested a consistent date range, so the scripts should explicitly report requested range AND actual traded-data range, and both annualization formulas should use the same declared convention.


## Critical newly identified risk: QQQ event indices may be applied to TQQQ by row number, not date
At commit `87e74d008884d475248263a9510fa39ef300517c`, both `research/failed_bounce_robustness.py` and `research/audit_failed_bounce_canonical_independent.py` download QQQ and TQQQ separately from requested START=`2010-01-01`. They calculate event row indices from QQQ (`build_events(q)` / `events(q)`) and pass those integer indices to `build_signal(len(t), events)` / `build_signal(len(t), evs)` for TQQQ. No explicit join/reindex by calendar date is present in the inspected code paths.
Because TQQQ began trading after QQQ, QQQ's first available session and TQQQ's first available session are not the same. This creates a serious potential index-offset bug: event dates in the QQQ ledger may be correct, but the defensive signal can be applied to a different TQQQ session. The exact offset and impact must be confirmed using the actual workflow data; do not infer a corrected final balance without replaying.
This may be the remembered price/execution discrepancy that led to concern over the ~$4M result, but the original conversation has not been recovered, so that connection is a hypothesis, not a fact.
Required fix before any verification:
1. Join QQQ and TQQQ data explicitly on shared trading-date index (inner join), preserving a single date index.
2. Generate events on aligned QQQ observations and build the signal on that same aligned index.
3. Assert each shock/low/decision timestamp maps to the same date in the TQQQ table; assert no integer-only cross-symbol indexing.
4. Compare old vs aligned results using identical downloaded snapshots and print the first/last observation and all mapped execution dates.
5. Add regression test where QQQ contains extra leading dates before TQQQ; verify the event is mapped by date, not shifted by row count.
Until this replay is done, the ~$4.04M figure should be labelled REPRODUCIBLE UNDER THE EXISTING IMPLEMENTATION, BUT NOT TRUSTWORTHY AS A CORRECTLY DATE-ALIGNED BACKTEST.


## Audit correction — QQQ/TQQQ row-index misalignment hypothesis disproved by source inspection
On continuation review of the exact artifact revision `87e74d008884d475248263a9510fa39ef300517c`, both canonical scripts explicitly intersect their QQQ and TQQQ indices before generating events/signals:
```python
idx = q.index.intersection(t.index)
q = q.reindex(idx).dropna()
t = t.reindex(idx).dropna()
```
Therefore the earlier claim that these scripts directly used unaligned QQQ row numbers against TQQQ dates was an incorrect inference. Do not cite it as the cause of the original $4M rejection. Because the data downloads call `.dropna()` before intersection and then reindex to the shared index, their dates should match in the normal data path; explicit assertions have now been added to both scripts to enforce this.
Commits adding assertions:
- `3c11699ac45d35a6cd48bf8fc40ff2f182bab7e2` — `research/failed_bounce_robustness.py`
- `36bec88f8ec3d93cefbbf2750786d3e6f456a646` — `research/audit_failed_bounce_canonical_independent.py`
Important process note: the assistant previously stated a possible alignment defect before fully reading both scripts. This was a false alarm; explicitly retract it. The original historical reason for the $4M rejection remains unrecovered.
Next step is not to change strategy based on that disproved hypothesis. Continue with (1) regression tests/workflow after new alignment assertions, (2) shared frozen dataset + daily curve comparison, and (3) recover exact original rejection context / inspect any actual open/close/midday price discrepancy.


## Verification after explicit date-alignment assertions (2026-10-09 UTC)
- Added explicit post-intersection equality/length assertions in both canonical scripts; commits `3c11699` and `36bec88`.
- GitHub Actions successfully reran both robustness and independent audit on the changed code:
  - [Robustness run 37874744047](https://github.com/eklu654/Trading-Bot/actions/runs/37874744047): success.
  - [Independent audit run 37874744058](https://github.com/eklu654/Trading-Bot/actions/runs/37874744058): success; canonical $4,040,313, TQQQ buy-and-hold $2,094,669; 9 events.
  - Earlier commit's [independent audit run 37874731173](https://github.com/eklu654/Trading-Bot/actions/runs/37874731173): success; canonical $4,040,315, buy-and-hold $2,094,669; 9 events.
  - Earlier commit's [robustness run 37874731205](https://github.com/eklu654/Trading-Bot/actions/runs/37874731205): success.
- Thus the explicit alignment assertions passed and did not change the headline result. The previously raised row-index-offset concern is retracted; code already intersected/reindexed both series before building events.
- Remaining high-value work: (a) ensure research-tests run 37874744026 completes and passes; (b) make both scripts export daily equity curves and aligned input data with hashes, or create a single shared frozen-data artifact; (c) compare daily return/equity curves, not only final balances; (d) recover the exact earlier conversational rejection message if possible.
