# 0DTE Chronological Validation — Frozen Control Set

**Date:** 2026-10-02  
**Source:** 0DTESPX management-timing matrix artifact  
**Artifact:** `0dte-timing-matrix-36527403745`  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012 per frozen control  
**Starting capital:** $100,000 platform preview  
**Purpose:** Reproduce and audit the frozen chronological validation without optimizing the holdout.

## Important methodology decision

The 45-cell timing matrix is exploratory/in-sample evidence. The full sample is divided chronologically:

- **Train:** 2022-06-16 through 2024-12-31 — 597 sessions
- **Validation:** calendar year 2025 — 238 sessions
- **Holdout:** 2026-01-01 through 2026-09-28 — 177 sessions

The 2026 holdout is not used to choose or tune the strategy.

Split return is defined as the sum of daily **net P/L** divided by the frozen $100,000 starting capital. This is intentionally the same accounting convention used by the project's prior validation report; it is not a compounded account-return calculation.

## Frozen controls

The validation set remains fixed at:

1. Iron condor, 16D/6D, 15:55 exit.
2. Iron condor, 16D/6D, 15:00 exit.
3. Put credit spread, 16D/6D, 15:55 exit.
4. Call credit spread, 16D/6D, 15:55 exit.

These are controls, not approved trading rules.

## Corrected chronological results

The repository now has an automated validator at:

`tools/0dte/analyze_chronological_controls.py`

It verifies all four controls contain exactly 1,012 unique sessions and that the chronological partitions contain exactly 597 / 238 / 177 sessions. The validator was added with regression coverage and the full repository test suite passed in GitHub Actions run **#276**.

| Control | Train | 2025 validation | 2026 holdout |
|---|---:|---:|---:|
| IC 16D/6D, 15:55 | **-3.98%** | **+10.30%** | **+7.69%** |
| IC 16D/6D, 15:00 | **-4.37%** | **-1.09%** | **+12.96%** |
| Put 16D/6D, 15:55 | **+2.05%** | **-11.59%** | **+10.58%** |
| Call 16D/6D, 15:55 | **-16.93%** | **+1.33%** | **-2.41%** |

These values are generated directly from the sanitized timing-matrix daily net-P/L records.

### Why this correction matters

An earlier version of this document contained several percentages that did not match the frozen artifact's daily net-P/L ledger. The repository now treats the artifact and the automated validator as the reproducibility source of truth.

The correction does **not** change the central research conclusion: the behavior is strongly time-period dependent, and the 2026 holdout alone cannot establish a stable unconditional edge.

## Net-P/L audit

The corrected dollar P/L by chronological split is:

| Control | Train | Validation | Holdout |
|---|---:|---:|---:|
| IC 16D/6D, 15:55 | -$3,978.88 | +$10,303.32 | +$7,690.28 |
| IC 16D/6D, 15:00 | -$4,373.88 | -$1,091.68 | +$12,960.28 |
| Put 16D/6D, 15:55 | +$2,045.68 | -$11,585.72 | +$10,576.64 |
| Call 16D/6D, 15:55 | -$16,929.32 | +$1,332.84 | -$2,414.12 |

The full-sample figures remain the previously documented matrix results; this audit only partitions the already-frozen daily observations chronologically.

## First major finding: the full-sample IC result is not a stable unconditional edge

The 16D/6D iron condor with a 15:55 exit produced +14.01% over the complete sample, but lost 3.98% during the 2022–2024 training period before producing positive results in 2025 and 2026.

That is materially different from a stable, unconditional return profile.

The adjacent 15:00 version was also negative in training and validation before turning strongly positive in the 2026 holdout.

## Second major finding: 2026 improvement is not unique to one control

The 2026 holdout was positive for:

- IC 16D/6D, 15:00: +12.96%
- Put 16D/6D, 15:55: +10.58%
- IC 16D/6D, 15:55: +7.69%

The call spread remained negative at -2.41%.

Because several distinct frozen controls improved during the same holdout period, the improvement cannot be attributed to the iron-condor construction alone. Market-state effects remain a plausible research explanation, but this experiment does not identify the cause.

## Third major finding: directional controls behave differently across time

The put spread moved from positive training performance to a large negative 2025 validation period and then positive 2026 holdout performance.

The call spread remained deeply negative in training, became slightly positive in 2025, and returned negative in the 2026 holdout.

This reinforces that directional behavior should not be treated as a substitute for a neutral 0DTE component without separate validation.

## Calendar-year behavior — 16D/6D iron condors

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

The evidence instead says:

> The frozen 0DTE controls exhibit substantial chronological variation, and late-day management may be a conditional component rather than an unconditional strategy.

The next experiment therefore remains regime attribution using variables defined independently of the option P/L.

## Next validation stage

1. Keep the four controls frozen.
2. Keep the 2026 holdout untouched.
3. Use independently defined market-regime variables.
4. Test a small predeclared regime-rule set on training only.
5. Validate unchanged rules on 2025.
6. Use 2026 only after the rule is frozen.
7. For any survivor, run account-constrained replay at the project's active capital tiers.
8. Compare the surviving options component against ETF-001 on common dates and identical starting capital.
9. Keep 0DTE research-only until account feasibility, out-of-sample behavior, execution assumptions, and risk controls all pass their respective gates.

## Current disposition

**0DTE remains research-only.**

No candidate is promoted by this document.
