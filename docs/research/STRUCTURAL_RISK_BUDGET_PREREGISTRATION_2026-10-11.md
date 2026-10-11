# Structural Risk-Budget Experiment Preregistration — 2026-10-11

## Question
Can a simple cap on deployed TQQQ exposure reduce B0's severe drawdown enough to justify its compounding cost, without adding more entry/exit signals?

## Fixed comparison
- Control: verified B0 exactly as implemented in `research/reentry_isolation.py`: QQQ daily adjusted-close loss <= -4.5% exits; re-entry after +10% rebound from the running low; close signal executes next TQQQ open.
- Candidate RB95: when B0 is invested, cap TQQQ target exposure at 95%; when B0 is defensive, remain in cash.
- Candidate RB90: same, capped at 90%.
- No dynamic cap, no additional indicators, no threshold search, no use of future data.
- Initial capital $5,000, actual TQQQ inception onward, aligned QQQ/TQQQ dates, one frozen input snapshot for all candidates.
- Test 0/10/25/50 bps costs per exposure change.

## Decision rule
- Unit tests and independent B0 identity check must pass.
- Compare terminal balance/CAGR, max drawdown, worst rolling 252-session return, minimum equity, exposure, and costs.
- A cap is only worth retaining if it materially improves downside metrics and preserves at least 90% of B0 terminal wealth across reasonable costs. A cosmetic reduction in drawdown is insufficient.
- If neither fixed cap passes, reject the simple fixed-exposure-budget approach in this TQQQ-only setup; do not search additional percentages. Then consider the broader multi-ETF family-allocation architecture separately.
- This is not a test of 2000: TQQQ did not exist then. Pre-inception stress tests must use clearly labeled synthetic daily-reset returns on underlying index data.
