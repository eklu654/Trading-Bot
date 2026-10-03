# Bull/Cash/Bear DMA Switching — Inverse ETF Research

## Hard portfolio constraint

This research **must never hold a bull leveraged ETF and a bear/inverse leveraged ETF at the same time**.

Every modeled session has exactly one directional state:

- **BULL** — 100% of the directional allocation is the paired bull ETF.
- **BEAR** — the configured fraction is the paired inverse ETF and the remainder is cash.
- **CASH** — no leveraged ETF exposure.

A transition is modeled as closing the prior state before the next state becomes active. There is no hedge sleeve and no simultaneous bull/bear position.

## Initial research universe

| Benchmark | Bull | Bear |
|---|---|---|
| SPY / S&P 500 | SPXL | SPXS |
| QQQ / Nasdaq-100 | TQQQ | SQQQ |
| SOXX / semiconductors | SOXL | SOXS |
| DIA / Dow 30 | UDOW | SDOW |
| IWM / Russell 2000 | TNA | TZA |

The paired products are daily leveraged/inverse products, so multi-day returns are path-dependent and are not expected to equal a simple +/-3x multiple of the benchmark's cumulative return.

## Signal design

Signals use the **non-leveraged benchmark** rather than the leveraged ETF itself.

For each candidate:

- Bull trigger: benchmark above its bull-side DMA.
- Bear trigger: benchmark below its bear-side DMA.
- Bull and bear DMA values are allowed to differ.
- Bear-side DMAs are intentionally tested at shorter horizons because this is a hypothesis to test, not an assumption to encode as truth.
- Confirmation lengths: 1 session and 5 sessions.
- Bear allocation: 25%, 50%, 75%, or 100%; the rest is cash.

The first matrix uses bull DMAs of 100/150/200/250 and bear DMAs of 20/30/50/75/100, subject to bear DMA < bull DMA.

## Chronological evaluation

Every configuration is reported on:

- Full historical sample
- Train: 2010–2019
- Validation: 2020–2022
- Holdout: 2023–2026

No holdout metric is used to select a configuration.

## Why this matters

The earlier fixed 200-DMA fallback research found that simply switching from one bull ETF to another did not reliably replace cash, especially during the initial COVID shock. The new experiment asks a different question: can a **directional state machine** recognize sustained downside early enough to use an inverse ETF, while still avoiding the long-run drag of staying bearish during ordinary market corrections?

The most important comparison is not just CAGR. We will track CAGR, max drawdown, Sharpe, Sortino, volatility, worst day, time in bull/bear/cash, and annual path dependence.

## Artifacts

- data/research/dma_bull_bear_switch_matrix.csv
- data/research/dma_bull_bear_switch_annual_returns.csv
- data/research/dma_bull_bear_switch_headline_holdout.csv

The research runner is research/test_dma_bull_bear_switching.py.
