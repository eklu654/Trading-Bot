# Actual-TQQQ failed-bounce feature audit — results

Date: 2026-10-09  
Status: **Insufficient sample; no feature or rule selected.**

## Run
- Workflow: [run 37913829194](https://github.com/eklu654/Trading-Bot/actions/runs/37913829194), job passed.
- Artifact ID: `11608750829`; digest: `sha256:d4ce774670f11686207d016be509afb5a7495125fc0cc45d6452af8757ced60e`.
- Data: nine canonical QQQ shock/recovery events aligned to actual TQQQ, 2010-02-11 through 2026-10-07. Features were measured at the +10% recovery decision; forward labels were retrospective diagnostics only.

## Outcome counts and central limitation
Of nine events, seven were labeled successful, one failed, and one was censored. The sole failed event was the 2022-07-19 recovery after the 2022 drawdown; the 2026-08-13 event had not resolved within the label horizon. With only one resolved failure, means/medians by class are not statistically meaningful and cannot establish a generalizable detector.

The failed 2022 event had:
- recovery speed 21 sessions from low;
- QQQ 60-session return -10.6%, 120-session return -13.3%, 200-session return -16.3%;
- price 13.8% below its 200-DMA, despite being 2.1% above its 50-DMA;
- seven bearish moving-average pair relationships and only one bullish pair relationship.

But several successful recoveries also occurred with negative intermediate returns and substantial moving-average damage: 2018-2019, COVID March 2020, and April 2025 are direct counterexamples to simple “below long DMA / negative momentum means veto” rules. The April 2025 successful event even had negative MACD histogram and MACD below signal at the recovery decision.

## Decision
Do not fit a classifier or threshold to this sample. This audit supports the intuition that broad trend damage can coexist with both failed and successful recoveries; the available actual-TQQQ sample does not identify a reliable veto condition. Keep B0 unchanged as the control. Any future candidate must have a small predeclared rule, preserve rapid rebounds, and be judged primarily on same-input terminal wealth and drawdown—not feature separation on nine events.
