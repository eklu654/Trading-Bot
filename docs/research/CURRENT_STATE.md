# Trading-Bot Research — Current State

**Last updated:** 2026-10-08  
**Active investigation:** Reverify the QQQ shock/recovery TQQQ strategy family.  
**Starting capital:** $5,000.

## Active baseline (user-confirmed, exact rule still being recovered)
The user's remembered current baseline is approximately **$3.3M**, based on a QQQ daily-drop trigger and +10% recovery from the post-shock low, plus an additional anti-bear-rally rule. The exact anti-fakeout rule must be recovered from prior source history/logs before treating any matrix row as the original frozen baseline. Do not substitute the simple ~$4.04M strategy for this baseline.

## Results status
- **~$3.337M structural-matrix result: INVALID AS ORIGINALLY IMPLEMENTED; FIXED VERSION RUNNING.** The original `research/failed_bounce_structural_matrix.py` skipped events labelled `censored`, where the label depended on up to 252 future sessions. This made future outcomes gate whether a qualifying event was traded. Commit `773c06b0621562497c6e47394fb267f214b788e6` removes that skip so labels are diagnostics only. The original $3.337M output must not be reused as the corrected result. Workflow runs triggered by this commit must finish and be inspected.
- **~$4.04M canonical shock/+10% result: PROVISIONAL / NOT APPROVED.** This is the simpler QQQ -4.5% daily shock, defensive until +10% off the post-shock low, using actual TQQQ returns. It does not include the remembered anti-bear-rally filter. Needs exact-window, event-ledger and chronological validation.
- **Independent audit alignment correction:** Previous note claiming the independent audit failed to align QQQ/TQQQ event indices was incorrect. `research/audit_failed_bounce_canonical_independent.py` explicitly intersects QQQ and TQQQ indexes before event construction. Do not repeat the prior misdiagnosis. Its explicit overnight/intraday loop appears consistent with close[t] signal -> open[t+1] execution; still compare its daily equity curve with `causal_execution.py` to establish exact agreement.
- **~$3.7M Fed/DMA synthetic-history result: NOT THE SAME STUDY.** Do not use it as evidence for actual-TQQQ shock/recovery performance.
- **Historical reason the ~$4M result was previously withdrawn:** not recovered yet; don't invent it.

## Latest code change
- Commit `773c06b0621562497c6e47394fb267f214b788e6`: removed the future-label `censored` skip from `signal_for_rule()`; future outcome labels are now diagnostic only and do not gate trade eligibility.
- Push triggered research workflows including:
  - structural matrix: https://github.com/eklu654/Trading-Bot/actions/runs/37862580078
  - independent audit: https://github.com/eklu654/Trading-Bot/actions/runs/37862580071
  - robustness: https://github.com/eklu654/Trading-Bot/actions/runs/37862580103
  - feature audit: https://github.com/eklu654/Trading-Bot/actions/runs/37862580158
  - research tests: https://github.com/eklu654/Trading-Bot/actions/runs/37862580050
  These were queued at last inspection; inspect their final status and artifacts before relying on results.

## Source files inspected
- `research/failed_bounce_structural_matrix.py` — blob `0ffb403cb29609a0ba4ade92ec9517ec11d722f1` after fix
- `research/failed_bounce_robustness.py` — blob `753ecc24f8df11406601495c2427e457fcd7be22`
- `research/audit_failed_bounce_canonical_independent.py` — blob `740d3bb7f71a9c143efe61b153b91c940cc39c80`
- `research/failed_bounce_strategy_walkforward.py` — blob `e6f7cd1103ab749b5cc20ca6a97726ad3095e325`
- `research/causal_execution.py` — blob `caf48a0f64b0485021cf27adf0d822ab795735ae`
- Detailed checkpoint: `docs/research/TQQQ_SHOCK_RECOVERY_REVERIFICATION_LOG_2026-10-08.md`

## Mandatory next steps
1. Inspect the corrected matrix and test workflow results/artifacts; record the new ending balance and matched buy-and-hold control.
2. Verify the independent audit and `causal_execution.py` produce the same daily equity series over the exact same aligned index; resolve any differences before interpreting $4.04M.
3. Recover the exact frozen anti-bear-rally rule that produced the user's remembered ~$3.3M baseline; don't infer the rule from the best current matrix row.
4. Reconstruct both baseline and simple $4M candidate on one aligned QQQ/TQQQ frame, identical dates, price basis, $5,000 start, and close-to-next-open execution.
5. Generate dated event/trade ledger and tests proving no future label is referenced by signal construction.
6. Run chronological holdouts only after rules are frozen; no winner selection on the holdout period.
7. Record every meaningful research action, exact outputs, commit SHA, workflow run ID, result status and next step here before switching tasks or ending a work session.

## Context-preservation rule
Before any new experiment, read this file and the detailed checkpoint. After every meaningful step, commit the current rules, exact output/result, status (VERIFIED / PROVISIONAL / REJECTED / UNVERIFIED), reason, commit SHA, workflow run ID, and next step. Never silently replace prior findings. At the end of every work session, update this file first.