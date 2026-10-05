# TQQQ DMA / Partial-Exposure Family — Final Classification (2026-10-05)

## Scope

This closes the remaining re-entry-delay variable for the TQQQ DMA/partial-exposure family. No further parameter tweaking is required within this family.

The research sequence covered:
- DMA lengths from 100 through 300 days.
- Below-DMA exposure from 0%, 25%, 50%, 75%, and 100%.
- Immediate re-entry and delayed re-entry/confirmation of 3, 5, and 10 sessions. A 1-session confirmation is equivalent to the immediate rule in the implemented signal timing.
- Trading-cost sensitivity from 0 to 50 bps.
- Full-history comparison against buy-and-hold.
- Separate re-entry sensitivity over the common later-period test window.

## Re-entry-delay result

The completed re-entry sensitivity run tested 1,000 combinations.

At zero trading cost, the best partial-exposure result for each non-immediate delay was:

| Re-entry rule | Best DMA | Below-DMA exposure | Final balance | CAGR | Max drawdown |
|---|---:|---:|---:|---:|---:|
| Immediate | 225 | 50% | $118,895 | 50.51% | -58.65% |
| 3 sessions | 250 | 75% | $102,643 | 47.68% | -72.29% |
| 5 sessions | 250 | 50% | $107,931 | 48.64% | -60.40% |
| 10 sessions | 250 | 75% | $99,461 | 47.08% | -72.29% |

The immediate rule remained the strongest wealth result. Delaying re-entry did not produce a better wealth/drawdown trade-off. Transaction-cost stress did not reverse that conclusion.

## Full-history result

The full-history sweep used the canonical TQQQ history through 2026-10-02.

Buy-and-hold:
- Final balance: $1,974,070 from $5,000
- CAGR: 43.24%
- Max drawdown: -81.66%

Best partial-exposure result:
- 200-DMA / 75% exposure below DMA
- Final balance: $1,316,468
- CAGR: 39.79%
- Max drawdown: -71.53%

A particularly relevant risk-balanced candidate was:
- 200-DMA / 50% exposure below DMA
- Final balance: $1,185,862
- CAGR: 38.92%
- Max drawdown: -58.22%

Thus the family consistently demonstrated its main property: reducing drawdown by sacrificing substantial terminal wealth.

## Final classification

**CLASSIFICATION: REJECTED AS A PRIMARY RETURN-MAXIMIZATION STRATEGY.**

The DMA/partial-exposure family does not currently justify replacing buy-and-hold TQQQ on the basis of terminal wealth. The best partial-exposure configurations materially trail buy-and-hold over the full history.

**SECONDARY STATUS: RETAINED AS A RISK-REDUCTION CONTROL.**

The family is not useless. It provides a genuine drawdown-reduction mechanism, with 200-DMA/50% reaching approximately -58% versus approximately -82% for buy-and-hold in the full-history test. But that protection has a substantial return cost.

## Research decision

Do not continue blind searches over more DMA lengths, exposure percentages, or re-entry delays within this family.

The family is now considered **closed for primary strategy discovery**. Future work should only revisit it if a separate research question specifically requires a lower-drawdown TQQQ control or a component of a broader regime strategy.
