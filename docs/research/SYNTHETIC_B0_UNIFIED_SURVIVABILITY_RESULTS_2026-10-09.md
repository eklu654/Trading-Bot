# Unified Synthetic B0 Survivability — Corrected Results Audit (2026-10-09)

**Correction notice:** This version supersedes the initial version of this document. A follow-up accounting audit found that the initial synthetic return construction applied 3× independently to both overnight and intraday legs, introducing an extra compounding term. The code and tests have been corrected to model one daily leverage reset. Do not use the prior version's result figures.

## Run and artifact provenance

- Corrected workflow: [TQQQ Dot-Com Survivability Research, run 37923204992](https://github.com/eklu654/Trading-Bot/actions/runs/37923199785), completed successfully.
- Corrected research code commit: `3ec8f679b1ecb57dbb738965b80be7b44ccc7c54`.
- Full research test suite: [run 37923205463](https://github.com/eklu654/Trading-Bot/actions/runs/37923205463), completed successfully: **131 passed, 1 existing warning**.
- Artifact: `tqqq-dotcom-survivability`, ID `11612419144`, SHA-256 `1dc4292720f1779969f4d7518cbd4f14369b0db45bfe4fb3823abd0e3cfd13fc`.
- Frozen QQQ CSV SHA-256: `dc1a36980348aa568455402c1c64c78a66db2919a6bdf45112dd5e287fb4edb7`.
- Summary CSV SHA-256: `73113d46f87396873fd1cff99b3d8d5f91be8eb59283c8371c42f2898b23d532`.

## Frozen common methodology

- Starting balance: $5,000.
- QQQ adjusted-price input: 1999-03-10 through 2026-10-08, 6,939 sessions; one QQQ download is shared by both strategies.
- The synthetic daily-reset 3× proxy uses QQQ adjusted overnight and intraday returns. The overnight leveraged gross return is `max(0, 1 + 3*r_overnight)`. Given the overnight move, the intraday leverage ratio is adjusted to `3*(1+r_overnight)/(1+3*r_overnight)`; this avoids resetting leverage twice. Without clipping, the combined return equals 3× QQQ's close-to-close daily return. If the synthetic proxy is wiped out overnight, it remains at zero.
- Both B0 and synthetic buy-and-hold use the same synthetic return legs and shared `research/causal_execution.py` close-to-next-open engine.
- B0 signals on QQQ adjusted-close daily returns <= -4.5%, goes defensive at the next open, tracks the post-trigger running low, and restores exposure after a 10% rebound from that low. Buy-and-hold stays fully exposed.
- No actual TQQQ existed in 2000. The proxy does not model actual TQQQ fees, financing, tracking error, fund operations, spreads, or borrow costs. It is a stress diagnostic, not actual TQQQ history or a forecast.

## Apples-to-apples results

| Metric | B0 shock/recovery | Synthetic 3× QQQ buy-and-hold |
|---|---:|---:|
| Ending balance | $861,126.36 | $64,245.39 |
| CAGR | 20.52399% | 9.69935% |
| Full-period max drawdown | -99.34403% | -99.95639% |
| Minimum equity | $126.98 | $16.62 |
| Minimum-equity date | 2009-03-09 | 2009-03-09 |
| First crossing of -99% drawdown | 2002-09-23 | 2001-04-03 |
| First crossing of -99.9% drawdown | Not crossed | 2002-07-23 |
| Equity reached zero | No | No |
| Average target exposure | 89.77% | 100.00% |

## 2000–2002 dot-com window

| Metric | B0 shock/recovery | Synthetic 3× QQQ buy-and-hold |
|---|---:|---:|
| 2000-window start to 2002-window end return | -98.36% | -99.85% |
| Trough date | 2002-10-09 | 2002-10-09 |
| Trough equity | $162.99 | $23.27 |
| Drawdown from prior peak to trough | -99.15798% | -99.93894% |
| Prior peak date | 2000-03-27 | 2000-03-27 |
| Prior peak recovered by end of sample? | Yes, 2018-01-05 | Yes, 2025-10-06 |

## Regime-level exposure diagnostic

| Window | Strategy | Average target exposure | Cash-target sessions | Window return | Minimum equity in window | Window max drawdown |
|---|---|---:|---:|---:|---:|---:|
| 2000–2002 | B0 | 50.93% | 369 / 752 | -98.36% | $162.99 | -99.158% |
| 2000–2002 | Synthetic buy-and-hold | 100.00% | 0 / 752 | -99.85% | $23.27 | -99.939% |
| 2007–2009 | B0 | 89.81% | 58 / 569 | -55.02% | $126.98 | -99.344% |
| 2007–2009 | Synthetic buy-and-hold | 100.00% | 0 / 569 | -65.97% | $16.62 | -99.956% |
| 2020 | B0 | 73.28% | 62 / 232 | +107.21% | $32,782.20 | -47.142% |
| 2020 | Synthetic buy-and-hold | 100.00% | 0 / 232 | +91.85% | $1,948.58 | -94.887% |
| 2022 | B0 | 62.95% | 93 / 251 | -69.54% | $58,296.37 | -72.437% |
| 2022 | Synthetic buy-and-hold | 100.00% | 0 / 251 | -78.22% | $3,987.80 | -89.536% |

## Interpretation

1. **B0 did not hit -99.9% drawdown or zero in this corrected unified replay.** It did cross -99% drawdown in September 2002. Its dot-com trough was about $162.99 from a prior peak of about $19,356.98. It later suffered its overall minimum of about $127 during the 2008–2009 crisis, at a full-period drawdown of -99.3440%.
2. **“Survives” is a weak pass condition.** The synthetic B0 control nearly lost everything in this model. It eventually recovered its prior dot-com peak in January 2018 and compounded to about $861k by October 2026, but the drawdown from its peak was extreme.
3. Synthetic buy-and-hold crossed -99.9% drawdown in July 2002 and fell to about $16.62 in March 2009. B0 finished about 13.4 times higher and avoided the -99.9% threshold in this same-engine comparison, but still experienced a -99.34% full-period drawdown.
4. B0's fast-shock rule reduced exposure during parts of the dot-com decline, but it was invested about 89.8% of the 2007–2009 window and still reached its full-period minimum during the GFC. The rule does not reliably detect a slow bear market. Conversely, it preserved strong modeled rebound participation in 2020 and reduced losses in 2022; these are descriptive in-sample results, not validation of a new overlay.
5. The synthetic daily-reset proxy is an uncalibrated model. Even with corrected daily leverage math, its results should be treated as stress evidence, not as a guarantee about an actual brokerage account.

## Reconciliation to earlier notes

The prior `NEAR_RUIN_DEFENSE_GATE_CONTINUATION_2026-10-09.md` recorded a separate synthetic B0 run ending around $836k with -99.372% full-period drawdown and -99.1484% dot-com-window drawdown. Those values came from a different synthetic return/execution implementation and are not numerically interchangeable. This corrected common-engine replay is now the preferred comparison for B0 versus synthetic buy-and-hold because both use the same frozen input and causal execution path. Keep prior audits intact as historical provenance.

## Decision / next gate

- Keep actual-TQQQ B0 as the modern-period control; do not imply its modern drawdown is representative of pre-2010 synthetic stress.
- The corrected synthetic result does not justify paper/live deployment. It confirms a near-ruin tail even without crossing -99.9% in the B0 replay.
- Any protective overlay must be preregistered and evaluated against both the modern actual-TQQQ compounding record and this synthetic stress path, with 0/10/25/50-bp transition-cost stress, COVID rebound retention, 2022 behavior, and chronological holdout results.
