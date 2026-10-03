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
- `data/research/dma_fallback_annual_returns_2018_2025.csv`

## Results from Dynamic ETF Research run #48

Run #48 completed successfully on 2026-10-03 and generated the three DMA fallback artifacts.
The results below are descriptive outputs from the fixed, predeclared controls; no fallback
pair was selected by optimization.

Full-period 2018-2025 results:

| Control | CAGR | Volatility | Sharpe | Max drawdown | Fallback days | Cash days |
|---|---:|---:|---:|---:|---:|---:|
| SOXL -> TQQQ | 25.22% | 67.62% | 0.676 | -67.01% | 228 | 685 |
| SOXL -> SPXL | 19.02% | 65.85% | 0.598 | -67.13% | 203 | 710 |
| TQQQ -> SOXL | 25.22% | 46.46% | 0.721 | -62.59% | 31 | 685 |
| TQQQ -> SPXL | 30.69% | 45.53% | 0.820 | -50.01% | 52 | 664 |
| SPXL -> TQQQ | 30.14% | 35.58% | 0.923 | -48.02% | 98 | 664 |
| SPXL -> SOXL | 25.04% | 34.81% | 0.819 | -48.92% | 52 | 710 |

For context, the corresponding static 100%-invested controls over the same 2018-2025
period were 32.62% CAGR / -81.66% max drawdown for TQQQ, 23.08% / -76.86% for SPXL,
and 21.65% / -90.46% for SOXL. These comparisons are descriptive and do not account for
transaction costs, slippage, taxes, or live execution effects.

### Stress-period observations

The fixed fallback controls did not reliably avoid the initial COVID crash because the
fallback ETF often failed its own 200-DMA eligibility test at the same time. For example,
SOXL -> TQQQ used TQQQ for only 2 sessions during the 2020-02-19 through 2020-04-30 window
and lost 50.46% over that diagnostic window. Cash therefore remained the effective fallback
for most of that episode.

The 2022 rate-hike bear produced more differentiation. TQQQ -> SPXL lost 35.34% during
2022 versus 48.21% for TQQQ -> SOXL, while SPXL -> TQQQ lost 28.65% and SPXL -> SOXL also
lost 28.65%. The fallback mechanism did not make these periods safe; it mainly changed the
amount of time exposed to a different leveraged ETF when that ETF independently remained
above its 200-DMA.

### Research interpretation

The strongest evidence from this test is not that a leveraged fallback is universally
preferable to cash. Rather, the result is highly target-dependent. SOXL benefited materially
from fixed fallbacks in the full-period sample, while TQQQ's cash rule already captured much
of its historical performance and some fallbacks reduced CAGR. The next useful test is
therefore not a broader fallback sweep; it is robustness/holdout testing of a small number of
predeclared controls, including whether the fallback logic survives transaction costs and
whether its apparent benefit comes from a small number of periods.
