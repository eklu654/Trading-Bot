# OPTIONS-002 capital-equivalent holdout gate — 2026-10-01

## Purpose

This gate checks whether OPTIONS-002 can actually open trades under the
repository's defined-risk account-feasibility model during the chronological
holdout beginning 2023-01-01.

This is separate from candidate-level P&L. A strategy that has attractive
candidate-level marks but cannot open those trades in a $5,000 account is not
capital-feasible for the intended starting account.

## Result

The existing account-feasibility replay outputs show accepted 2023+ trades at the $5,000 account level for selected configurations. This makes $5,000 the first active capital-feasibility tier, but the observed sample remains too small and configuration-dependent to establish deployment viability.

The wider-wing candidate-level holdout comparison therefore must not be interpreted as evidence that OPTIONS-002 can compete with ETF-001 in the actual $5,000 portfolio. The account-feasibility layer remains the controlling constraint.

The dynamic 20-delta-short / 10-delta-long-wing structure is the principal wider-wing candidate to investigate further because it produced accepted trades at higher capital levels. Those accepted trades do not by themselves establish $5,000 deployment viability.

## Why the current structures remain capital-constrained

The smallest observed defined losses imply that some configurations require materially more than $5,000 to satisfy a 3–7% per-trade risk ceiling. The $5 fixed-wing structure is the closest to the $5,000 boundary, while the dynamic 20Δ/10Δ and $10 fixed-wing structures generally require substantially more capital for the observed holdout losses.

At $5,000, the 7% ceiling is $350. A trade with defined loss above $350 is rejected by the current risk gate regardless of its candidate-level historical P&L.

## Higher-account holdout feasibility

The existing account-feasibility outputs show that the 2023+ holdout begins to
produce accepted trades at higher account sizes, but only for selected
configurations:

- **$5,000:** 20 accepted holdout trades across three tested configurations,
  all using 7% risk caps. Aggregate net P&L across those independent
  configurations was **+$148**.
- **$10,000:** 17 tested configurations produced accepted holdout trades,
  totaling **283 accepted trades** and aggregate net P&L of **-$794.60** across
  independent configurations.

These aggregates combine separate backtests and must **not** be interpreted as
portfolio returns or as evidence that a single configuration earned those
results.

## ETF reference

The rebuilt ETF-001 25%-cash / 200-DMA strategy remains continuously
capital-scalable at the portfolio level because it does not require the
defined-risk option width represented by OPTIONS-002.

For the 2023+ period, the rebuilt ETF-001 equity curve increased substantially
over the holdout. This is a descriptive reference only; it is not used to
select or tune OPTIONS-002.

## Interpretation

1. **$5,000 is now the canonical starting balance and the primary capital-feasibility gate.**
2. Candidate-level OPTIONS-002 holdout P&L is insufficient for deployment
   evaluation when the account-feasibility replay cannot open the trades.
3. No OPTIONS-002 wider-wing candidate should be promoted on the basis of the
   candidate-level comparison alone.
4. Further options research should determine whether any tested structure can produce a sufficiently large, stable sample at $5,000 without weakening the risk controls.
5. Any such change must be tested on training/validation first and then carried
   unchanged into the untouched holdout.

## Reproducibility

Use:

    python research/analyze_options002_capital_holdout.py

The script writes:

    data/research/options002_capital_holdout_summary.csv

It does not rank strategies by holdout performance and does not modify the
account-feasibility model.
