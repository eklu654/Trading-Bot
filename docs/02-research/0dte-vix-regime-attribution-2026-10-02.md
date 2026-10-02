# 0DTE Frozen-Control VIX Regime Attribution — 2026-10-02

**Status:** Descriptive research; no candidate selection  
**Input:** Completed 0DTESPX 45-cell timing-matrix artifact plus the repository VIX history  
**Frozen controls:** IC 16D/6D at 15:55, IC 16D/6D at 15:00, put 16D/6D at 15:55, call 16D/6D at 15:55

## Purpose

The completed 0DTE timing matrix showed strong time-period dependence. The next question is whether that behavior is associated with a measurable volatility regime.

This analysis uses fixed VIX buckets chosen before inspecting the results:

- **<15**
- **15–20**
- **20–25**
- **25–30**
- **>=30**

The analysis is attribution only. It does not search for the best threshold, select a winning control, or modify the frozen chronological validation.

## Full-sample attribution

The 1,012-session sample contains one session without a matching VIX observation.

| Control | VIX <15 | 15–20 | 20–25 | 25–30 | >=30 |
|---|---:|---:|---:|---:|---:|
| IC 16D/6D, 15:55 | +$8,186 | +$6,907 | -$7,983 | +$2,322 | +$4,372 |
| IC 16D/6D, 15:00 | +$7,021 | +$2,722 | -$3,383 | +$1,427 | -$503 |
| Put 16D/6D, 15:55 | +$9,431 | +$389 | -$14,000 | +$4,553 | +$584 |
| Call 16D/6D, 15:55 | -$6,359 | -$4,724 | -$6,989 | +$48 | -$66 |

These are platform-preview dollar P&L values from $100,000 starting capital; they are not $5,000-account results.

## What the attribution shows

### 1. The 20–25 VIX bucket is consistently weak

All four frozen controls have negative aggregate P&L in the 20–25 bucket:

- IC 15:55: -$7,983
- IC 15:00: -$3,383
- Put 15:55: -$14,000
- Call 15:55: -$6,989

That common behavior is more informative than simply looking at which individual cell had the highest full-sample return. It suggests that a simple "higher VIX = better short premium" assumption is not supported uniformly by this sample.

### 2. The >=30 bucket is too sparse for a reliable conclusion

There are only **31** sessions with VIX >=30 across the full sample, and only **2** in the 2026 holdout. The IC 15:55 control has positive full-sample P&L in this bucket, but that observation is dominated by a small number of sessions and should not be treated as validated evidence.

### 3. The relationship is non-monotonic

The frozen controls do not show a simple monotonic progression from low VIX to high VIX. For example, the IC 15:55 control is positive below 20, negative at 20–25, and positive again above 25.

Therefore, replacing the project's current regime logic with a single VIX threshold based on this attribution would amount to fitting the historical sample.

## Chronological check

The same fixed buckets were examined separately in TRAIN (2022-06-16 through 2024-12-31), VALIDATION (2025), and HOLDOUT (2026-01-01 through 2026-09-28).

For the 16D/6D IC 15:55 control:

| Split | <15 | 15–20 | 20–25 | 25–30 | >=30 |
|---|---:|---:|---:|---:|---:|
| TRAIN | +$5,412 | -$1,060 | -$5,523 | +$57 | -$2,866 |
| VALIDATION | +$965 | +$3,959 | -$235 | -$1,003 | +$6,618 |
| HOLDOUT | +$1,809 | +$4,008 | -$2,225 | +$3,267 | +$620 |

The holdout's >=30 cell contains only two sessions, so its positive result has very little statistical weight.

The 20–25 weakness persists across all three chronological periods for this control, but that does not by itself establish a tradable regime rule.

## Disposition

This experiment supports a narrower research question:

> **Can an independently defined market-regime classifier identify conditions in which a frozen 0DTE control has materially different risk/return behavior without using option P&L to define the regime?**

It does **not** establish such a classifier yet.

The next regime experiment should use market variables available independently of the options result, keep the regime definitions frozen before evaluation, and preserve the 2026 holdout as the final untouched check.

## Reproducibility

Run:

    python tools/0dte/analyze_vix_regimes.py path/to/0dte_management_timing_matrix.json path/to/vix_daily.csv --output artifacts/0dte_vix_regime_attribution.csv

No strategy parameters are optimized by this tool.
