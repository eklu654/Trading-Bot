# Composite Fed + Macro + DMA Structural Defense — 2026-10-05

## Research question

The Fed lifecycle study showed that monetary-policy lifecycle matters, but the
live-safe Fed-state proxy alone was not sufficient to protect leveraged
exposure from every structural bear-market failure.

The macro baseline independently showed that broad economic deterioration is
economically meaningful but can be too late when used alone.

The next hypothesis is therefore deliberately structural:

> A defensive state should activate when either monetary-policy transmission
> has entered a dangerous paused-tightening state while the market is already
> below trend, or the broader economic regime has entered persistent
> deterioration; once activated, the defense should persist until both the
> market and macro regime have recovered.

## Frozen composite rule

### Enter defense

Enter the defensive state when either condition is true:

1. **Fed + market trigger**
   - QQQ below its 200-DMA; and
   - Fed state is TIGHTENING_PAUSED.

2. **Macro trigger**
   - macro state is MACRO_DETERIORATION or MACRO_CRISIS.

### Exit defense

Exit only when both are true:

- QQQ is above its 200-DMA; and
- macro state is STRUCTURAL_EXPANSION.

The rule is intentionally asymmetric. Entry can occur from either monetary
or economic deterioration; recovery requires both market and macro
confirmation.

## Frozen exposure family

Test only:

- 0% TQQQ during defense;
- 25%;
- 50%;
- 75%.

BUY_AND_HOLD remains the permanent maximum-growth benchmark.

A newly observed close signal is applied starting with the next trading day.
This prevents same-day close information from influencing the same day's
return.

## Why this is the logical next test

The preceding evidence points to different failure modes:

- Fed lifecycle information identifies when tightening effects may continue
  after active hikes have stopped.
- The Fed-state × DMA study found especially poor outcomes in
  BELOW_DMA + TIGHTENING_PAUSED.
- The macro classifier identifies broader deterioration but recognizes the
  dot-com regime too late to be a standalone leveraged-ETF escape mechanism.
- A persistent state is preferable to repeatedly reacting to individual
  observations.

This test therefore combines the layers instead of optimizing another DMA.

## Required comparisons

The primary comparison is full-history terminal wealth from $5,000, with:

- CAGR;
- maximum drawdown;
- minimum equity;
- average exposure;
- defensive duration;
- transition count.

The family must be judged against BUY_AND_HOLD and the already-closed DMA
family.

## Guardrails

- No new DMA-length search.
- No re-entry-delay search.
- No named-crisis tuning.
- No final-hike hindsight.
- No threshold optimization after seeing the final outcome.
- Existing macro thresholds remain frozen.
- Existing Fed-state definition remains frozen.
- Synthetic TQQQ remains the full-history descriptive proxy.

## Interpretation gate

A composite strategy is not a success merely because terminal wealth rises.

It must materially improve the wealth/drawdown tradeoff and remain
chronologically defensible.

If the composite still leaves catastrophic drawdowns, the next step should
focus on whether the economic/credit regime can identify the structural break
earlier, rather than adding more arbitrary price thresholds.

## First full-history result

The frozen composite completed successfully.

| Strategy | Final balance | CAGR | Max drawdown |
|---|---:|---:|---:|
| BUY_AND_HOLD | $39,448 | 7.78% | -99.96% |
| COMPOSITE_STRUCTURAL_0 | $2,317,044 | 24.94% | -85.89% |
| COMPOSITE_STRUCTURAL_25 | $1,871,567 | 23.98% | -89.31% |
| COMPOSITE_STRUCTURAL_50 | $886,184 | 20.66% | -97.38% |
| COMPOSITE_STRUCTURAL_75 | $245,459 | 15.17% | -99.53% |

The 0% and 25% defense variants are a substantial improvement over
buy-and-hold on this synthetic full-history path. However, the result is not
yet a production candidate because the same frozen rule gives up meaningful
wealth during the modern period.

Chronological slices of the frozen rule show:

- 1999–2009: the 0% defense variant strongly improves the catastrophic
  dot-com path.
- 2010–2019: all composite variants trail buy-and-hold while providing no
  additional maximum-drawdown reduction.
- 2020–2026: the composite remains substantially below buy-and-hold in CAGR;
  only the more aggressive 75% defense approaches the modern-period wealth
  benchmark, while the drawdown remains dominated by the underlying leveraged
  exposure.

This means the composite has demonstrated **historical structural
recognition**, but not yet the required modern-era opportunity-cost discipline.

**Classification: PROMISING, NOT YET ROBUST.**

The important finding is that the Fed layer and macro layer add information
when combined with market trend, but the current macro classifier is still too
broad/late and the defense can remain active during modern expansion periods.

The next research gate should therefore be a chronological holdout/robustness
study of the frozen composite, followed by targeted investigation of which
specific economic/credit dimension can distinguish true structural breaks
from ordinary modern corrections. No further DMA parameter search is
justified.

## Chronological robustness result

The frozen rule was then evaluated without changing any parameters across three
fixed periods.

### 1999–2009

The 0% defense variant produced a +21.68% CAGR with -80.13% maximum drawdown,
versus -31.89% CAGR and -99.96% drawdown for buy-and-hold.

This confirms that the composite can materially change the catastrophic
pre-2010 path.

### 2010–2019

Buy-and-hold produced a 44.27% CAGR.

The composite variants produced:

- 75%: 42.94% CAGR;
- 50%: 41.49%;
- 25%: 39.93%;
- 0%: 38.27%.

All had the same approximately -57.92% maximum drawdown as buy-and-hold.

Therefore the composite did **not** improve the modern risk/return tradeoff in
this period; it simply reduced exposure and sacrificed wealth.

### 2020–2026

Buy-and-hold produced a 44.09% CAGR with -80.79% maximum drawdown.

The composite variants produced:

- 75%: 36.99% CAGR;
- 50%: 28.91%;
- 25%: 20.09%;
- 0%: 10.74%.

Again, maximum drawdown was essentially unchanged for the 25%–75% variants,
while the 0% variant was worse at -85.89%.

## Robustness classification

**CLASSIFICATION: HISTORICALLY EFFECTIVE, MODERN-ERA OVER-DEFENSIVE.**

The composite is not yet a strategy candidate.

The research has now answered an important question: the Fed + macro + DMA
architecture can recognize the dot-com-style structural break, but the current
macro classifier does not distinguish that environment cleanly enough from
modern conditions. It therefore pays too much opportunity cost after 2010
without delivering incremental drawdown protection.

This is exactly the kind of result the holdout gate was intended to expose.

The Fed layer remains in the architecture. The next research should not search
more exposure percentages or DMA lengths. Instead, it should identify which
economic/financial dimension is genuinely distinctive in structural failures
such as 2000–2002 and 2007–2009 while avoiding unnecessary defense during
modern bull-market corrections.
