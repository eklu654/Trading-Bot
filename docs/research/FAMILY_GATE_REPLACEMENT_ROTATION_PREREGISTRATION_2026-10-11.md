# Family-Gate Replacement Rotation Preregistration — 2026-10-11

## Motivation
The validated family-specific shock gate reduced full-period maximum drawdown by only about 2.2 percentage points while cutting terminal wealth by about 69%. Event attribution shows the gate often leaves the affected family's slot in cash; large drawdowns are concentrated in a few families, especially SOXL, but gate timing overlaps only part of those loss windows. Do not tune the shock/recovery thresholds.

## Fixed hypothesis
Keep the frozen DMA-250 / top-2 / 5-session family rotation and the exact same family-specific -4.5% shock / +10% recovery gate. Change only what happens to the gated slot:
- A family-specific shock exits only that family beginning next session.
- On the existing 5-session rebalance dates, rank all eligible, currently ungated families by the frozen benchmark/DMA score and select the top two; equal-weight the selected families.
- If a selected family becomes gated between rebalance dates, zero only that family's slot immediately; do not immediately reallocate the slot. It remains zero until the next scheduled rebalance, when the ranking can fill the slot with another eligible ungated family.
- A family whose gate clears between rebalance dates does not automatically regain its old slot; it must qualify at the next scheduled rebalance.
- If fewer than two eligible ungated families exist at a scheduled rebalance, allocate equally across those available; any remainder stays cash.
- Never hold both bull and inverse ETFs from the same family. This test uses bull ETFs or cash only.

## Controls and evaluation
Compare the frozen base, the existing cash-gated overlay, and the replacement-rotation candidate on the same common date range and actual ETF return inputs. Initial capital $5,000; costs 0/10/25/50 bps; full/train/validation/holdout splits. Assert the base weights reproduce the frozen base calculation and the overlay never increases family exposure except at scheduled rebalances.
The candidate passes only if it improves full-period max drawdown by at least 5 percentage points while preserving at least 80% of the frozen base's terminal wealth at 10 and 25 bps, with no catastrophic train/validation degradation. If it fails, reject it; do not tune the shock/recovery thresholds, cadence, or top-N.
This is actual family-ETF history only; it does not test 2000. Pre-inception tests must be clearly labeled synthetic daily-reset simulations.
