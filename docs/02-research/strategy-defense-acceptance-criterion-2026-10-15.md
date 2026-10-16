# Strategy Defense Acceptance Criterion — 2026-10-15

## Binding decision rule

A defensive overlay does **not** succeed merely because it lowers maximum drawdown. Its primary acceptance criterion is a **higher terminal account balance** than the corresponding unprotected strategy over the same dates, with the same starting capital and comparable assumptions.

A defense that reduces drawdown but ends with less money is not a successful defense under the project's objective. Drawdown remains an important risk diagnostic and a constraint against near-ruin, but it is not a substitute for terminal wealth.

## Required comparisons

For every defense/overlay candidate, compare it against its exact frozen control (B0 or the relevant unprotected candidate) using:

1. Same start/end dates, starting balance ($5,000), instrument universe, data source, and trading calendar.
2. Terminal balance in dollars and relative to the matched control.
3. Annual returns and years in which the candidate underperforms the control.
4. Maximum drawdown, worst day, recovery time, exposure/turnover, and trading-cost sensitivity.
5. Near-ruin / account-wipeout risk, including slow bear markets and rapid bear-market rallies/recoveries.
6. Validation and holdout results separately; no selecting thresholds from holdout results.

## Decision policy

- **Reject as a successful defense** if terminal balance is lower than the matched control, even if drawdown improves.
- **Do not promote automatically** just because terminal balance is higher; still assess near-ruin risk, robustness, costs, and out-of-sample performance.
- Report drawdown as a secondary risk metric and terminal wealth as the primary optimization objective.
- Keep B0 frozen during defense research. Keep F75 shadow-only unless and until it passes the same matched-control test.
- Do not mix incomparable date ranges or use different return compounding conventions in control/candidate comparisons.

## Current research implication

The E4c 1x cap result from the 2026-10-16 research pass (holdout return +81.2% versus SPY +111.5%) is not a successful SPY-beating candidate. More importantly for defense evaluation, any overlay with a lower terminal balance than its matched B0/control is not a successful defense under this project rule, regardless of its drawdown improvement. Candidates with higher holdout returns but catastrophic validation losses also remain rejected pending robust validation.

This is a project-level evaluation rule, not a claim that lower drawdown has no value; it means lower drawdown alone does not satisfy the project's success criterion.
