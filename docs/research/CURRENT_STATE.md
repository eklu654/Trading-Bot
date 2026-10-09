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