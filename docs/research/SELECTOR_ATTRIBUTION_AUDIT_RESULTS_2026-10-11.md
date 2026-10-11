# Frozen Family-Selector Attribution Audit — Results (2026-10-11)

## Run and artifact
- Corrected workflow: [run 38123681582 — success](https://github.com/eklu654/Trading-Bot/actions/runs/38123681582).
- Tested commit: `8813ab420b16c2954b92eb24f20ff5300c38d343`.
- Unit tests passed; diagnostic script completed and all six outputs were uploaded.
- Artifact: `frozen-selector-attribution-audit`, ID `11696426826` (expires 2026-11-10).
- Actual ETF/family history only: 2010-03-12 to 2026-10-02, 4,166 sessions; starting balance $5,000; 25 bps turnover cost.
- Frozen control: DMA-250 eligibility, rank by benchmark distance above DMA, equal-weight top two, rebalance every five sessions.

## QA corrections and authority
An initial successful diagnostic run used an index beginning one session too early (2010-03-11) and reported split ending equity on the continuous full-period equity curve. The implementation was corrected before accepting the report: the analysis now starts on 2010-03-12, and train/validation/holdout metrics reset equity to $5,000 within each split. The first unit-test failure was only a strict floating-point equality assertion; it was corrected to a tolerance. **Only the corrected run linked above is authoritative.**

## Control results
| Split | Sessions | Ending equity from $5,000 split start | Max drawdown | Average exposure | Sessions with some cash |
|---|---:|---:|---:|---:|---:|
| Full | 4,166 | $249,490 | -68.53% | 84.78% | 15.22% |
| Train (2010–2019) | 2,469 | $21,323 | -65.85% | 82.42% | 17.58% |
| Validation (2020–2022) | 756 | $6,827 | -65.48% | 76.19% | 23.81% |
| Holdout (2023–2026) | 941 | $42,845 | -66.50% | 97.87% | 2.13% |

The holdout's high average exposure (97.9%) and 66.5% drawdown show that the DMA eligibility rule does not create a durable account-level risk limit. It is a family eligibility/trend filter, not a portfolio drawdown stop.

## Attribution findings
Additive family contribution is the sum of daily family weight × ETF return. It is a diagnostic decomposition of portfolio return, not a separately compounded counterfactual.

### Deepest episodes
- **2021-12-27 to 2023-03-13:** maximum drawdown -68.53%, peak $80,370, trough $25,292, recovery to prior high on 2024-03-01 (244 sessions after trough). Mean exposure during peak-to-trough was 47.4%. Additive contributions during the decline: semiconductors/SOXL -0.365, S&P/SPXL -0.294, Russell/TNA -0.129, Nasdaq/TQQQ -0.089, Dow/UDOW -0.089. During the next 63 sessions after the trough, SOXL and TQQQ average weights rose to 54.0% and 45.2%, respectively; their additive contributions were +0.381 and +0.216. The rotation participated strongly in the recovery, but had also carried large semiconductor and broad-market losses.
- **2024-07-10 to 2025-04-08:** drawdown -66.50%, peak $112,679, trough $37,747, recovered 2026-01-12 (191 sessions). SOXL's additive contribution during the decline was -0.434; TNA -0.175; UDOW -0.160; TQQQ -0.089. SOXL's average weight across this whole episode was only 6.4%, illustrating that even intermittent allocation to an extremely volatile leveraged family can matter. In the following 63 sessions the strongest additive contributions came from TQQQ (+0.281) and SPXL (+0.205); SOXL contributed +0.046.
- **2015-03-02 to 2016-06-27:** drawdown -65.85%, recovery after 235 sessions. Additive drawdown contributions: SOXL -0.354, TQQQ -0.284, SPXL -0.184.
- **COVID shock, 2020-02-19 to 2020-03-12:** drawdown -65.48% in only 16 sessions. The portfolio was 100% invested, split 50/50 between TQQQ and SOXL; additive contributions were -0.414 and -0.486. It recovered the prior high 102 sessions after the trough. This is a clear example where a slow 250-DMA eligibility filter did not prevent a sudden leveraged loss, while full participation in the rebound later mattered.

## Interpretation
1. **The main structural exposure is not just SOXL.** In the worst episodes, SPXL, TQQQ, SOXL and TNA can all contribute substantial losses. A semiconductor cap alone cannot fix the account-level risk profile.
2. **The 250-DMA filter is too slow to be a crash circuit breaker.** The COVID decline occurred over 16 sessions; five-session rebalancing and benchmark eligibility do not protect against sudden leveraged-ETF drawdowns. In prolonged bears, the strategy can also suffer across multiple families.
3. **Recovery participation is economically important.** After the 2021–2023 decline, SOXL/TQQQ exposure contributed strongly during the following 63 sessions. Broad permanent caps reduce some loss but also reduce this recovery participation; stress-conditioned SOXL capping preserved wealth but barely improved drawdown.
4. **The selector is momentum/concentration logic, not risk parity.** Ranking benchmark distance above DMA and equal-weighting two leveraged products concentrates exposure in whichever families have strongest recent benchmark trends, without scaling for their realized volatility or crash sensitivity.
5. Do not tune DMA, top-N, cadence, SOXL cap, or shock thresholds from this audit. It is diagnostic, not a parameter-search dataset.

## Decision and next bounded step
The current family-specific exit/cap family remains rejected. The next research step should be a *structurally distinct* account-level sizing test, not another family gate: predeclare one portfolio-level risk budget that scales the entire selected basket using prior-close realized volatility, then compare it with the frozen base using the same 0/10/25/50 bps costs and chronological splits. The existing volatility-targeting matrix in `research/test_dma_family_rotation_risk_overlay.py` must be audited for prior results before deciding whether any such test is genuinely new; do not repeat its grid. If that matrix has already been fully tested and rejected, proceed instead to the separately labeled pre-inception synthetic daily-reset stress study. No paper/live promotion until a candidate passes predeclared wealth, drawdown, execution, and robustness gates.

## Artifact hashes (corrected run)
- Summary SHA-256: `3be8b1df5e0d3f41dfa929784fe98b99db5ac5f5e608bd9750a312e8868d2657`
- Worst drawdowns SHA-256: `193d0e1a6e5e9bfe7a689fdd4d0969f9bf8346c41e62a11f9114e0b0c7eab296`
- Daily weights SHA-256: `c66bdea07c5840520df09bda1542fdd9a41a17073679d5c828c684537a636518`
- Worst 100 days SHA-256: `c452978d8e562cea08a592c09d9299bfa7f072a0d2558d56c81930177c48b7f0`
- Artifact ZIP SHA-256: `70871a0f50d3ffbf8b39378d3f2f0495f3ccf465b7da60b9648cac1198e19b87`
