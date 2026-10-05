# Fed State × DMA Event Study — 2026-10-05

## Research question

Does contemporaneously knowable monetary-policy state add useful information **after the market trend is already known**?

This is the bridge between the Fed event study and the existing DMA/partial-exposure family.

## Frozen classification

No state uses hindsight about the eventual final hike.

- **TIGHTENING_ACTIVE:** at least one Fed hike in the trailing 90 calendar days.
- **TIGHTENING_PAUSED:** no hike or cut in the trailing 90 days and the trailing 12-month target-rate change is positive.
- **EASING:** at least one cut in the trailing 90 days OR the trailing 12-month target-rate change is negative.
- **NEUTRAL:** none of the above.

Market state is independently frozen:

- **ABOVE_DMA:** QQQ adjusted close is at/above its 200-day moving average.
- **BELOW_DMA:** QQQ adjusted close is below its 200-day moving average.

The study is descriptive. It does not claim that Fed policy causes the observed returns.

## What this tests

The important comparison is **within the same DMA state**:

- ABOVE_DMA + each monetary state
- BELOW_DMA + each monetary state

If monetary state has little separation inside a given DMA state, adding Fed policy may add little practical information.

If monetary state materially separates outcomes within BELOW_DMA, that would support the hypothesis that monetary policy can act as a **risk-state modifier** rather than a standalone sell trigger.

## Outputs

The workflow produces:

- `tqqq_fed_dma_daily_states.csv` — contemporaneous state for every QQQ trading day.
- `tqqq_fed_dma_event_observations.csv` — forward 3/6/12-month QQQ returns for each state/date.
- `tqqq_fed_dma_event_summary.csv` — grouped means, medians, and positive-return frequency.

## Guardrails

- No parameter search.
- No dot-com-specific optimization.
- No "final hike" state.
- No strategy trading simulation yet.
- The permanent 100% TQQQ buy-and-hold benchmark remains untouched.
- The next decision should be based on whether monetary state provides incremental information over DMA, not whether one arbitrary Fed threshold happens to maximize historical wealth.

## Interpretation

This is intentionally a **falsification gate**.

If Fed state does not materially improve separation after DMA is known, stop adding Fed complexity to the trading architecture.

If it does, freeze the classifier and only then test a small, predeclared Fed-state × DMA exposure family against the full historical sequence, with terminal balance as the primary objective.
