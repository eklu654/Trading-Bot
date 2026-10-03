# 200-DMA Re-entry Confirmation — 2018-2025

The research code now compares the existing immediate 200-DMA re-entry behavior with the
project's intended **one full trading week above the 200-DMA before re-entry** rule.

## Fixed rule

- Exit to cash when the prior-session close is below the 200-DMA.
- After an exit, require five consecutive completed trading sessions with the prior close
  at or above the 200-DMA.
- Re-enter on the following session.
- No threshold or lookback search is performed.

The test covers TQQQ, SOXL, and SPXL over 2018-2025 and reports CAGR, volatility, Sharpe,
maximum drawdown, worst day, and days invested.

Artifact:
- `data/research/dma_reentry_confirmation_2018_2025.csv`

This is intended to separate two questions that were previously blended together:
whether a 200-DMA exit is useful at all, and whether the re-entry timing after an exit
should be immediate or delayed by the stated one-week confirmation rule.

## Results from Dynamic ETF Research run #48

The fixed five-session confirmation test completed successfully over 2018-2025.

| ETF | Immediate CAGR | Five-session CAGR | Immediate Max DD | Five-session Max DD | Immediate Sharpe | Five-session Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| TQQQ | 34.42% | 31.63% | -50.01% | -48.14% | 0.861 | 0.825 |
| SOXL | 8.44% | 11.45% | -69.63% | -68.04% | 0.462 | 0.494 |
| SPXL | 12.95% | 16.64% | -57.82% | -45.08% | 0.532 | 0.641 |

The fixed one-week confirmation therefore had different effects by ETF. It reduced TQQQ
CAGR while modestly reducing volatility and maximum drawdown; it increased both CAGR and
risk-adjusted metrics for SOXL and SPXL in this historical sample. This is not sufficient
by itself to establish a universal re-entry rule. A future promotion test should keep the
five-session rule fixed and evaluate it on chronological validation/holdout periods rather
than selecting the confirmation length from the same sample.
