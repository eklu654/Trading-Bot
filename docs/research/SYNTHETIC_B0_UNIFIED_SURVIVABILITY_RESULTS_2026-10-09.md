# Unified Synthetic B0 Survivability — Results Audit (2026-10-09)

## Run and artifact provenance

- Workflow: [TQQQ Dot-Com Survivability Research, run 37922871659](https://github.com/eklu654/Trading-Bot/actions/runs/37922871659), completed successfully.
- Code commit: `ed17d79a7de7123290e99df6e7d7f7a1c4e6757d`.
- Research tests: [run 37922871498](https://github.com/eklu654/Trading-Bot/actions/runs/37922871498), completed successfully; this included the new unit tests for the unified calculation.
- Artifact: `tqqq-dotcom-survivability`, ID `11612890699`, SHA-256 `bcf8a0f6c8efdfbbb587e41f0361f30ca0d40d5f63bd143f9458a2f6e9a2d6f3`.
- Frozen QQQ CSV SHA-256: `a392a84b15f9acedfece990b23302241b712306bbbba930f1f6c8822c0492a36`.
- Summary CSV SHA-256: `7356207cdfc07f442d541550bf1d31a15ec6b4c6faf152aecd32aabc61edba00`.

## Frozen common methodology

- Starting balance: $5,000.
- QQQ adjusted-price input: 1999-03-10 through 2026-10-08, 6,939 sessions; one QQQ download is shared by both strategies.
- Synthetic 3x exposure is calculated from QQQ adjusted overnight and intraday returns, each multiplied by 3 and floored at -100%. This clipping prevents a leveraged leg from losing more than 100%; if equity reaches zero it cannot recover. The model does not include actual TQQQ fees, financing, tracking error, fund operations, spreads, or borrow costs.
- Both B0 and synthetic buy-and-hold use the same synthetic overnight/intraday return legs and the shared `research/causal_execution.py` close-to-next-open engine.
- B0 signals on QQQ adjusted-close daily returns <= -4.5%, goes defensive at the next open, tracks the post-trigger running low, and restores exposure after a 10% rebound from that low. Buy-and-hold stays fully exposed.
- These are synthetic pre-inception stress results, not actual TQQQ history and not a claim that a reconstructed proxy exactly matches the fund.

## Apples-to-apples results

| Metric | B0 shock/recovery | Synthetic 3x QQQ buy-and-hold |
|---|---:|---:|
| Ending balance | $757,425.43 | $58,182.00 |
| CAGR | 19.96% | 9.31% |
| Full-period max drawdown | -99.4074% | -99.9618% |
| Minimum equity | $113.87 | $14.61 |
| Minimum-equity date | 2009-03-09 | 2009-03-09 |
| First crossing of -99% drawdown | 2002-09-23 | 2001-04-02 |
| First crossing of -99.9% drawdown | Not crossed | 2002-07-23 |
| Equity reached zero | No | No |
| Average target exposure | 89.77% | 100.00% |

## 2000–2002 dot-com window

| Metric | B0 shock/recovery | Synthetic 3x QQQ buy-and-hold |
|---|---:|---:|
| 2000-window start to 2002-window end return | -98.44% | -99.86% |
| Trough date | 2002-10-09 | 2002-10-09 |
| Trough equity | $154.41 | $21.50 |
| Drawdown from prior peak to trough | -99.1964% | -99.9438% |
| Prior peak date | 2000-03-27 | 2000-03-27 |
| Prior peak recovered by end of sample? | Yes, 2018-01-22 | Yes, 2025-10-28 |

## Regime-level exposure diagnostic

| Window | Strategy | Average target exposure | Cash-target sessions | Window return | Minimum equity in window | Window max drawdown |
|---|---|---:|---:|---:|---:|---:|
| 2000–2002 | B0 | 50.93% | 369 / 752 | -98.44% | $154.41 | -99.196% |
| 2000–2002 | Synthetic buy-and-hold | 100.00% | 0 / 752 | -99.86% | $21.50 | -99.944% |
| 2007–2009 | B0 | 89.81% | 58 / 569 | -55.05% | $113.87 | -99.407% |
| 2007–2009 | Synthetic buy-and-hold | 100.00% | 0 / 569 | -66.01% | $14.61 | -99.962% |
| 2020 | B0 | 73.28% | 62 / 232 | +110.91% | $29,178.29 | -46.66% |
| 2020 | Synthetic buy-and-hold | 100.00% | 0 / 232 | +102.44% | $1,776.60 | -95.356% |
| 2022 | B0 | 62.95% | 93 / 251 | -69.69% | $52,279.01 | -72.593% |
| 2022 | Synthetic buy-and-hold | 100.00% | 0 / 251 | -78.18% | $3,714.93 | -90.288% |

This reinforces a structural weakness: B0 is often defensive during the fast dot-com shock phase, but it was exposed about 89.8% of the 2007–2009 window and still reached its overall minimum during the GFC. A daily shock threshold does not reliably detect a slow bear market. Conversely, B0's lower exposure improved the modeled 2022 decline while preserving substantial 2020 recovery participation. This is descriptive in-sample evidence only, and it does not validate a new overlay.

## Interpretation

1. **B0 did not hit -99.9% drawdown or zero in this unified replay.** It did cross -99% drawdown in September 2002 and its dot-com trough was about $154 from a prior peak of about $19,215. It later suffered its overall minimum of about $114 during the 2008–2009 crisis, at a full-period drawdown of -99.4074%.
2. **“Survives” is a very weak pass condition.** The synthetic B0 control nearly lost everything in this model. It eventually recovered its prior dot-com peak in 2018 and compounded to about $757k by October 2026, but a live account that fell to roughly $114 from a peak near $19k would face severe behavioral, operational, and account-maintenance risks.
3. Synthetic buy-and-hold crossed -99.9% drawdown in July 2002 and fell to about $14.61 in March 2009. B0 finished about 13.0 times higher and avoided the -99.9% threshold in this same-engine comparison, but still experienced a -99.41% full-period drawdown.
4. No synthetic daily-reset series is actual TQQQ. The clipping convention, execution model, and absence of product costs materially affect the tail. The result should be treated as a stress diagnostic, not a forecast or proof of survival in a real brokerage account.

## Reconciliation to prior notes

The prior `NEAR_RUIN_DEFENSE_GATE_CONTINUATION_2026-10-09.md` recorded a separate synthetic B0 run ending around $836k with -99.372% full-period drawdown and -99.1484% dot-com-window local drawdown. Those figures came from a different synthetic return/execution implementation and are **not numerically interchangeable** with this new common-engine replay. Keep the old audit intact as historical provenance; use this unified replay for the specific apples-to-apples B0 versus buy-and-hold question going forward. Any additional candidate should be added to this same script and run on the same frozen input/engine before being compared.

## Decision / next gate

- Keep actual-TQQQ B0 as the modern-period control; do not imply that its modern drawdown is representative of pre-2010 synthetic stress.
- The synthetic result does not justify paper/live deployment. It confirms a near-ruin tail even without crossing -99.9% in the unified run.
- Before considering a protective overlay, require a pre-registered candidate that improves the synthetic tail without surrendering the modern actual-TQQQ compounding advantage; report 0/10/25/50-bp transition-cost stress, COVID rebound retention, 2022 behavior, and chronological holdout results.
