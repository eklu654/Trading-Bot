# Re-entry Confirmation Experiment Preregistration — 2026-10-11

## Question
Can one simple trend-confirmation gate permit earlier partial re-entry after QQQ shocks without repeatedly buying false rebounds, and without the excessive upside cost observed in DMA overlays?

## Control and context
- Control B0 remains unchanged: exit after QQQ adjusted-close daily return <= -4.5%; re-enter at the first close at least +10% above the running low; signal executes at next TQQQ open.
- Initial capital $5,000; actual TQQQ evaluation starts at inception on aligned QQQ/TQQQ sessions; same frozen input snapshot across all candidates; execution costs 0/10/25/50 bps per exposure change.
- Prior results are context, not candidates to promote: B0 approximately $4.04M and -73.53% max drawdown; immediate re-entry and simple +5%/+10% staging underperformed. The prior DMA family was rejected because wealth loss was too large relative to drawdown improvement.
- Existing R2P is the preregistered staged-re-entry comparison, retaining 50% exposure after a renewed shock once staged. R2 remains an exploratory reset-to-cash comparison.

## New candidate R3 (one fixed rule; no threshold sweep)
1. The initial -4.5% shock exits to cash.
2. Continue tracking the lowest QQQ adjusted close since the defensive episode began; a renewed shock resets this low and recovery reference.
3. Re-enter at 50% only when both conditions hold at a close: QQQ is at least 5% above the running low AND QQQ closes above its 20-session simple moving average.
4. After staging, retain 50% through renewed shocks and update the running low. Restore 100% only when QQQ is at least 10% above the current running low AND closes above the 20-session SMA.
5. Every signal executes at the next TQQQ open; no same-close fills or look-ahead.
6. No tuning of the 5%, 10%, 20-session, or 50% levels based on this run.

## Decision criteria
- First gate: unit tests and accounting invariants must pass. Any failure invalidates the run.
- Compare R3 against B0, R1, R2, and R2P on terminal wealth, CAGR, max drawdown, worst rolling 252-session return, minimum equity, average exposure, days at 0/50/100%, exposure changes, and 0/10/25/50 bps costs.
- A candidate is not promoted merely for lower drawdown. It must preserve a substantial majority of B0 terminal wealth and show a meaningful drawdown or worst-year improvement across costs, without relying on one crisis episode.
- If R3 fails the trade-off, reject this rule and do not tune its SMA length or rebound thresholds. Next research step should be event-level attribution and a separately preregistered, distinct hypothesis.
- Actual TQQQ history is not evidence for 2000: TQQQ did not exist then. Any pre-inception stress test must be a separately labeled synthetic daily-reset simulation on underlying index data.

## Run / audit trail
- Branch: `research/qqq-slow-bear-audit`.
- Workflow: [Re-entry isolation experiment](https://github.com/eklu654/Trading-Bot/actions).
- Candidate implementation: `research/reentry_isolation.py`, identifier `R3`.
- Tests: `tests/test_reentry_isolation.py`.
- This preregistration is committed before interpreting the new run's performance.
