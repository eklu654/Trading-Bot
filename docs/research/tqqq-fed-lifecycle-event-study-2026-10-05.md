# Fed Tightening-Cycle Lifecycle x DMA Event Study — 2026-10-05

## Purpose

The Fed layer is permanent. This study asks whether the interpretation of a
QQQ trend state changes depending on where the economy is in the monetary
policy tightening/easing lifecycle.

## Lifecycle phases

For each completed tightening cycle:

1. PRE_TIGHTENING — 365 days before the first hike.
2. EARLY_TIGHTENING — first 90 days beginning with the first hike.
3. MATURE_TIGHTENING — after the early phase through the final hike.
4. POST_FINAL_HIKE_LAG — first 365 days after the final hike.
5. RESTRICTIVE_PAUSE — after that lag until the first cut, when such a period
   exists.
6. BENIGN_EASING / CRISIS_EASING — first 365 days after the first post-cycle
   cut, classified retrospectively according to whether an NBER recession
   begins within the following 6 months.

The final-hike and recession labels are historical research classifications,
not proposed live signals.

## Market cross-section

Every lifecycle phase is split by QQQ 200-DMA state:

- ABOVE_DMA
- BELOW_DMA

For each cell the study records observation count, number of cycles, forward
3/6/12-month QQQ returns, forward synthetic-TQQQ returns, median returns, and
positive-return frequency.

## Why this is the next test

The existing Fed x DMA study freezes a contemporaneously knowable monetary
state. This lifecycle study deliberately adds historical phase information
because monetary-policy effects are lagged and because active hiking is not
the same condition as a finished hiking cycle whose restrictive effects are
still transmitting.

Federal Reserve research defines tightening cycles using first/last hikes and
discusses lagged transmission through financial conditions and the broader
economy. The Fed has also explicitly noted uncertainty around those lags.

## Critical hypothesis

The hypothesis under examination is:

The dangerous window for leveraged equity exposure may occur after the Fed
stops hiking, when accumulated restriction is finally transmitted into
financial/economic conditions and market trend deterioration becomes visible.

This is a hypothesis, not an assumed result.

## Dot-com versus modern-period question

The lifecycle results will be compared with the earlier DMA survivability work.
In particular, we want to know whether the unusually strong behavior of
shorter DMAs around the dot-com bust reflects a different monetary-policy and
market lifecycle rather than a universally superior DMA.

The 1999-2000 tightening cycle is especially important because the subsequent
NBER recession began in March 2001, after the Fed tightening cycle had ended.
That makes the post-final-hike period a materially different research state
from active tightening.

## Guardrails

- 100% TQQQ buy-and-hold remains the permanent maximum-growth benchmark.
- No strategy parameter optimization is performed here.
- No Fed hike = sell rule is tested.
- No final-hike state is proposed as a live signal.
- Synthetic TQQQ is a descriptive 3x daily-reset proxy, not exact historical
  TQQQ.
- The next strategy experiment should be derived from historical structure,
  not arbitrary threshold searching.
