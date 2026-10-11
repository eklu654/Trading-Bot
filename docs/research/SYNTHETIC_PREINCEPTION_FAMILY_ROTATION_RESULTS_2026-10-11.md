# Synthetic Pre-Inception Family-Rotation Stress — Results (2026-10-11)

## Validated run
- **Workflow:** [run 38124303767 — success](https://github.com/eklu654/Trading-Bot/actions/runs/38124303767)
- **Commit:** `160e9b490d4c89eea61d2d526e3f30cf3024f0eb`
- **Artifact:** `synthetic-preinception-family-rotation`, ID `11696865319`, SHA-256 `0f528a8224c9ee402f4735916bd7eee55849cef48c1f09ff0591ddf01bfefc18` (expires 2026-11-10)
- Tests passed, including the B0 close-signal/next-session exposure state test. This report uses the final corrected run after fixing the test dependency, lagging the financing yield, standardizing price returns, making the first scored session return zero, and adding the fixed B0 comparison. Earlier runs with different accounting/model assumptions are superseded.

## Scope and assumptions
- Evaluation: 2000-03-08 through 2002-12-31, 707 sessions, $5,000 starting equity. Start is the first common session with all five prior-close 250-session moving averages available.
- Benchmark families: SPY, QQQ, ^SOX, DIA, ^RUT. Signals use prior-close benchmark price versus prior-close 250-DMA; rank eligible families by distance above DMA; equal-weight top two; rebalance every five common sessions.
- Synthetic 3x daily-reset return: `3 × benchmark price return − 2 × prior-close ^IRX yield / 252 − 0.95% / 252`. Wealth is absorbing at zero. A 25 bps turnover-cost sensitivity is included.
- Price returns are used for all five families, consistently excluding dividends. These are synthetic daily-reset proxies, **not actual TQQQ, SOXL, SPXL, UDOW, or TNA returns**. There is no tracking error, actual fund financing agreement, fund liquidation/creation mechanism, or execution microstructure.

## Results
| Control | Cost | Ending $5,000 | Max drawdown | Peak date → trough date | Worst rolling 252-session return | Below $50? | Below $5? |
|---|---:|---:|---:|---|---:|---|---|
| Synthetic DMA250/top-2/C5 family rotation | 0 bps | $239.40 | -95.86% | 2000-03-10 → 2002-06-03 | -87.96% | No | No |
| Synthetic DMA250/top-2/C5 family rotation | 25 bps | $218.65 | -96.20% | 2000-03-10 → 2002-06-04 | -88.32% | No | No |
| Synthetic canonical B0 shock/recovery approximation | 0 bps | $89.22 | -99.13% | 2000-03-27 → 2002-10-09 | -89.58% | Yes, 2002-10-09 | No |
| Synthetic canonical B0 shock/recovery approximation | 25 bps | $80.72 | -99.21% | 2000-03-27 → 2002-10-09 | -90.07% | Yes, 2002-10-03 | No |
| Synthetic 3x QQQ buy-and-hold | 0 bps | $4.53 | -99.95% | 2000-03-27 → 2002-10-09 | -99.15% | Yes, 2001-04-03 | Yes, 2002-07-23 |
| Synthetic 3x QQQ buy-and-hold | 25 bps | $4.52 | -99.95% | 2000-03-27 → 2002-10-09 | -99.15% | Yes, 2001-04-03 | Yes, 2002-07-23 |
| Static equal-weight 1x benchmark basket | 0 bps | $2,588.79 | -58.26% | 2000-03-24 → 2002-10-09 | -41.34% | No | No |

### Family-rotation path
| Date | No-cost equity | 25 bps equity |
|---|---:|---:|
| 2000 year-end | $767.05 | $747.78 |
| 2001 year-end | $556.55 | $526.55 |
| 2002 year-end | $239.40 | $218.65 |

Average family-rotation exposure was about 50.9%. Despite being in cash for roughly half of the sessions, the strategy lost about 96% of its account value over the prolonged bear. The drawdown peak was just after the dot-com peak, and the account had not recovered by the end of 2002.

The fixed B0 shock/recovery approximation averaged 50.35% exposure, nearly the same as the family selector's 50.92%, but ended at only $89.22 (0 bps) / $80.72 (25 bps) and drew down 99.13% / 99.21%. It crossed below $50 on 2002-10-09 at zero cost and 2002-10-03 at 25 bps, but did not cross $5. This is a close-to-close approximation, not the exact canonical next-open B0 execution. It suggests that the daily shock/recovery rule alone did not protect the synthetic portfolio from the prolonged 2000–2002 bear under this model.

The synthetic QQQ proxy's own wealth path, compounded from the QQQ data start in 1999 (not from the $5,000 evaluation start), ended at 0.555% of its original proxy wealth and reached a -99.95% drawdown. The synthetic semiconductor proxy reached about -99.99% drawdown and ended at 0.340% of its original proxy wealth. Neither proxy crossed zero in this sample, but both came extremely close to total loss. Those proxy-wealth percentages are not account balances and should not be confused with the $5,000 portfolio comparison above.

## Interpretation
1. **The frozen family selector did not hit modeled zero, but its -96.2% drawdown is still near-ruin territory.** At 25 bps, $5,000 fell to about $219. This is not acceptable evidence for unattended deployment.
2. **The fixed B0 approximation also came close to ruin**: $5,000 fell to about $81 at 25 bps with a 99.21% max drawdown. Its shock/recovery mechanism did not protect this synthetic path enough to avoid a near-total loss.
3. **The family selector outperformed both B0 and synthetic 3x QQQ buy-and-hold in this single stress window**, ending at about $219 vs $81 and $4.52 at 25 bps. But a 96.2% drawdown is still catastrophic, and the B0 comparison uses close-to-close synthetic execution rather than the actual next-open convention.
4. **Cash exposure helped, but not enough.** About 51% average exposure did not prevent a prolonged loss because selected leveraged proxies suffered extreme path-dependent decay.
5. **The 1x basket also lost materially**, ending at $2,589 with -58.3% max drawdown. Some loss is from the underlying bear market; leverage and daily-reset compounding magnified it substantially.
6. **Do not tune the selector to 2000–2002.** This is one pre-inception stress case, not a portfolio design target and not a validated reconstruction of actual leveraged ETFs. It is evidence that any candidate needs an explicit account-level survivability gate in addition to terminal-wealth comparison.

## Decision / next step
No candidate is promoted. Do not expand the DMA/top-N/cadence/cap search. The same-model B0 comparison is now complete and does not justify tuning either rule to this event. The already-tested V30/L20/DD20–30 overlays show the known tradeoff: materially smaller drawdowns but dramatically lower ending wealth in actual-era account replay. Next, retain these as historical stress evidence and require any future candidate to meet a predeclared survivability gate across multiple regimes plus actual-era terminal-wealth and execution tests. Any pre-inception result remains synthetic and diagnostic.

## Provenance
- Input SHA-256: DIA `5dd74284025ed7f801f0059126315a3070045819c4f8d4e222e860182d9f1078`; ^IRX `f0a785c5674c13442e54d69626284a9e513aef6e12df49b257567cab153b9068`; QQQ `78c019c89ef247f61c4aa710cf10cb583aa83211176ba8a858030b7f53278c03`; ^RUT `60932a051a942c08b42de0bb1aa0492cb6fcec46f971f8f1daa3a266e37ad8ff`; ^SOX `25a8d7274521cf56c798a9bc182b1150987e3b80d560a98a6bc56c1577b53088`; SPY `7c6f9cbf2533386c244ab142ebe39ae5fc1847a93c6318e2abd42eed317d890b`.
- Summary SHA-256: `3f2976b092bb794f779e7943ac3b1fb6df749920a14bdc8e88254df5d85a2cab`
- Equity SHA-256: `cc82901731da8f4166e6d90c8463c6bde5915b9036c6cb0eb37625667de935e4`
- Weights SHA-256: `4e7fb8c172beae1ee1f5752dbdb88f899f79fe5180c3b861c56b428813c8c305`
- Proxy returns SHA-256: `6608946b3d0b201984b57016ca69bff4a4f24dd55b5980fdc54748b9bbda7941`
- Artifact ZIP SHA-256: `0f528a8224c9ee402f4735916bd7eee55849cef48c1f09ff0591ddf01bfefc18`
