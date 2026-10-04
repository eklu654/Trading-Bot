# ETF-031 Results — TQQQ Buy-and-Hold Robustness

ETF-031 is a benchmark robustness audit, not a parameter-selection sweep.

## Common empirical period

- Start: 2010-03-11
- End: 2026-10-02
- Starting capital: $5,000
- All direct controls use the same common period.

## Direct controls

At 0 bps:

| Strategy | Ending balance | CAGR | Max drawdown | Volatility | Recovery days |
|---|---:|---:|---:|---:|---:|
| TQQQ buy-and-hold | $1,558,429 | 41.44% | -81.66% | 61.18% | 707 |
| SOXL buy-and-hold | $1,363,181 | 40.30% | -90.46% | 91.70% | 1,230 |
| Frozen family rotation | $378,052 | 29.85% | -67.40% | 57.22% | 354 |
| SPXL buy-and-hold | $339,693 | 29.01% | -76.86% | 51.02% | 291 |
| TQQQ 200-DMA/cash | $329,962 | 28.78% | -50.01% | 42.80% | 105 |
| TQQQ 200-DMA/next-open execution | $504,211 | 32.12% | -48.14% | 43.47% | 164 |
| QQQ buy-and-hold | $91,390 | 19.18% | -35.12% | 20.67% | 405 |

At 50 bps, TQQQ buy-and-hold still ends at approximately $1.551M with a 41.40% CAGR.

## Robustness findings

- Every tested calendar-year start from 2010 through 2025 produced a positive CAGR; measured range: 15.62% to 85.03%.
- The 2020–2022 era produced -8.53% CAGR and an -81.66% maximum drawdown.
- Worst rolling CAGR was -81.15% over 1 year, -11.25% over 3 years, +5.66% over 5 years, and +25.34% over 10 years.
- Path permutation preserved the terminal return distribution while producing materially different drawdowns; adverse return ordering can reach a -100% path drawdown despite the same terminal multiple, underscoring the importance of path risk for leveraged buy-and-hold.
- Removing 2022 produces a 55.46% CAGR and approximately $7.45M from $5,000; this is a sensitivity result, not a forecast.
- Fixed future-CAGR scenarios were calculated separately from the historical result. One-third of the observed 41.44% CAGR is 13.81%, which compounds $5,000 to approximately $9,549 / $18,235 / $66,506 over 5 / 10 / 20 years.

## Risk-overlay comparison

The existing V30/L20/DD20/25/30 overlays substantially reduce historical terminal wealth relative to the offensive benchmarks. At 0 bps their approximate $5,000 terminal balances are $35.6k, $45.9k, and $53.4k respectively.

## Interpretation

The audit establishes historical benchmark behavior over a common period. It does not establish that historical leveraged-ETF returns will persist. Drawdown is retained as a measured path characteristic rather than an automatic rejection criterion; any future rejection based on drawdown must be tied to an explicit survival, broker, operational, or predeclared risk constraint.

ETF-031 also does not yet constitute the complete structural-macro research program described in the issue objective. The historical robustness portion is complete; the next research stage should stress plausible future return regimes, adverse sequencing, and operational survival assumptions without using the historical sample to optimize a new strategy.
