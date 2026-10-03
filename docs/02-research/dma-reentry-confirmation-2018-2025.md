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
