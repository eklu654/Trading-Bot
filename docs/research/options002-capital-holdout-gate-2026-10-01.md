# OPTIONS-002 capital-equivalent holdout gate — 2026-10-01

## Purpose

This gate checks whether OPTIONS-002 can actually open trades under the
repository's defined-risk account-feasibility model during the chronological
holdout beginning 2023-01-01.

This is separate from candidate-level P&L. A strategy that has attractive
candidate-level marks but cannot open those trades in a $2,000 account is not
capital-feasible for the intended starting account.

## Result

The existing account-feasibility replay outputs show **zero accepted OPTIONS-002
trades on the 2023+ holdout for every tested $2,000 configuration**.

The wider-wing candidate-level holdout comparison therefore must not be
interpreted as evidence that OPTIONS-002 can compete with ETF-001 in the actual
$2,000 portfolio. The account-feasibility layer is the controlling constraint.

The dynamic 20-delta-short / 10-delta-long-wing structure remains the only wider
candidate that produced accepted trades in the broader historical account tests,
but those accepted trades do not establish 2023+ capital viability at $2,000.

## Why $2,000 fails the current risk gate

On the 2023+ holdout, the smallest modeled defined loss observed among the
tested midpoint candidates was approximately:

| Structure | Minimum defined loss | Minimum NLV at 7% risk cap | Minimum NLV at 5% | Minimum NLV at 3% |
|---|---:|---:|---:|---:|
| 20Δ / 10Δ dynamic wings | $928 | ~$13,257 | ~$18,560 | ~$30,933 |
| 20Δ / $5 fixed wings | $311 | ~$4,443 | ~$6,220 | ~$10,367 |
| 20Δ / $10 fixed wings | $665 | ~$9,500 | ~$13,300 | ~$22,167 |

These are **minimum theoretical NLV thresholds based only on the smallest
holdout defined loss**. They are not recommendations for an account size and
do not account for fees, future loss changes, lifecycle overlap, or broker
specific requirements.

At $2,000, the 7% ceiling is $140. Therefore even the smallest observed
defined loss for every tested wider-wing structure exceeds the maximum allowed
risk. The 50% modeled buying-power ceiling is not the binding constraint in
these cases; the defined-risk ceiling is.

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

1. **$2,000 is currently the binding constraint.**
2. Candidate-level OPTIONS-002 holdout P&L is insufficient for deployment
   evaluation when the account-feasibility replay cannot open the trades.
3. No OPTIONS-002 wider-wing candidate should be promoted on the basis of the
   candidate-level comparison alone.
4. Further options research should first answer whether a different structure,
   contract multiplier, entry credit, or capital rule can produce genuine
   2023+ $2,000 feasibility without weakening the risk controls.
5. Any such change must be tested on training/validation first and then carried
   unchanged into the untouched holdout.

## Reproducibility

Use:

    python research/analyze_options002_capital_holdout.py

The script writes:

    data/research/options002_capital_holdout_summary.csv

It does not rank strategies by holdout performance and does not modify the
account-feasibility model.
