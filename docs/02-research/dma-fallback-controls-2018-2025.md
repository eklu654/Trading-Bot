# 200-DMA Exit: Cash vs Leveraged-ETF Fallbacks — 2018-2025

## Purpose

The existing research showed that a generic 200-DMA cash rule behaves very differently by
underlying: TQQQ 200-DMA + cash was strong in 2018-2025, while SOXL 200-DMA + cash was
much weaker. This follow-up asks a narrower question:

> When a leveraged ETF falls below its 200-day moving average, is cash actually the
> useful destination, or can a different leveraged ETF remain investable?

This test is deliberately simple and predeclared. It does not optimize fallback choice,
moving-average length, or thresholds.

## Controls

For each target ETF, the test keeps the target while its own prior-session close is at
or above its 200-DMA. When the target is below its 200-DMA, it uses one fixed fallback
ETF if that fallback is itself above its own 200-DMA; otherwise it goes to cash.

Fixed pairs:

- SOXL -> TQQQ
- SOXL -> SPXL
- TQQQ -> SOXL
- TQQQ -> SPXL
- SPXL -> TQQQ
- SPXL -> SOXL

A cash-only 200-DMA control is included for SOXL, TQQQ, and SPXL.

Signals are evaluated using information available at the prior close and affect the
next session, matching the existing deterministic research convention.

## Stress windows

The test also reports the predeclared:

- 2020-02-19 through 2020-04-30 (COVID crash)
- 2022-01-03 through 2022-12-30 (2022 rate-hike bear)

These windows are diagnostic only and are not used to select a fallback.

## Decision rule

No strategy is promoted from this test merely because it has the highest CAGR. The
useful result is whether fixed fallback controls consistently improve the risk/return
profile relative to cash across the full sample and the predefined stress windows.

The workflow artifact is:
- `data/research/dma_fallback_controls_2018_2025.csv`
- `data/research/dma_fallback_stress_2018_2025.csv`
