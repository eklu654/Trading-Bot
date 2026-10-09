# Recovery-gated structural confirmation — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; workflow pending.**

## Rationale
The prior matrix was applied continuously and blocked B0 re-entry on successful fast rebounds (notably 2019-01-07 and 2020-03-26). The new candidate uses the matrix only at B0's +10% recovery decision; it does not reduce exposure during ordinary B0-held periods. If a slow recovery is vetoed, the strategy stays defensive, tracks any new low, and reevaluates the next +10% recovery attempt.

## Rule
- B0 trigger: QQQ adjusted-close daily return <= -4.5%; track post-trigger low; recovery condition is close >= 10% above the running low.
- At a recovery attempt, compute the frozen structural condition (QQQ below 150-DMA AND 100-DMA below 150-DMA) and fast-shock condition (QQQ below 100-DMA AND at least one of 63-session return <= -20%, 252-session drawdown <= -20%, VIX >= 30).
- If neither flag is true, honor B0 recovery.
- If either flag is true, honor recovery anyway when sessions from the current running low to this recovery attempt are <= N (fast-rebound exception).
- Otherwise veto the recovery and remain defensive; if a new low occurs, reset the running low and wait for a fresh +10% rebound before reassessment.
- Sensitivity points: N = 5, 8, 10 trading sessions. This small sensitivity set is exploratory and in-sample; do not select a production threshold from it.

## Controls and metrics
- B0 unchanged, same $5,000 initial capital, same actual TQQQ aligned input and next-open execution.
- Also run a separately labeled hypothetical 3x QQQ proxy from 1999 for regime diagnostics only.
- Compare final balance, CAGR, max drawdown, worst rolling 252-session return, COVID/2022 windows, and the full recovery-attempt ledger (including veto/release reason).
- Synthetic history is not actual TQQQ. No candidate is production-ready based on this in-sample run.

## Audit
- Code: `research/canonical_recovery_gate.py`
- Workflow: `.github/workflows/canonical-recovery-gate.yml`
- Code commit: `8d2684084dbad1cb416b45299aae1fe77905f76f`
- Workflow commit: `dacb52f60e206de1a364bc767d97436ccd98a9ac`
- Append workflow, artifact, and result summary when complete.
