# Canonical Shock/Recovery + Fed-Paused/200-DMA Overlay — First Candidate Result

**Date:** 2026-10-09 UTC  
**Classification:** **REJECTED AS CURRENTLY DEFINED** (not a rejection of all Fed-based hypotheses)  
**Purpose:** Test one predeclared structural overlay against the unchanged canonical shock/recovery baseline.  
**Workflow:** [run 37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208)  
**Artifact:** `canonical-shock-recovery-fed-dma-overlay`, ID 11595564083.

## Frozen rules

### Control: canonical baseline

- $5,000 initial equity.
- QQQ adjusted-close daily return <= -4.5% starts defense.
- 0% TQQQ exposure begins at the next open.
- Re-enter at the next open after QQQ adjusted close reaches 10% above the post-shock running low.
- Otherwise 100% TQQQ.

### Candidate: baseline + Fed-paused/200-DMA overlay

- Compute the existing Fed lifecycle state from the daily effective target-rate series.
- Lag the Fed state by one QQQ session as a conservative availability rule.
- Arm an additional sticky defensive state when QQQ adjusted close is below its existing 200-session SMA AND the lagged Fed state is TIGHTENING_PAUSED.
- Keep that overlay armed until QQQ closes at/above its 200-DMA.
- Combine with the baseline by taking the lower of the two exposures; the overlay can reduce exposure but never increase it.
- Use close[t] signal -> open[t+1] execution, with prior exposure applied to overnight returns and new exposure applied intraday.
- No parameters were optimized in this run.

All three paths used one aligned market dataset within the run. The artifact contains the frozen market inputs, daily Fed state labels, daily equity curves, baseline event ledger, overlay transitions, period scorecard, cost sensitivity, and manifest.

## Whole-period result

| Metric | Baseline | Baseline + overlay | TQQQ buy-and-hold |
|---|---:|---:|---:|
| Ending balance | $4,040,316 | $2,908,571 | $2,094,669 |
| CAGR | 49.49% | 46.57% | 43.70% |
| Maximum drawdown | -73.53% | -73.53% | -81.66% |
| Average close-signal exposure | 93.46% | 92.89% | 100% |
| Defensive signal sessions | 274 | 298 | 0 |

The overlay ended about **$1.132 million (28.0%) below the unchanged baseline** while producing **no improvement in maximum drawdown**. It still beat TQQQ buy-and-hold over the full window, but that is not the relevant pass criterion: the question is whether the overlay improves the baseline's slow-bear resilience without excessive opportunity cost.

## What happened in the periods that matter?

The period return below is independently compounded within each named period; period drawdown is local to that window.

| Period | Baseline return | Candidate return | Baseline max DD | Candidate max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +895.0% | -43.1% | -43.1% |
| 2015–2019 | +569.6% | +382.1% | -44.5% | -44.5% |
| 2020–2021 | +325.6% | +325.6% | -47.0% | -47.0% |
| 2022–2024 | +42.3% | +42.3% | -72.6% | -72.6% |
| 2025–2026-10-07 | +100.2% | +100.2% | -56.1% | -56.1% |

The candidate does not alter exposure in the 2022–2024 window or in COVID/2025. Its only effect is in 2015–2019, where it materially reduces terminal wealth without improving period maximum drawdown.

## Why it failed

The transition ledger shows six defensive episodes, all in **2016 and 2019**:

- 2016-03-28 to 2016-03-29
- 2016-04-28 to 2016-05-10
- 2016-05-11 to 2016-05-24
- 2016-06-17 to 2016-06-20
- 2016-06-24 to 2016-06-30
- 2019-06-03 to 2019-06-04

Those were brief pauses in exposure during ordinary corrections. The candidate did **not** activate during the 2022 tightening-driven decline because its condition requires TIGHTENING_PAUSED; the Fed was still in the active hiking phase when the early damage accumulated. This is exactly the failure mode the overlay was supposed to address, and it did not.

## Decision

1. **Reject this exact overlay as a candidate for improving the baseline.** It sacrifices about 28% of terminal wealth and does not reduce maximum drawdown.
2. **Do not conclude that the Fed layer is useless.** This test falsifies the narrow paused-only × below-200-DMA rule as a helpful overlay on this baseline; a different Fed lifecycle hypothesis would require separate evidence.
3. **Do not immediately broaden into indicator fishing.** The next step should be a diagnostic report of when the existing Fed state was TIGHTENING_ACTIVE, TIGHTENING_PAUSED, EASING, or NEUTRAL during each drawdown episode and which state was actually present at the baseline's trigger/late-trigger dates. This can tell us whether any further Fed candidate has a causal chance of catching 2022 earlier before spending time backtesting another rule.
4. Any subsequent candidate must preserve the baseline, use the same data and execution, and be evaluated against both the acute-crash windows and the 2010/2016/2022 slow-bear cases.

## Reproducibility links

- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37885392208
- Candidate script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_fed_dma_overlay.py
- Workflow definition: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-fed-dma-overlay.yml
- Baseline stress-window audit: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
