# OPTIONS-002 Wider-Wing Research Results — 2026-10-01

## Run status

GitHub Actions run #12 completed successfully. The run generated 409 artifact files covering fixed-width $5/$10 wings, dynamic 20-delta/10-delta long wings, ALL_DAYS/BROAD_SIDEWAYS/TURBULENT_ONLY entry filters, conservative/mid fills, and $2,000/$5,000/$10,000 account-feasibility ladders at 3%/5%/7% defined-risk ceilings.

This report is descriptive research. It does not promote a candidate or use holdout results for optimization.

## Capital-feasibility findings

At $2,000 starting NLV, the account-feasibility replay accepted trades only for the dynamic 20/10-delta candidate:
- 20-delta short / 10-delta long, ALL_DAYS, conservative, 7% risk: 2 accepted trades, -$37.40.
- 20-delta short / 10-delta long, ALL_DAYS, mid, 3% risk: 2 accepted trades, +$258.60.
- 20-delta short / 10-delta long, ALL_DAYS, mid, 5% risk: 4 accepted trades, +$238.20.
- 20-delta short / 10-delta long, ALL_DAYS, mid, 7% risk: 4 accepted trades, +$238.20.
- The $5 fixed-wing and $10 fixed-wing candidates had zero accepted trades at $2,000 across the tested configurations.

The $2,000 results have very small accepted-trade counts and therefore should not be treated as evidence of stable profitability.

At $5,000, the dynamic 20/10-delta candidate had 45 accepted trades across the tested account configurations, while the $5 fixed-wing candidate had 86 and the $10 fixed-wing candidate had zero. Aggregated P&L across configurations was +$684.00, -$1,485.20, and $0 respectively. These aggregates are not a portfolio backtest; they sum separate feasibility configurations and should not be interpreted as deployable returns.

At $10,000, the dynamic 20/10-delta candidate had 440 accepted trades, the $5 fixed-wing candidate 1,417, and the $10 fixed-wing candidate 30. Aggregated P&L across configurations was +$3,457.00, -$5,237.40, and -$1,917.00 respectively. Again, these are sums across independent tested configurations, not a single trading account.

## Chronological holdout observations

The chronology analysis uses:
- TRAIN: 2010–2018
- VALIDATION: 2019–2022
- HOLDOUT: 2023 onward

For the ALL_DAYS candidate on the holdout period:
- Dynamic 20/10-delta: conservative +$316 over 44 trades; midpoint +$638 over 42 trades.
- 20-delta/$10 fixed wing: conservative -$379 over 44 trades; midpoint -$723 over 42 trades.
- 20-delta/$5 fixed wing: conservative -$108 over 45 trades; midpoint -$474 over 42 trades.

The filtered candidates also produced positive descriptive holdout P&L in this dataset, but they have substantially fewer trades and therefore require additional validation before any decision.

## Important limitations

1. Account-feasibility results are constrained by the modeled defined-risk and buying-power gates. They are not broker buying-power previews.
2. A large number of candidate rows are rejected because of unresolved lifecycle data and/or position overlap. This means accepted-trade counts are much smaller than raw replay-trade counts.
3. The holdout figures are descriptive observations, not an optimization target.
4. No candidate is promoted from this run.
5. The $2,000 account remains the key practical constraint: the wider fixed-wing structures were generally infeasible under the tested risk ceilings.
6. The next research stage should test the surviving structurally feasible approach on common dates against the ETF alternatives and independently validate lifecycle handling, fill assumptions, and account constraints before any live/paper deployment decision.

## Workflow cleanup

The one-time push trigger used to launch this research run has been removed. The OPTIONS-002 workflow is back to manual dispatch only.
