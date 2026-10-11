# Synthetic Pre-Inception Family-Rotation Stress — Results (2026-10-11)

## Validated run
- **Workflow:** [run 38124147212 — success](https://github.com/eklu654/Trading-Bot/actions/runs/38124147212)
- **Commit:** `e9177d79f609adf0b61cbeffdb4738b9e6f8e568`
- **Artifact:** `synthetic-preinception-family-rotation`, ID `11696760343`, SHA-256 `053949741d07342f6d99d60dc796037a5d9cba8fa50e97a5955854cb9d388290` (expires 2026-11-10)
- Tests passed. This report uses only the final corrected run after fixing the test dependency, lagging the financing yield, using a common price-return convention, and adding max-drawdown/year-end diagnostics. Earlier successful runs with different inputs/conventions are superseded.

## Scope and assumptions
- Evaluation: 2000-03-08 through 2002-12-31, 707 sessions, $5,000 starting equity. Start is the first common session with all five prior-close 250-session moving averages available.
- Benchmark families: SPY, QQQ, ^SOX, DIA, ^RUT. Signals use prior-close benchmark price versus prior-close 250-DMA; rank eligible families by distance above DMA; equal-weight top two; rebalance every five common sessions.
- Synthetic 3x daily-reset return: `3 × benchmark price return − 2 × prior-close ^IRX yield / 252 − 0.95% / 252`. Wealth is absorbing at zero. A 25 bps turnover-cost sensitivity is included.
- Price returns are used for all five families, consistently excluding dividends. These are synthetic daily-reset proxies, **not actual TQQQ, SOXL, SPXL, UDOW, or TNA returns**. There is no tracking error, actual fund financing agreement, fund liquidation/creation mechanism, or execution microstructure.

## Results
| Control | Cost | Ending $5,000 | Max drawdown | Peak date → trough date | Worst rolling 252-session return | Below $50? | Below $5? |
|---|---:|---:|---:|---|---:|---|---|
| Synthetic DMA250/top-2/C5 family rotation | 0 bps | $236.41 | -95.86% | 2000-03-10 → 2002-06-03 | -87.96% | No | No |
| Synthetic DMA250/top-2/C5 family rotation | 25 bps | $215.91 | -96.20% | 2000-03-10 → 2002-06-04 | -88.32% | No | No |
| Synthetic 3x QQQ buy-and-hold | 0 bps | $4.65 | -99.95% | 2000-03-27 → 2002-10-09 | -99.15% | Yes, 2001-04-03 | Yes, 2002-07-23 |
| Synthetic 3x QQQ buy-and-hold | 25 bps | $4.64 | -99.95% | 2000-03-27 → 2002-10-09 | -99.15% | Yes, 2001-04-03 | Yes, 2002-07-23 |
| Static equal-weight 1x benchmark basket | 0 bps | $2,588.79 | -58.26% | 2000-03-24 → 2002-10-09 | -41.34% | No | No |

### Family-rotation path
| Date | No-cost equity | 25 bps equity |
|---|---:|---:|
| 2000 year-end | $757.48 | $738.42 |
| 2001 year-end | $549.60 | $519.96 |
| 2002 year-end | $236.41 | $215.91 |

Average family-rotation exposure was about 50.9%. Despite being in cash for roughly half of the sessions, the strategy lost about 96% of its account value over the prolonged bear. The drawdown peak was just after the dot-com peak, and the account had not recovered by the end of 2002.

The synthetic QQQ proxy's own wealth path, compounded from the QQQ data start in 1999 (not from the $5,000 evaluation start), ended at 0.555% of its original proxy wealth and reached a -99.95% drawdown. The synthetic semiconductor proxy reached about -99.99% drawdown and ended at 0.340% of its original proxy wealth. Neither proxy crossed zero in this sample, but both came extremely close to total loss. Those proxy-wealth percentages are not account balances and should not be confused with the $5,000 portfolio comparison above.

## Interpretation
1. **The frozen family selector did not hit modeled zero, but its -96.2% drawdown is still near-ruin territory.** At 25 bps, $5,000 fell to about $216. This is not acceptable evidence for unattended deployment.
2. **It was less catastrophic than synthetic 3x QQQ buy-and-hold in this one stress window**, which fell below $5 and ended around $4.64. The selector reduced the modeled drawdown by roughly 3.75 percentage points, but it did not provide robust capital protection.
3. **Cash exposure helped, but not enough.** About 51% average exposure did not prevent a prolonged loss because selected leveraged proxies suffered extreme path-dependent decay.
4. **The 1x basket also lost materially**, ending at $2,589 with -58.3% max drawdown. Some loss is from the underlying bear market; leverage and daily-reset compounding magnified it substantially.
5. **Do not tune the selector to 2000–2002.** This is one pre-inception stress case, not a portfolio design target and not a validated reconstruction of actual leveraged ETFs. It is evidence that any candidate needs an explicit account-level survivability gate in addition to terminal-wealth comparison.

## Decision / next step
No candidate is promoted. Do not expand the DMA/top-N/cadence/cap search. The already-tested V30/L20/DD20–30 overlays show the known tradeoff: materially smaller drawdowns but dramatically lower ending wealth in actual-era account replay. Before another strategy experiment, make a same-model comparison against the frozen canonical B0 shock/recovery control (fixed -4.5% QQQ daily shock and +10% recovery-from-low, no parameter sweep) so the stress study compares the current selector with the project's other canonical defensive mechanism under identical synthetic return assumptions. Any result remains synthetic and diagnostic.

## Provenance
- Input SHA-256: DIA `5dd74284025ed7f801f0059126315a3070045819c4f8d4e222e860182d9f1078`; ^IRX `f0a785c5674c13442e54d69626284a9e513aef6e12df49b257567cab153b9068`; QQQ `78c019c89ef247f61c4aa710cf10cb583aa83211176ba8a858030b7f53278c03`; ^RUT `60932a051a942c08b42de0bb1aa0492cb6fcec46f971f8f1daa3a266e37ad8ff`; ^SOX `25a8d7274521cf56c798a9bc182b1150987e3b80d560a98a6bc56c1577b53088`; SPY `7c6f9cbf2533386c244ab142ebe39ae5fc1847a93c6318e2abd42eed317d890b`.
- Summary SHA-256: `9c1e374e816d37be27f12d85414575fe9e28643b194578154e308124e7407ad8`
- Equity SHA-256: `8bfd03f0a6bd14257e828fc525c4db08f5867f0e3d7a1b8e282aee406e1ee2c7`
- Weights SHA-256: `4e7fb8c172beae1ee1f5752dbdb88f899f79fe5180c3b861c56b428813c8c305`
- Proxy returns SHA-256: `6608946b3d0b201984b57016ca69bff4a4f24dd55b5980fdc54748b9bbda7941`
- Artifact ZIP SHA-256: `053949741d07342f6d99d60dc796037a5d9cba8fa50e97a5955854cb9d388290`
