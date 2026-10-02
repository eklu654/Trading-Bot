# Leveraged ETF Controls — 2018-2025 Benchmark

**Research run:** Dynamic ETF Research #36  
**Commit:** `cbdd6dfda0f2089ec7f9e0ab96f6a0a0f442de06`  
**Data through:** 2026-09-25  
**Comparison window:** 2018-01-01 through 2025-12-31 (first trading day 2018-01-02)

## Purpose

This benchmark adds simple buy-and-hold controls for TQQQ and SOXL and compares them with fixed 200-day moving-average cash controls and the deterministic dynamic family-leverage benchmark. The goal is to determine whether the added complexity is producing something materially different from simply holding a high-beta leveraged ETF.

All signals use next-session execution. The static controls are true buy-and-hold series using adjusted close returns.

## 2018-2025 results

| Strategy | CAGR | Volatility | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|
| SPY buy-and-hold | 14.22% | 19.46% | 0.782 | -33.72% |
| SSO buy-and-hold | 20.41% | 38.96% | 0.674 | -59.34% |
| SPXL buy-and-hold | 23.08% | 57.94% | 0.654 | -76.86% |
| **TQQQ buy-and-hold** | **32.62%** | 71.16% | 0.758 | -81.66% |
| **SOXL buy-and-hold** | **21.65%** | 104.06% | 0.714 | -90.46% |
| SPY 200DMA + cash | 10.65% | 12.59% | 0.869 | -19.81% |
| SPXL 200DMA + cash | 12.95% | 33.83% | 0.532 | -57.82% |
| TQQQ 200DMA + cash | **34.42%** | 48.01% | **0.861** | **-50.01%** |
| SOXL 200DMA + cash | 8.44% | 67.52% | 0.462 | -69.63% |
| Dynamic family leverage | 21.24% | 54.59% | 0.630 | -63.14% |

## Research interpretation

1. **100% SOXL is not a trivial benchmark.** It produced 21.65% CAGR for 2018-2025, very close to the dynamic family's 21.24% CAGR.
2. The difference is risk: SOXL's annualized volatility was 104.06% and maximum drawdown was -90.46%, versus 54.59% volatility and -63.14% maximum drawdown for the dynamic benchmark.
3. **TQQQ is an especially important control.** In this window, TQQQ buy-and-hold produced 32.62% CAGR, while TQQQ with the 200DMA cash rule produced 34.42% CAGR with materially lower volatility (48.01%) and max drawdown (-50.01%).
4. The deterministic dynamic family strategy therefore does **not** clear the simple TQQQ controls on this 2018-2025 sample. Its value proposition would need to come from robustness across additional periods, better downside behavior, or a later strategy that improves the control set without excessive parameter complexity.
5. The SOXL 200DMA rule is notably weak in this sample: 8.44% CAGR. That is evidence against assuming that a generic 200DMA cash rule automatically improves every leveraged ETF.

## Gate for further work

Do not promote the deterministic dynamic family strategy based on CAGR alone. The next useful work is to test whether a small, predeclared set of robust controls can improve the risk/return tradeoff across distinct stress and recovery regimes without becoming a parameter-optimization exercise.

The 2018-2025 SOXL comparison is now a permanent control artifact in the research workflow.
