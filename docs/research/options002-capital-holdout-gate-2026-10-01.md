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
