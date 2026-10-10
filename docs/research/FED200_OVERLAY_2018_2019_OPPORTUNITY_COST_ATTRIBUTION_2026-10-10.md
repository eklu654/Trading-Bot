# Fed/200-DMA Overlay: 2018–2019 Opportunity-Cost Attribution

**Date:** 2026-10-10  
**Classification:** Retrospective attribution of an already-run candidate; no rule changes, no new portfolio backtest.  
**Source workflow:** [Frozen Fed-vs-DMA ablation, run 37889360594](https://github.com/eklu654/Trading-Bot/actions/runs/37889360594)  
**Source artifact:** `canonical-shock-recovery-frozen-overlay-comparison`, artifact ID `11597189873`, SHA-256 `784c85850d4c7394bba091e3bea3e1ae66514632554e2112e47b8fee4d38650b`  
**Frozen market input hash:** `eea8ba3291428ec6e386002bab09de94a54e16508648c17f2a947b5e80731c1e`

## Question

Is the active-Fed/200-DMA overlay's 2018–2019 opportunity cost concentrated in a particular defense interval that overlaps baseline shock defense, or is it a broad cost of the state machine?

## Evidence from the existing leave-one-episode-out ledger

For the 50%-exposure-in-overlay candidate (F50), the full candidate ends at **$4,087,451** versus B0 at **$4,040,314**. Its event ledger identifies three material 2018–2019 intervals:

| Overlay episode | Overlay dates | Overlay sessions | Incremental defense sessions beyond B0 | F50 conditional terminal contribution |
|---|---|---:|---:|---:|
| 6 | 2018-12-04–2019-02-04 | 41 | 20 | -$410,120 |
| 7 | 2019-02-06–2019-02-13 | 6 | 6 | -$117,674 |
| 8 | 2019-03-07–2019-03-08 | 2 | 2 | -$202,395 |

The first interval is the largest of the three. It is **not solely** a baseline-overlap issue: 21 of its 41 overlay sessions overlap B0 defense, but 20 sessions add incremental defense. Episodes 7 and 8 are entirely incremental defense.

For comparison, F75's corresponding conditional contributions are approximately -$199,638, -$58,377, and -$100,442. F25's are approximately -$613,931, -$172,750, and -$297,051. These are conditional terminal differences from removing one episode at a time, not additive components; compounding means they must not be summed.

## Context: protection is concentrated elsewhere

The same ledger attributes a large positive conditional terminal contribution to the long 2022–2023 overlay episode (2022-04-05–2023-01-25): about **+$1.066M for F50**, +$613k for F75, and +$1.357M for F25. These leave-one-episode-out effects are also conditional, not additive.

That contrast explains the trade-off visible in the full-period results: the overlay's 2022 defense can outweigh several earlier false-positive costs, but a small number of 2018–2019 intervals materially determine terminal wealth. It does **not** show that the 2018 episodes can be safely removed without weakening the 2022 defense.

## Answer

The cost is **concentrated but not isolated to one single interval**. The Dec 4, 2018–Feb 4, 2019 interval is the largest identified 2018–2019 contributor, while the Feb 6–13 and Mar 7–8 intervals add further meaningful opportunity cost. The main interval partly overlaps baseline defense, but 20 of its sessions are incremental; the other two intervals are fully incremental.

This is a diagnosis, not evidence of a fixable bug. Because the full sample and these dates have already been examined, a rule change based on this attribution would be further development on known data. Do not tune the exit/re-entry state machine to these intervals and call the same-period result validation.

## Next step and guardrails

- Keep B0 as the control; do not promote or retune F25/F50/F75 from this analysis.
- If a specific causal hypothesis is proposed, write a preregistered rule using only information available at the signal close, preserve next-open execution and the one-session Fed lag, and evaluate it on the same common inputs for accounting consistency.
- Treat the 2018–2019 intervals as development evidence. Require a newly frozen prospective/chronological holdout before any robustness claim.
- No new portfolio backtest, no threshold sweep, and no paper/live authorization were performed by this attribution pass.
