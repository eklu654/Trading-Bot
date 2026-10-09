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


## Results

- Workflow passed: [run 37913598899](https://github.com/eklu654/Trading-Bot/actions/runs/37913598899).
- Artifact ID `11607946132`; SHA-256 `0e9e84b2492c26692a3c0f7194e8ae0cdb8d71f41f5bca5448e945de942d916a`.
- Actual TQQQ dates: 2010-02-11 through 2026-10-07, 4,189 rows; synthetic QQQ proxy dates: 1999-03-10 through 2026-10-07, 6,938 rows. Nine actual B0 events.
- Candidate re-evaluates every day while B0 remains defensive after a veto. The actual ledger shows the 2019 and COVID recovery attempts take 8 sessions from the low and pass the N=8/10 fast-recovery exception; the 2022-07-19 attempt took 21 sessions and was vetoed until the matrix cleared on 2022-08-10.

### Actual TQQQ comparison

| Rule | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return | COVID window | 2022 window |
|---|---:|---:|---:|---:|---:|---:|
| B0 canonical | $4,040,314 | 49.49% | -73.53% | -72.64% | +24.58% | -69.83% |
| Recovery gate, fast exception 5 sessions | $1,724,457 | 42.04% | -80.99% | -80.35% | -6.67% | -78.33% |
| Recovery gate, fast exception 8 sessions | $3,101,939 | 47.13% | -79.68% | -78.99% | +24.58% | -76.83% |
| Recovery gate, fast exception 10 sessions | $3,101,939 | 47.13% | -79.68% | -78.99% | +24.58% | -76.83% |

The 8- and 10-session variants preserve the COVID window but finish about 23.2% below B0, worsen max drawdown by about 6.1 percentage points, and worsen the 2022 window. The 5-session variant blocks the COVID rebound and performs substantially worse. Thus this recovery-gated rule is **REJECTED in its tested form**; no threshold is selected.

### Synthetic 3x QQQ diagnostic

| Rule | Ending balance | CAGR | Max drawdown | COVID window | 2022 window |
|---|---:|---:|---:|---:|---:|
| B0 canonical | $836,044 | 20.40% | -99.37% | +26.34% | -68.81% |
| Recovery gate, 5 sessions | $534,492 | 18.46% | -98.87% | -6.54% | -77.85% |
| Recovery gate, 8 sessions | $749,261 | 19.92% | -99.27% | +26.34% | -76.24% |
| Recovery gate, 10 sessions | $832,677 | 20.38% | -99.19% | +26.34% | -76.24% |

Synthetic series is not actual TQQQ and is not fully calibrated; these results are only signal diagnostics.

## Decision
This targeted “matrix only gates B0 recovery” implementation is better scoped than the rejected always-on overlay, but still does not improve the actual-TQQQ objective. The 2022 veto delays re-entry until the matrix clears, and the opportunity cost outweighs the avoided weakness in the full-period account. Do not deploy or keep tuning N on this same sample. Next useful question is whether a **bounded, short re-entry delay** (rather than waiting for DMA clearance) captures enough of the false-bounce protection without keeping TQQQ out for weeks. Treat any such follow-up as exploratory and do not select a winner from the inspected period.


## Same-input correction rerun
- Corrected run: [37914294832](https://github.com/eklu654/Trading-Bot/actions/runs/37914294832); artifact ID `11608866543`, SHA-256 `f1bfb2dbe565df8c3f2841bbcb60c280524a94f95fc17e576e864b2eba7b40db`.
- Live-period indicator features now use B0's frozen QQQ closes. Results match to displayed precision: N=8/10 end $3.102M vs B0 $4.040M and worsen drawdown/2022. Rejection remains.
