# Re-entry Isolation Results — Initial Run Audit (2026-10-09)

## Run and artifact
- Workflow: [Re-entry isolation experiment, run 37921554325](https://github.com/eklu654/Trading-Bot/actions/runs/37921554325)
- Commit tested: `0aad7d8a3b90631dc405de8be0b4551d26487f01`
- Result: workflow succeeded; state-transition tests, backtest, and artifact upload all succeeded.
- Artifact: `reentry-isolation-results`, ID `11612082869`, SHA-256 `a707bfd60dc5a6e17aaf7bb011eca69fba8aa706d5836dbff1fc2989141700a3`.
- Research tests: [run 37921554321](https://github.com/eklu654/Trading-Bot/actions/runs/37921554321), successful.

## Zero-cost comparison (exploratory)
| Candidate | Ending balance | CAGR | Max drawdown | Worst 252-session return | Avg target exposure |
|---|---:|---:|---:|---:|---:|
| B0 | $4,040,316 | 49.49% | -73.53% | -72.64% | 93.46% |
| R1 | $3,661,416 | 48.61% | -81.15% | -80.51% | 99.57% |
| R2 | $3,039,513 | 46.95% | -77.14% | -76.37% | 95.57% |

Start balance $5,000. Costs are one-way exposure-change costs; the artifact includes 0, 10, 25, and 50 bps. At 10/25/50 bps the B0 ending balances were $3,964,237 / $3,852,659 / $3,673,279; R1 was $3,535,421 / $3,354,291 / $3,072,253; R2 was $2,964,441 / $2,855,202 / $2,681,772.

## Interpretation
- On this full sample, neither faster-re-entry candidate improved terminal wealth or drawdown over B0.
- R1 ended about 9.4% below B0 and worsened max drawdown by about 7.62 percentage points.
- R2 ended about 24.8% below B0 and worsened max drawdown by about 3.60 percentage points.
- The result cautions against treating time spent in cash as the main defect; re-entering before a selloff has stabilized can restore exposure into renewed losses.

## Important preregistration deviation / caveat
The preregistration is at [REENTRY_ISOLATION_EXPERIMENT_PREREG_2026-10-09.md](REENTRY_ISOLATION_EXPERIMENT_PREREG_2026-10-09.md). The implementation includes a renewed-shock reset that forces exposure to zero and resets the staged R2 tranche on another QQQ daily return <= -4.5%. That reset was added to prevent immediate re-entry during consecutive shock sessions. However, the preregistration says that after R2's +5% tranche is entered, it is not reduced merely because QQQ subsequently falls. The implementation and preregistration are therefore not fully identical for R2. Treat the reported R2 result as exploratory, not as a clean preregistered confirmation. R1 also has the renewed-shock exception, so it is an immediate-re-entry-with-renewed-shock-guard variant rather than an unconditional next-open re-entry.

## Accounting and data notes
- Workflow log reports that the 0-bps cost-helper equity reconciles to causal daily returns for B0/R1/R2.
- Same frozen aligned QQQ/TQQQ input files were used for all candidates.
- These figures are historical backtest results, not a guarantee of future results. Any synthetic pre-inception proxy must remain separately reported from actual TQQQ.

## Decision
B0 remains the control. Reject R1 and R2 as replacements on these results. Before another candidate is tested, either update the preregistration to match the renewed-shock reset before a fresh run, or implement the originally preregistered R2 behavior exactly and run a separately identified test. Do not tune thresholds based on the event outcomes in this run.
