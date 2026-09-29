# 0DTE Chronological Validation — First Pass

**Date:** 2026-09-29  
**Source:** 0DTESPX management-timing matrix artifact  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012  
**Purpose:** Determine whether the strongest 0DTE timing-matrix controls survive chronological validation without optimizing the holdout.

## Important methodology decision

The 45-cell timing matrix is treated as an exploratory/in-sample experiment. The full sample is divided chronologically:

- **Train:** 2022-06-16 through 2024-12-31 — 597 sessions
- **Validation:** calendar year 2025 — 238 sessions
- **Holdout:** 2026-01-01 through 2026-09-28 — 177 sessions

The 2026 holdout is not used to choose the strategy.

## Frozen controls

The first validation pass focuses on the 16D/6D controls already identified by the completed matrix:

1. Iron condor, 15:55 exit — original strongest full-sample control.
2. Iron condor, 15:00 exit — adjacent-time control.
3. Put credit spread, 15:55 exit — one-sided comparison.
4. Call credit spread, 15:55 exit — opposite-direction comparison.

These are controls, not approved trading rules.

## Results

| Control | Train return | 2025 validation | 2026 holdout |
|---|---:|---:|---:|
| IC 16D/6D, 15:55 | -3.98% | +10.30% | +7.69% |
| IC 16D/6D, 15:00 | -4.37% | -1.09% | +12.96% |
| Put 16D/6D, 15:55 | +2.05% | -3.03% | +10.58% |
| Call 16D/6D, 15:55 | -18.75% | -4.74% | -4.53% |

## First major finding: the full-sample IC result is not a stable unconditional edge

The 16D/6D iron condor with a 15:55 exit produced +14.01% over the complete sample, but the first chronological segment (2022–2024) lost 3.98%.

It then made +10.30% in 2025 and +7.69% in the 2026 holdout.

This is much more informative than the aggregate +14.01% figure. The strategy's historical behavior is clearly time-dependent.

The adjacent 15:00 version is even more revealing:

- 2022–2024: -4.37%
- 2025: -1.09%
- 2026 YTD: +12.96%

The two late exits therefore show a large change in behavior across time rather than a uniform historical premium.

## Second major finding: 2026 is unusually favorable across several late-exit candidates

The 2026 holdout was positive for both 16D/6D iron-condor exits and the 16D/6D put spread:

- IC 15:00: +12.96%
- Put 15:55: +10.58%
- IC 15:55: +7.69%

The call spread remained negative.

This means the positive 2026 results cannot by themselves establish that the iron condor is uniquely responsible for the improvement. Market conditions may be contributing.

## Third major finding: the call benchmark remains structurally weak

The 16D/6D call-credit spread was negative in all three chronological segments:

- Train: -18.75%
- 2025: -4.74%
- 2026 holdout: -4.53%

That makes it useful as a negative/directional control rather than a leading candidate.

## Calendar-year breakdown — 16D/6D iron condor

### 15:55

| Year | Net P/L |
|---|---:|
| 2022 | -$4,069.28 |
| 2023 | +$1,283.52 |
| 2024 | -$1,193.12 |
| 2025 | +$10,303.32 |
| 2026 YTD | +$7,690.28 |

### 15:00

| Year | Net P/L |
|---|---:|
| 2022 | -$359.28 |
| 2023 | +$2,853.52 |
| 2024 | -$6,868.12 |
| 2025 | -$1,091.68 |
| 2026 YTD | +$12,960.28 |

## What this means for the bot

The correct conclusion is **not** "the 16D/6D iron condor works."

The stronger conclusion is:

> The 0DTE results appear to be regime/time-period dependent, and late-day management deserves testing as a conditional component rather than as an unconditional strategy.

That fits the broader evidence base. Academic research on 0DTE trading finds that net P/L distributions are state-dependent and dominated by tail risk, with selective timing rules potentially behaving differently from unconditional carry. citeturn0search17

tastylive's own published material likewise emphasizes that 0DTE gamma increases substantially through the day and that management timing matters; one study found different behavior between opening-window and final-30-minute short-premium trades. citeturn0search0turn0search5

## Next validation stage

Do **not** search the full sample for another better strike or exit.

Instead:

1. Build historical market-regime labels independently of strategy P/L.
2. Test the frozen controls by regime.
3. Determine whether the 2025/2026 improvement corresponds to measurable volatility/trend characteristics.
4. Test a small, predeclared set of regime rules on the training period only.
5. Validate those rules on 2025.
6. Use 2026 only once the rule is frozen.
7. Then run account-constrained replay at $2,000, $5,000, $10,000, and $20,000.
8. Finally compare the resulting options component against the leveraged-ETF component.

## Current disposition

**0DTE remains research-only.**

The timing matrix successfully narrowed the research problem, but the chronological test shows that full-sample profitability is not sufficient evidence of a stable edge.

The next high-value experiment is **regime attribution**, not more unconstrained strategy optimization.
