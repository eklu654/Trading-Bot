# Fed Paused-State × DMA Sticky Defense — 2026-10-05

## Purpose

The completed Fed lifecycle study identified the most important historical
risk cell as the period after tightening had stopped while the market had
already fallen below its 200-DMA. The frozen contemporaneous Fed-state study
also found unusually poor forward outcomes for:

> BELOW_DMA + TIGHTENING_PAUSED

This study converts that descriptive finding into the first small,
predeclared strategy family.

## Live-safe rule

The strategy does **not** use the historical final-hike date.

Defense is triggered only when both conditions are knowable on the decision
date:

1. QQQ is below its 200-DMA.
2. The Fed state is TIGHTENING_PAUSED:
   - no hike in the trailing 90 calendar days;
   - no cut in the trailing 90 calendar days;
   - the 12-month target-rate change remains positive.

Once triggered, the strategy remains in its defensive exposure until QQQ closes
above its 200-DMA.

This persistence is intentional. It tests whether the dangerous regime should
be treated as a state rather than as a one-day exit signal.

## Frozen exposure family

No optimization is performed. The only defense exposures are:

- 0% TQQQ;
- 25% TQQQ;
- 50% TQQQ;
- 75% TQQQ.

BUY_AND_HOLD remains the maximum-growth benchmark.

Existing 200-DMA / 50% and 200-DMA / 75% controls are included only as
reference controls.

## Why this test follows the lifecycle study

The lifecycle study found that POST_FINAL_HIKE_LAG + BELOW_DMA had materially
worse forward synthetic-TQQQ outcomes than POST_FINAL_HIKE_LAG + ABOVE_DMA.
The live-safe Fed state cannot know the eventual final hike, so the strategy
uses TIGHTENING_PAUSED as the contemporaneous proxy.

The sticky exit rule is also designed to address the failure mode of a
one-day Fed/DMA signal: a bear-market rally can temporarily restore the DMA
condition while the structural damage is still unfolding.

## Required interpretation

The study is successful only if it demonstrates a meaningful improvement in
the wealth/drawdown tradeoff without relying on hindsight.

A large improvement in the 2000–2002 path alone is insufficient.

The full historical sequence from the fixed $5,000 starting balance is the
primary test. Results will be compared with:

- BUY_AND_HOLD;
- DMA_200_50;
- DMA_200_75.

The Fed layer remains permanent regardless of the outcome. A weak result means
this representation of monetary-policy state is insufficient, not that the
Fed layer should be discarded.

## Guardrails

- No threshold search.
- No named-crisis tuning.
- No final-hike knowledge.
- No publication-vintage hindsight beyond the existing FRED state construction.
- No new DMA-length search.
- No re-entry-delay search.
- Synthetic TQQQ remains a descriptive daily-reset proxy before the actual
  TQQQ era.

## Next gate

If this family fails, the next research direction should move upward from the
Fed-state proxy toward the broader economic/credit regime rather than
continuing to tune DMA parameters.

If it materially improves the tradeoff, freeze the exact rule and validate it
chronologically on separated training/validation/holdout periods before any
production consideration.

## First full-history result

The frozen family completed successfully.

| Strategy | Final balance | CAGR | Max drawdown |
|---|---:|---:|---:|
| BUY_AND_HOLD | $66,247 | 49.59% | -99.96% |
| FED_PAUSED_DMA_STICKY_0 | $3,706,234 | 73.11% | -98.13% |
| FED_PAUSED_DMA_STICKY_25 | $1,917,262 | 69.01% | -98.97% |
| FED_PAUSED_DMA_STICKY_50 | $788,528 | 63.65% | -99.55% |
| FED_PAUSED_DMA_STICKY_75 | $257,311 | 57.14% | -99.84% |

The rule materially improved terminal wealth on the synthetic full-history
path, especially at 0% defense exposure, but it did **not** solve leveraged
survivability: maximum drawdown remained approximately 98%.

The family also produced repeated short-lived exits during 2016 because the
QQQ 200-DMA condition repeatedly crossed while the Fed remained paused. That
is a concrete indication that the simple sticky state is not sufficiently
stable for production use.

**Classification: PROMISING HISTORICAL SIGNAL, REJECTED AS A STANDALONE
PRODUCTION CONTROL.**

The result is valuable because it validates the research hypothesis that
contemporaneous monetary-policy state can identify a dangerous post-tightening
environment when combined with market trend. It is not sufficient by itself
because it does not provide acceptable drawdown protection and is vulnerable
to choppy reactivation.

The next test therefore combines this Fed signal with the broader macro
regime rather than tuning the DMA trigger or re-entry delay.
