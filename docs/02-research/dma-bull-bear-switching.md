# Bull/Cash/Bear DMA Switching — Inverse ETF Research

## Hard portfolio constraint

The exclusivity rule is **per underlying/family**, not global across the portfolio.

For each paired benchmark family, the portfolio may hold **at most one directional side at a time**:

- **BULL** — 100% of that sleeve's directional allocation is the paired bull ETF.
- **BEAR** — the configured fraction of that sleeve is the paired inverse ETF and the remainder is cash.
- **CASH** — that sleeve has no leveraged ETF exposure.

Therefore:

- **Forbidden:** SOXL + SOXS, TQQQ + SQQQ, SPXL + SPXS, UDOW + SDOW, or TNA + TZA at the same time.
- **Allowed:** UDOW + SOXS, TQQQ + SDOW, SPXL + TZA, or other combinations where the bull and bear positions belong to different benchmark families.

A transition within one family is modeled as closing the prior state before the next state becomes active. There is no simultaneous bull/bear position **within the same family**. Cross-family directional exposure is explicitly permitted because a macro/sector allocation may reasonably be bullish in one family while bearish in another.

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

## Combined cross-family testing

The combined holdout experiment independently evaluates all five benchmark families and then combines their sleeve returns using an equal 20% weight per family. This equal-weight construction is a research control, not a production allocation decision. Each family enforces its own bull/bear exclusivity rule, while opposite directional states across different families remain valid.

This specifically tests the portfolio behavior implied by the clarified constraint: one family can be bullish while another is bearish, without either position invalidating the other.

## Why this matters

The earlier fixed 200-DMA fallback research found that simply switching from one bull ETF to another did not reliably replace cash, especially during the initial COVID shock. The new experiment asks a different question: can a **directional state machine** recognize sustained downside early enough to use an inverse ETF, while still avoiding the long-run drag of staying bearish during ordinary market corrections?

The most important comparison is not just CAGR. We will track CAGR, max drawdown, Sharpe, Sortino, volatility, worst day, time in bull/bear/cash, and annual path dependence.

## Artifacts

- data/research/dma_bull_bear_switch_matrix.csv
- data/research/dma_bull_bear_switch_annual_returns.csv
- data/research/dma_bull_bear_switch_headline_holdout.csv
- data/research/dma_bull_bear_switch_combined_holdout.csv

The research runner is research/test_dma_bull_bear_switching.py.
