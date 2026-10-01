# OPTIONS-002 vs ETF-001 Common-Date Holdout Comparison — 2026-10-01

## Purpose

This research step compares the existing OPTIONS-002 candidate structures with ETF-001 over the same historical trade windows. It is descriptive only: it does not optimize parameters, select a winner, or promote a strategy.

The chronological holdout remains **2023 onward**.

## Important benchmark-integrity finding

The previously uploaded `etf001_dma_scaffold.csv` is not suitable for this comparison. Its `portfolio_value` becomes non-finite beginning **2013-01-04** and remains invalid for much of the later sample.

The raw ETF price files themselves contain finite adjusted-close data. The comparison therefore rebuilds ETF-001 directly from the raw TQQQ/SPXL/SOXL/VIX data, using the documented 200-day moving-average / five-session re-entry logic, 25% cash allocation, and next-session execution.

This prevents the invalid scaffold from contaminating the comparison.

## Holdout observations

The matched 2023+ candidate-level results are:

| Candidate | Matched trades | Aggregate candidate P&L | Mean P&L / defined loss | Median P&L / defined loss | Mean ETF-001 DMA return over same windows |
|---|---:|---:|---:|---:|---:|
| 20Δ shorts / 10Δ long wings — conservative | 44 | +$316 | -0.36% | +3.66% | +1.48% |
| 20Δ shorts / 10Δ long wings — midpoint | 42 | +$638 | -0.16% | +4.59% | +1.66% |
| 20Δ shorts / $5 fixed wings — conservative | 45 | -$108 | -1.15% | +5.37% | +1.44% |
| 20Δ shorts / $5 fixed wings — midpoint | 42 | -$474 | -3.51% | +2.10% | +1.59% |
| 20Δ shorts / $10 fixed wings — conservative | 44 | -$379 | -1.19% | +2.64% | +1.48% |
| 20Δ shorts / $10 fixed wings — midpoint | 42 | -$723 | -2.35% | +4.91% | +1.52% |

The option P&L figures above are candidate-level strategy P&L, not account-level returns. P&L-per-defined-loss is used as a normalized risk measure because candidate files do not represent a single fixed portfolio allocation.

## Interpretation

The dynamic 20Δ/10Δ structure remains the only tested wider-wing family with positive aggregate candidate P&L in this holdout snapshot. However, its average P&L relative to defined loss is slightly negative, and the matched ETF-001 DMA windows had positive average returns.

The fixed $5 and $10 structures have negative aggregate holdout P&L under both fill models.

These observations are **not sufficient to conclude that either strategy should be deployed**. The option candidate set is small, the candidate-level denominator is not a portfolio return, and the ETF comparison is a same-window benchmark rather than a capital-equivalent portfolio simulation.

## Next validation gate

Before any regime-selector work or deployment consideration:

1. Re-run the ETF-001 backtest and replace the invalid scaffold with a verified finite artifact.
2. Run a capital-equivalent common-date comparison using the actual account-feasibility lifecycle.
3. Compare the dynamic 20Δ/10Δ structure against ETF-001 across TRAIN, VALIDATION, and HOLDOUT without changing parameters based on holdout results.
4. Add transaction-cost/fill sensitivity and lifecycle-overlap checks to the common-date report.
5. Keep candidate promotion disabled until independent validation supports it.

No OPTIONS-002 candidate is promoted by this research step.
