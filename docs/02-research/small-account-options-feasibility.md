# Small-Account Options Feasibility Research

**Status:** Research decision — not a production rule  
**Last reviewed:** 2026-09-28

## 1. Finding

The historical 2020 portfolio framework remains useful as a provenance baseline, but current tastylive research makes clear that small accounts face structural constraints when using undefined-risk positions.

In June 2025, tastylive specifically documented that small accounts can face substantially higher BPR and BPR volatility with naked positions. It reported an example in which a 15% IWM move increased BPR by more than 200%, with a worst-case example reaching 3.6× initial BPR. It also notes that lower-priced underlyings can improve premium-to-BPR efficiency.

A separate June 2025 guide says that $10,000 accounts already face meaningful constraints with naked strategies and suggests risk-defined structures such as spreads, iron condors, and time spreads for broader diversification.

These sources do not establish a universal rule that $2,000 accounts must use defined risk. They establish that account size materially changes the feasible strategy universe.

## 2. Project implication

The $2,000 OPTIONS-001 account must therefore be treated as a **feasibility experiment**, not simply as a scaled-down implementation of the historical 75/25 framework.

The system must measure:

- percentage of candidate trades rejected because of contract granularity;
- percentage rejected because of BPR;
- percentage rejected because of NLV sizing;
- percentage rejected because of the 15% underlying concentration limit;
- number of simultaneously feasible positions;
- achievable diversification;
- BPR expansion under stress;
- defined-risk versus undefined-risk opportunity frequency.

The bot must not relax the historical sizing rules merely to create more trades.

## 3. Initial account-size experiment

Run the same strategy framework at:

- $2,000
- $5,000
- $10,000
- $25,000
- larger reference accounts where useful

The objective is to determine where the strategy becomes operationally feasible.

Do not interpret better performance at a larger account as evidence that the strategy itself is better. The experiment is primarily about constraint feasibility, diversification, and risk behavior.

## 4. $2,000 structure-selection hypothesis

For the $2,000 account, the first research pass should explicitly compare:

### A. Historical-mix model

Attempt to preserve the historical:

- VIX BP ceiling;
- 75% undefined / 25% defined allocation;
- 3–7% NLV undefined sizing;
- 1–3% NLV defined sizing;
- 15% single-underlying limit.

Record every infeasible trade rather than modifying the rules.

### B. Defined-risk feasibility model

Permit only defined-risk structures while preserving the other portfolio controls.

Candidate structures:

- vertical credit spreads;
- iron condors;
- iron butterflies where appropriate;
- other defined-risk premium structures supported by the finalized strategy universe.

This is an **experimental comparison**, not a claim that tastylive universally recommends this exact $2,000 configuration.

## 5. Why this matters

The historical framework can mathematically permit a $60–$140 undefined-risk trade in a $2,000 account, but that does not mean an actual option contract can satisfy the intended percentage allocation.

Contract granularity, broker BPR formulas, option liquidity, and assignment risk can make the theoretical sizing infeasible.

The system must distinguish:

**theoretical allocation**

from:

**actually executable contract size**.

## 6. Beta-weighted Delta limitation

Recent tastylive material reinforces that beta-weighted Delta is useful for standardizing portfolio directional exposure, but it is not sufficient by itself.

A 2025 tastylive discussion notes that low-correlation products can underestimate actual risk when correlations rise sharply during volatility spikes, and that gamma must also be monitored for changing exposure.

Therefore the project will **not** freeze a numerical beta-weighted-Delta neutrality band until the underlying study/data is recovered.

The risk engine will continue to treat beta-weighted Delta as one dimension alongside:

- gamma;
- BPR;
- BPR expansion;
- notional/unit exposure;
- correlation;
- maximum loss;
- stress scenarios.

## 7. Undefined-risk defense

Official tastylive material on strangles documents rolling the untested side as a defensive technique after the tested side is breached. A 2025 study also reports favorable historical results for rolling the untested side in its tested scenario.

This does **not** justify automatically coding "always roll the untested side."

Before implementation, compare at minimum:

1. close immediately;
2. hold;
3. roll untested side;
4. roll tested side;
5. roll entire position;
6. convert to defined risk where operationally possible.

Each must be tested with identical entry conditions and realistic execution assumptions.

## 8. Current research conclusion

The project should preserve the historical tastytrade framework as a documented benchmark while treating the $2,000 account as a separate feasibility experiment.

The research question is not:

> "How do we force the historical portfolio into $2,000?"

It is:

> "At what account size and under what structure constraints does the documented methodology become executable without silently violating its own risk controls?"

That distinction is now part of the research specification.
