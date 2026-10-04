# ETF-031 Path Survivability Addendum — 2026-10-04

## Purpose

This addendum extends the authoritative ETF-031 comparison with rolling-window path evidence. It is deliberately descriptive: these statistics characterize the already-frozen controls and do not tune a strategy.

Source: frozen ETF-031 robustness artifact from GitHub Actions run 37169061754, covering the common period **2010-03-11 → 2026-10-02** with **4,167 daily observations** and a $5,000 starting balance.

## TQQQ buy-and-hold: rolling return robustness

| Rolling window | Worst CAGR | Best CAGR | Worst internal DD |
|---|---:|---:|---:|
| 1 year (252 sessions) | -81.15% | +415.93% | -81.02% |
| 3 years (756) | -11.25% | +122.25% | -81.66% |
| 5 years (1,260) | +5.66% | +79.32% | -81.66% |
| 10 years (2,520) | +25.34% | +62.85% | -81.66% |

The important point is not simply the 41.44% full-period CAGR. A one-year entry window could historically produce a deeply negative CAGR, while even the 3-year worst rolling CAGR was negative. The 5-year rolling CAGR was positive in every observed window, but the worst 5-year path still contained an approximately 81.66% peak-to-trough drawdown.

## Rolling-window drawdown breach rates

These are **window-incidence statistics**, not the percentage of calendar time spent below a drawdown threshold. For each rolling window, the calculation asks whether the maximum drawdown occurring inside that window breached the threshold.

| Window | Observed windows | DD >= 50% | DD >= 60% | DD >= 70% | DD >= 80% |
|---|---:|---:|---:|---:|---:|
| 1 year | 3,916 | 26.84% | 12.67% | 5.23% | 1.43% |
| 3 years | 3,412 | 57.30% | 38.01% | 20.78% | 16.41% |
| 5 years | 2,908 | 67.23% | 56.71% | 37.17% | 34.22% |
| 10 years | 1,648 | 100.00% | 100.00% | 65.59% | 60.38% |

This is a strong warning against describing TQQQ buy-and-hold as merely an “81.66% maximum drawdown strategy.” Over longer rolling windows, severe drawdowns are pervasive rather than isolated.

## Rolling CAGR downside incidence

| Window | Negative CAGR windows | CAGR < 10% windows |
|---|---:|---:|
| 1 year | 17.16% | 23.98% |
| 3 years | 3.69% | 13.39% |
| 5 years | 0.00% | 1.34% |
| 10 years | 0.00% | 0.00% |

This provides a more useful distinction between **return risk** and **path risk**. TQQQ's historical long-horizon return was exceptionally strong, but short and medium holding periods could still be extremely poor.

## Start-date robustness

The same ETF-031 artifact tested every calendar-year start from 2010 through 2025 while preserving the common terminal date of 2026-10-02.

| Start year | Ending $5k | CAGR |
|---:|---:|---:|
| 2010 | $1,558,429 | 41.44% |
| 2011 | $1,060,731 | 40.53% |
| 2012 | $1,140,735 | 44.52% |
| 2013 | $724,146 | 43.61% |
| 2014 | $338,146 | 39.18% |
| 2015 | $211,965 | 37.57% |
| 2016 | $190,997 | 40.37% |
| 2017 | $157,197 | 42.46% |
| 2018 | $70,229 | 35.27% |
| 2019 | $90,750 | 45.37% |
| 2020 | $37,506 | 34.79% |
| 2021 | $19,597 | 26.86% |
| 2022 | $9,954 | 15.62% |
| 2023 | $50,110 | 85.03% |
| 2024 | $17,311 | 57.11% |
| 2025 | $10,449 | 52.50% |

CAGR remained positive for every tested calendar-year start, but terminal wealth varied enormously because the remaining horizon and entry regime differed.

## Era evidence

The TQQQ path was not uniformly strong:

- 2010-2014: **51.69% CAGR**, **-43.91% max DD**
- 2015-2019: **40.09% CAGR**, **-58.08% max DD**
- 2020-2022: **-8.53% CAGR**, **-81.66% max DD**
- 2023-2026-10-02: **85.03% CAGR**, **-58.04% max DD**

The 2020-2022 regime is therefore a particularly important survivability test. It demonstrates that the enormous full-period terminal balance is not evidence of smooth or continuously favorable compounding.

## Implications for the strategy gate

1. **TQQQ buy-and-hold remains a first-class economic control.** Its historical terminal wealth is too large to discard merely because of drawdown.
2. **Its path risk is severe enough that paper readiness cannot be based on CAGR alone.** The system must explicitly model drawdown thresholds, minimum equity, recovery duration, and emergency behavior.
3. **Rolling-window evidence strengthens the case for testing controls such as TQQQ 200-DMA/next-open.** That control retains a high historical CAGR while materially reducing headline max drawdown.
4. **This does not prove the 200-DMA control is superior.** It must receive the same rolling-window, start-date, era, cost, execution, and operational analysis before selection.
5. **Drawdown-frequency analysis is not complete for every Tier-A control yet.** The current ETF-031 artifact provides rolling-window path statistics for TQQQ buy-and-hold; equivalent daily-equity rolling analyses should be generated for SOXL, SPXL, TQQQ 200-DMA/next-open, and the frozen family rotation before final candidate selection.
6. **Do not use these rolling windows as independent statistical samples.** They overlap heavily. They are path diagnostics, not independent observations for significance testing.

## Gate status

The evidence now supports a more precise research objective:

> Maximize robust terminal wealth while explicitly constraining the probability and operational consequences of unacceptable path behavior.

No production strategy is selected by this addendum.
