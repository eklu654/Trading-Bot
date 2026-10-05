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

The study is descriptive. It does not claim that Fed policy causes the observed returns. The Fed layer is a permanent research component of the strategy architecture; this study determines which monetary-policy dimensions and interactions are useful, not whether the Fed layer should exist.

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

## Calendar lookback

The trailing 12-month target-rate change is calculated against the most recent available FRED observation on or before the exact date one calendar year earlier. A fixed `shift(365)` is deliberately not used because FRED's policy-rate series does not guarantee one observation per calendar day.

## Guardrails

- No parameter search.
- No dot-com-specific optimization.
- No "final hike" state.
- No strategy trading simulation yet.
- The permanent 100% TQQQ buy-and-hold benchmark remains untouched.
- The next decision should be based on whether monetary state provides incremental information over DMA, not whether one arbitrary Fed threshold happens to maximize historical wealth.

## Interpretation

This is a **Fed-model discovery study**, not a go/no-go test for the Fed layer.

The Fed layer remains in the architecture regardless of whether this particular four-state classifier adds enough separation. A weak result means we need a better representation of monetary policy — for example policy direction, cumulative tightening, time since the last hike, restrictive-policy persistence, easing context, or interaction with financial/economic stress — rather than that interest rates are irrelevant.

If the frozen state shows useful separation, freeze the useful components and test a small, predeclared Fed-state × DMA exposure family against the full historical sequence, with terminal balance as the primary objective. If it does not, continue researching the Fed transmission mechanism before adding trading parameters.
