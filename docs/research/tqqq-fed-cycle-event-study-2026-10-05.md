# Fed-Cycle Event Study — 2026-10-05

## Purpose

Test the hypothesis that Federal Reserve tightening is best treated as a **risk-state modifier**, not a standalone TQQQ sell signal.

The first stage is descriptive. It establishes the Fed's historical actions and measures market behavior around tightening cycles before any Fed-aware DMA strategy is built.

## Fixed strategy benchmark

The maximum-growth tier is permanently:

- 100% TQQQ
- no DMA
- buy and hold

It is a control, not an optimizable parameter.

## Historical tightening cycles

Use the Federal Reserve's published cycle boundaries:

- 1994-02 to 1995-03
- 1999-07 to 2000-07
- 2004-06 to 2006-08
- 2015-12 to 2018-07
- 2022-03 to the final hike in July 2023 (treated as a completed tightening cycle for this event study)

The Federal Reserve identifies these cycles in its financial-conditions research.

## First-stage questions

1. How much did the Fed tighten in each cycle?
2. How long did each cycle last?
3. What happened to Nasdaq-100 and TQQQ after the first hike?
4. What happened after the final hike?
5. How often did a major U.S. equity deterioration follow?
6. Does 1994-95 behave as a useful control case where tightening created financial stress without a U.S. recession?
7. Is the post-final-hike window materially different from the active-hiking window?

## Guardrails

- No strategy parameters are optimized in this stage.
- Fed activity is not a direct sell signal.
- Market outcomes are measured after the fact only for research classification.
- Do not use future Fed actions to classify a date in a live strategy.
- Actual TQQQ is used where available; Nasdaq-100 is retained for the pre-TQQQ period.
- This is an event study, not yet the Fed × DMA optimization.

## Next stage

After the event study passes validation, classify daily/monthly monetary states from information available at the time and cross them with the existing DMA/partial-exposure family.

The eventual comparison remains terminal balance first, with CAGR and drawdown as diagnostics.


## Implementation status

The next-stage frozen Fed-state × DMA event study is now implemented separately in `research/test_tqqq_fed_dma_event_study.py` so the original descriptive cycle study remains unchanged.
