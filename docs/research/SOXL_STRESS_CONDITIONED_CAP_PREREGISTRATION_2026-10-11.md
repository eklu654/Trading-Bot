# Stress-Conditioned SOXL Cap Preregistration — 2026-10-11

## Motivation
The permanent SOXL 25% cap reduced full-period max drawdown by about 4.6 percentage points, but lost about 26.4% of terminal wealth at 25 bps and failed the preregistered gates. Event-level analysis shows the cap was active on 2,517 selected-family sessions, of which 1,379 had positive SOXL returns and 1,128 negative; the mean SOXL return on capped sessions was positive. The opportunity cost is therefore consistent with capping the family during long, strong trends as well as stress.

## Fixed hypothesis
Keep the same frozen DMA-250/top-2/5-session family rotation and the same 25% SOXL cap/replacement behavior, but activate the cap only during a predeclared SOXX stress state:
- Calculate SOXX's drawdown from its trailing 60-session closing high using only data known at the prior close.
- Enter stress when that drawdown is <= -15%; exit stress when it recovers to >= -10% (hysteresis).
- Update the stress state only on the frozen 5-session rebalance dates.
- At a rebalance, if SOXL is selected in the top two and stress is active, cap SOXL at 25%, preserve the other selected family's 50% weight, and allocate the freed 25% to the next-highest eligible family not already selected. If no replacement family is eligible, leave that portion in cash.
- If stress is inactive or SOXL is not selected, reproduce the frozen base weights exactly.
- No off-cycle rebalancing, no additional shock gates, no other cap values, and no parameter sweep.

## Evaluation / stop rule
Compare the frozen base, permanent SOXL_CAP25_ROTATE, and stress-conditioned cap using the same aligned actual ETF/benchmark inputs, $5,000 initial capital, 0/10/25/50 bps costs, and full/train/validation/holdout splits. Assert the no-stress control exactly reproduces base weights, SOXL never exceeds 25% during stress, and total exposure never exceeds 100%.
The stress-conditioned candidate passes only if full-period max drawdown improves by at least 5 percentage points while preserving at least 80% of base terminal wealth at 10 and 25 bps, without catastrophic train/validation degradation. Otherwise reject it and do not tune the 60-session window or 15%/10% hysteresis thresholds.
This is actual ETF history from 2010 onward; it does not test 2000. Pre-inception stress tests must be separately labeled synthetic daily-reset simulations.
