# $2,000 OPTIONS-001 Account Feasibility Findings

**Date:** 2026-09-28  
**Historical workflow:** Historical Research run #91  
**Commit under test:** 3981b0b64d0eb3d64ed430c15b9b104cb6379d45  
**Account:** $2,000 starting NLV  
**Strategy candidate:** BROAD_SIDEWAYS  
**Underlying:** SPY  
**Structure:** one short strangle candidate at a time  
**Current modeled BPR ceiling:** 50% of NLV

## Executive finding

The corrected historical account-feasibility replay completed successfully.

The result is decisive for the **current $2,000 naked-SPY-strangle implementation**:

- 929 candidate entries were evaluated.
- 0 were accepted.
- 929 were rejected.
- All four tested combinations (conservative/mid fills × 2× loss-stop/no-stop) produced the same account-level feasibility outcome.
- The dominant rejection was **BUYING_POWER_LIMIT**.
- The account therefore generated no realized P/L under the current account constraints.

This does **not** prove that OPTIONS-001 is intrinsically unprofitable. It proves that the current naked-SPY-strangle implementation cannot express its historical trade set inside the present $2,000/50%-BPR account model.

## Why this matters

The unconstrained historical replay is materially different from the account-constrained replay.

For BROAD_SIDEWAYS:

| Variant | Completed trades | Total P/L |
|---|---:|---:|
| Conservative + 2× loss rule | 110 | $433 |
| Mid + 2× loss rule | 108 | $1,548 |
| Conservative + no-stop | 96 | $5,885 |
| Mid + no-stop | 98 | $7,211 |

These figures are **not account-realizable $2,000 results**. They are the unconstrained trade-economics replay and should not be used as evidence that a $2,000 account can reproduce those returns.

The account replay instead rejected every candidate before opening a position.

## BPR scale

The 929 candidate BPR estimates in the corrected artifact had approximately:

- minimum: $1,378
- 10th percentile: $2,426
- median: $4,047
- 75th percentile: $5,937
- 90th percentile: $8,152
- maximum: $11,082

Against a $2,000 account with a 50% BPR ceiling, only $1,000 of BPR is available. The minimum modeled candidate BPR was already above that ceiling.

The median candidate therefore required roughly twice the entire account's value in modeled BPR, before considering the separate stress-loss constraint.

## Controlled capital sensitivity

A secondary local analysis using the completed candidate/outcome artifact indicates that simply increasing capital changes feasibility sharply, but the result is highly sensitive to the BPR ceiling and remains sample-limited:

- At $2,000 and 50% BPR: 0 accepted.
- At $5,000 and 50% BPR: only a small number of candidates become feasible.
- At $10,000 and 50% BPR: substantially more candidates become feasible.
- Raising the BPR ceiling also increases the number of feasible trades, but that is not automatically an acceptable solution because BPR is a risk constraint rather than merely a throughput setting.

These sensitivity figures are exploratory and are not a substitute for rerunning the authoritative account replay with each configuration.

## Current interpretation

The immediate bottleneck is not execution automation.

It is **strategy/account compatibility**.

The current implementation asks a $2,000 account to sell naked SPY premium while limiting modeled BPR to 50% of NLV and also requiring the modeled 20% stress loss to remain below NLV. That combination produces zero deployable trades in the tested historical sample.

Therefore the next research question is not "how do we make the bot trade more?"

It is:

> What options structure can preserve the intended premium-selling/regime-switching objective while being economically expressible by a $2,000 account without weakening the hard risk controls?

## Required next experiments

### 1. Defined-risk options candidate

Construct a separate OPTIONS-002 candidate using defined-risk spreads or another bounded-loss structure.

Measure:

- historical expectancy;
- conservative versus mid fills;
- trade count;
- win rate;
- worst trade;
- maximum defined loss;
- fees;
- BPR;
- account utilization;
- accepted/rejected opportunity rate;
- drawdown;
- stress loss;
- sensitivity to DTE and delta.

Do not silently replace OPTIONS-001. It remains a separate research candidate.

### 2. Capital feasibility curve

Run the same authoritative account replay at several NLV values, including at least:

- $2,000
- $5,000
- $10,000
- $20,000

This establishes the minimum capital at which the current structure begins to have meaningful opportunity throughput.

### 3. BPR-model validation

Compare the research BPR estimate against the actual broker's buying-power preview/requirements for representative contracts when broker testing is available.

The current BPR formula is explicitly a research estimate. It must not be treated as an Alpaca quotation.

### 4. Regime economics

Continue testing whether the options strategy actually adds value specifically during the periods where ETF-001 is weak.

The options strategy does not need to be profitable in every market regime to be useful, but it must provide enough positive, risk-adjusted contribution in its intended regime to justify switching away from ETF-001.

### 5. Portfolio-level test

Only after a viable options structure is found should SWITCH-001 be tested as a combined portfolio:

ETF-001 + OPTIONS candidate + cash + hard portfolio risk controls.

The combined portfolio is the actual product we eventually want to operate autonomously.

## Deployment implication

The current $2,000 naked-SPY-strangle configuration is **not deployment-ready**.

No production or live-execution code should be built around the assumption that this particular options configuration is viable at $2,000.

The correct next step is to find a viable strategy/account combination while preserving the hard risk controls, then build autonomous execution around the validated contract.
