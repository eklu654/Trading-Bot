# Canonical Shock/Recovery + Active-Tightening/200-DMA Overlay — Candidate 2 Result

**Date:** 2026-10-09 UTC  
**Classification:** **WORKING TRADE-OFF CANDIDATE; NOT SELECTED**  
**Workflow:** [run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946)  
**Artifact:** `canonical-shock-recovery-active-tightening-overlay`, ID 11595834480  
**Market-input SHA-256:** `9e86e33570d8b14a3fdc27d9f9b371e8a138c306929e48767551e3f48d612ba2`.

## Frozen candidate rule

Control is the unchanged `qqq_shock45_recovery10_actual_tqqq_v1` baseline.

Candidate 2 adds a sticky defense that enters when QQQ adjusted close is below the existing 200-session SMA and the one-session-lagged Fed lifecycle state is **TIGHTENING_ACTIVE**. The overlay remains armed until QQQ closes at/above the 200-DMA. Baseline shock/recovery defense remains independently active. All comparisons use the same aligned QQQ/TQQQ market data and close-to-next-open execution. No parameters were optimized.

## Whole-period results

| Metric | Baseline | Baseline + active-tightening overlay | TQQQ buy-and-hold |
|---|---:|---:|---:|
| Ending balance from $5,000 | $4,040,313 | $3,674,919 | $2,094,669 |
| CAGR | 49.49% | 48.64% | 43.70% |
| Maximum drawdown | -73.53% | -57.34% | -81.66% |
| Worst rolling 252-session return | -72.64% | -47.11% | -81.04% |
| Average close-signal exposure | 93.46% | 88.71% | 100% |
| Defensive signal sessions | 274 | 473 | 0 |

Candidate 2 gives up **$365,394 (about 9.0%)** of ending wealth relative to the baseline, but improves maximum drawdown by about **16.2 percentage points** and improves the worst rolling 252-session return by about **25.5 percentage points**. It still finishes above TQQQ buy-and-hold. This is a real trade-off, not a clear winner.

## Period scorecard

Period returns are independently compounded within each period; period drawdown is local to the period.

| Period | Baseline return | Candidate return | Baseline max DD | Candidate max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +895.0% | -43.1% | -43.1% |
| 2015–2019 | +569.6% | +374.8% | -44.5% | -42.3% |
| 2020–2021 | +325.6% | +325.6% | -47.0% | -47.0% |
| 2022–2024 | +42.3% | +82.6% | -72.6% | -53.4% |
| 2025–2026-10-07 | +100.2% | +100.2% | -56.1% | -56.1% |

The candidate materially improves the 2022–2024 result and the 2016 slow-correction local drawdown. It materially reduces wealth during 2015–2019, primarily because it repeatedly enters/exits during the 2016 and 2018–2019 trend-chop periods. It does not change the COVID or 2025 exposure because those episodes occur while the Fed state is EASING, not TIGHTENING_ACTIVE.

## Targeted stress windows using inherited account equity

| Window | Baseline return | Candidate return | Baseline local max DD | Candidate local max DD |
|---|---:|---:|---:|---:|
| 2010 slow correction | -7.39% | -7.39% | -40.8% | -40.8% |
| 2016 slow correction | -18.09% | -17.95% | -42.0% | -23.8% |
| 2018 Q4 bear (to 2019-03-29) | +0.04% | -29.18% | -31.6% | -34.6% |
| COVID crash/rebound | +24.58% | +24.58% | -47.0% | -47.0% |
| 2022 tightening bear | -69.83% | -43.68% | -72.6% | -53.4% |
| 2025 correction | -12.75% | -12.75% | -56.1% | -56.1% |

These windows use each portfolio's own inherited starting equity; do not compare raw dollar start/end values between strategies as though they had the same prior wealth. The active overlay's strongest evidence is 2022. Its clearest cost is 2018 Q4: it reduced exposure during several brief crosses around the 200-DMA, then missed part of the eventual recovery.

## Cost sensitivity

| Cost per full exposure change | Baseline ending balance | Candidate ending balance |
|---|---:|---:|
| 0 bp | $4,040,313 | $3,674,919 |
| 10 bp | $3,964,234 | $3,555,567 |
| 25 bp | $3,852,656 | $3,383,558 |
| 50 bp | $3,673,276 | $3,114,652 |

Under the script's simplified cost model, the candidate's drawdown advantage persists, while the ending-wealth penalty also persists. These are sensitivity estimates, not broker-specific live-fill forecasts.

## Decision

- **Do not replace the baseline.** It still wins on terminal wealth in this historical sample.
- **Do not discard Candidate 2 yet.** It is the first overlay that substantially improves the measured 2022 drawdown and rolling-year loss while retaining a terminal balance above buy-and-hold.
- **Do not tune the rule based on these same periods.** The next useful step is diagnostic attribution of the candidate's 2018/2019 false-positive transitions and the 2022 defense interval, then a frozen chronological validation. The baseline and this one candidate should remain the only active price/Fed strategies in the comparison for now.
- Before any final choice, establish whether the 2018 opportunity cost is a fixed cost of a trend-based overlay or a fixable rule defect without sacrificing the 2022 protection. If a new rule is invented after inspecting these results, these periods become development data; a future untouched holdout is required.

## Reproducibility

- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37885966946
- Candidate script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_active_tightening_overlay.py
- Workflow definition: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-active-tightening-overlay.yml
- Fed state attribution: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
