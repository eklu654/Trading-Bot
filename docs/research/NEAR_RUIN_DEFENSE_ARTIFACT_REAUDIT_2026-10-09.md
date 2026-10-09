# Near-Ruin Defense Gate — Completed Artifact Re-audit (2026-10-09)

Status: analysis of an existing completed run; no new backtest or strategy promotion is claimed.

## Source and execution audit

Inspected [run 37915725568](https://github.com/eklu654/Trading-Bot/actions/runs/37915725568), job `audit` (success), artifact `11609492820`. The job ran `research/failed_bounce_robustness.py` and uploaded the frozen aligned QQQ/TQQQ data, daily equity, event counterfactuals, period summaries, and cost table. The script imports `research/causal_execution.py`; its implementation correctly uses the prior executed weight for the overnight leg and the new executed weight for the intraday leg. This is inspection of a prior run, not a new run during this continuation.

## Confirmed artifact results

- B0: approximately $4.040315M ending balance and -73.5343% maximum drawdown.
- Actual-TQQQ buy-and-hold: approximately $2.094669M and -81.6598% maximum drawdown.
- Transition-cost sensitivity: about $4.002M at 5 bps, $3.964M at 10 bps, $3.851M at 25 bps, and $3.671M at 50 bps. Maximum drawdown changes only modestly across these costs.

## Event-level counterfactual diagnosis

Removing the defense for one event at a time increased terminal wealth for the 2020-06-11 shock by about $1.019M, the 2020-09-03 shock by about $328k, and the 2025-04-03 event by about $236k. Conversely, the defense was beneficial for the 2018 Q4 event (about $818k terminal difference), the 2020-02-27 event (about $1.345M), and the two 2022 events (about $740k and $612k). These counterfactuals are each measured against the shared full-strategy terminal curve; they are not additive causal effects and do not prove that a simple calendar/context filter generalizes.

## Revised next-step diagnosis

The problem is event discrimination: retain protective exits during established/persistent weakness while avoiding damaging exits during fast recoveries. Do not simply suppress shocks whenever trailing 60-session return is positive; that could also suppress the February 2020 protection event. Before any full replay, the candidate state timeline must distinguish the beneficial 2018 Q4 / February 2020 / 2022 defenses from damaging June/September 2020 and April 2025 exits without future knowledge. If it cannot, reject the candidate before running the wealth replay.

No new candidate backtest was run, and no rule is promoted by these findings.
