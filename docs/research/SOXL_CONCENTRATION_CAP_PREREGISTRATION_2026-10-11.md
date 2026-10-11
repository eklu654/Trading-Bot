# Semiconductor Family Concentration Cap Preregistration — 2026-10-11

## Hypothesis
The event-level audit identified the semiconductor family (SOXL) as the largest single-family dollar-loss contributor in the two deepest recent drawdown episodes. A fixed family-specific concentration cap may preserve more upside than portfolio-wide exposure cuts or a shock gate because it reduces SOXL concentration only when selected and reallocates the excess to another eligible family.

## Frozen control
Use the existing DMA-250 / top-2 / 5-session family rotation unchanged as the control. Universe: SPXL/SPY, TQQQ/QQQ, SOXL/SOXX, UDOW/DIA, TNA/IWM. Bull ETFs or cash only. Signals use prior-close information and next-session returns. Use common aligned dates and the pinned endpoint patch through 2026-10-02.

## One fixed candidate: SOXL_CAP25_ROTATE
- At the existing 5-session rebalance dates, calculate the same frozen eligibility and benchmark/DMA ranking.
- If SOXL is not in the selected top two, preserve the frozen base weights exactly.
- If SOXL is in the top two, cap SOXL at 25% of portfolio weight; keep the other selected family at its frozen 50% slot; allocate the freed 25% to the next-highest-ranked eligible family not already selected.
- If no replacement family is eligible, leave the unfilled weight in cash.
- No off-cycle rebalancing, no shock gates, no threshold tuning, no new indicator, and no additional parameter sweep.

## Evaluation / stop rule
Compare base and SOXL_CAP25_ROTATE on the same frozen inputs, $5,000 initial capital, 0/10/25/50 bps turnover costs, and full/train/validation/holdout splits. Assert the no-cap control exactly reproduces the frozen base and the candidate never exceeds 100% total exposure or holds incompatible bull/inverse pairs.
Candidate passes only if full-period max drawdown improves by at least 5 percentage points and at least 80% of base terminal wealth remains at 10 and 25 bps, without catastrophic train/validation degradation. Otherwise reject it; do not try 20%, 30%, or other caps.
This is an actual-history test from 2010 onward, not a test of the 2000 bear market. Pre-inception simulations must be separately labeled synthetic daily-reset returns.
