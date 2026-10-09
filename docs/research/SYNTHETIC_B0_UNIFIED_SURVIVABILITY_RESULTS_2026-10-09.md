# Unified Synthetic B0 Survivability — Corrected Results Audit (2026-10-09)

**Correction notice:** This version supersedes the initial version of this document. A follow-up accounting audit found that the initial synthetic return construction applied 3× independently to both overnight and intraday legs, introducing an extra compounding term. The code and tests have been corrected to model one daily leverage reset. A second audit found that the earlier DMA grid held candidate capital in cash during its warm-up while B0 used its full history. Earlier synthetic DMA-grid comparisons are therefore also superseded; the common-window matrix below is the valid comparison.

## Run and artifact provenance

- Corrected workflow: [TQQQ Dot-Com Survivability Research, run 37924281212](https://github.com/eklu654/Trading-Bot/actions/runs/37924281212), completed successfully.
- Corrected research code commit: `8a112f41be46f89519af2ea601d7720640355587`.
- Full research test suite: [run 37923205463](https://github.com/eklu654/Trading-Bot/actions/runs/37923205463), completed successfully: **133 passed, 1 existing warning**.
- Artifact: `tqqq-dotcom-survivability`, ID `11613132675`, SHA-256 `096407a3cb2f7d03be50b1cad100c225d44368b332c587c7001246c9652c21f5`.
- Frozen QQQ CSV SHA-256: `872fa74a650ce2668bbc0edaea9e3dfa1cd3525310480bdccaf65cf7fb51cb24`.
- Summary CSV SHA-256: `be20b24a15d3dd080feac27e81ca5aacefe2d33fb03aa2b12969b96ceb28a82c`.

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

## Common-window validation of the partial-DMA grid

The earlier DMA-grid result was not comparable to full-history B0 because the DMA candidates sat in cash during their warm-up while B0 compounded from the start. The matrix was corrected to compute all signals on the full frozen input, then start every strategy with $5,000 on the same date after the longest 250-session lookback. B0 is now included as a control in the same matrix.

- Synthetic common-window run: [run 37924504497](https://github.com/eklu654/Trading-Bot/actions/runs/37924504497), artifact ID `11612893692`, ZIP SHA-256 `a90965ffd3f246f25d7ec843dd3fcb3f302b86d6104b9b32c07fff070c446445`, CSV SHA-256 `997216fddf4d07f0ba8485a93d628b62ebdf7765465aec7045daa37dd8e81e36`.
- Common synthetic window: 2000-03-03 through 2026-10-02, 6,686 sessions, $5,000 starting balance.

| Synthetic candidate | Ending balance | CAGR | Max drawdown | Average exposure |
|---|---:|---:|---:|---:|
| 250-DMA, 25% below DMA | $341,120.74 | 17.22% | -93.38% | 81.44% |
| 250-DMA, 0% below DMA | $323,434.23 | 16.98% | -86.99% | 75.25% |
| B0 shock/recovery | $253,404.68 | 15.91% | -99.34% | 89.66% |
| Synthetic 3× QQQ buy-and-hold | $9,602.65 | 2.49% | -99.96% | 100.00% |

On this common synthetic window, 250-DMA/25% ends about 34.6% above B0 and improves max drawdown by about 5.97 percentage points. This is the best-ending row selected from an in-sample grid, so the result is exploratory and subject to selection bias.

### Same candidate on actual TQQQ

The actual-TQQQ matrix uses its own shared warm-up window of 2011-02-07 through 2026-10-02 and $5,000 starting capital. The B0 control is computed from the full QQQ signal history, then evaluated over the same date range as every DMA row.

- Actual-TQQQ run: [run 37924045646](https://github.com/eklu654/Trading-Bot/actions/runs/37924045646), artifact ID `11613400799`, ZIP SHA-256 `e153dce449cffc04123b2db379f475b798122d51caeacdf66967dde18fea5bb6`, CSV SHA-256 `f0f6f9627677741ee9db4901d7a25a1c3215d570d8d0d5af03ef2c4ab5d2d28a`.

| Actual-TQQQ strategy | Ending balance | CAGR | Max drawdown | Average exposure |
|---|---:|---:|---:|---:|
| B0 shock/recovery | $1,816,680.16 | 45.75% | -73.53% | 93.04% |
| Buy-and-hold | $941,843.07 | 39.76% | -81.66% | 100.00% |
| 250-DMA, 25% below DMA | $357,926.19 | 31.38% | -67.42% | 89.90% |

The 250-DMA/25% candidate has a materially smaller actual-TQQQ drawdown, but its ending wealth is about **80.3% below B0** on the same date range; B0 ends about **5.08 times higher**. It therefore fails the primary wealth-retention gate. The synthetic result does not justify replacing B0 or promoting the 250-DMA rule.

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
