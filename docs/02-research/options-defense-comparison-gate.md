# OPTIONS-001 Defense Comparison Gate

**Status:** Research gate — do not promote a defense rule  
**Date:** 2026-09-28

## Purpose

The current research question is whether active management of a challenged short strangle improves the outcome relative to leaving the position alone under the same no-stop baseline.

The temporary 2x-credit loss threshold has been removed from this comparison. It was a research placeholder and the no-stop replay materially changed the earlier conclusion about turbulent/high-volatility entries.

## First comparison

The first controlled comparison is:

1. **NO_ADJUSTMENT** — original strikes remain unchanged until the normal 50% profit target or 21 DTE exit.
2. **ROLL_UNTESTED** — after an EOD close reaches/breaches one original short strike, close the opposite untested short and replace it at the same expiration with a deterministic closer strike.

Both variants use:

- SPY
- 2010–2025 replay
- BROAD_SIDEWAYS candidate
- approximately 45 DTE entry
- 30–60 DTE selection window
- approximately 16-delta short call and put at entry
- one position at a time
- 50% profit target
- 21 DTE exit
- conservative bid/ask and midpoint sensitivity
- one defensive adjustment maximum in the first experiment

The challenge trigger is deliberately an EOD close at/beyond the current short strike because the public dataset is EOD-only.

## What counts as meaningful evidence

A roll is **not** promoted merely because its aggregate P/L is higher.

The comparison must report, for each fill model:

- completed trades
- total P/L
- mean P/L/trade
- median P/L/trade
- win rate
- worst trade
- lower-tail trade outcomes
- maximum observed open debit proxy
- number and percentage of challenged trades
- number and percentage of adjusted trades
- adjustment cash-flow contribution
- final exit reason
- results split by SIDEWAYS_CHOPPY and TURBULENT_HIGH_VOL
- chronological development / validation / holdout performance where the existing replay partitions permit it

The key question is whether the defense improves challenged-trade and tail behavior **without merely shifting losses into adjustment debits or relying on favorable midpoint execution**.

## Promotion gate

`ROLL_UNTESTED` remains a research candidate unless all of the following are true:

1. It improves or materially preserves aggregate results under both fill models.
2. The improvement is not explained solely by midpoint execution.
3. Challenged trades show a measurable reduction in adverse outcomes or improved recovery.
4. The adjustment itself does not create an unacceptable debit burden.
5. The result is not concentrated in one small historical episode.
6. The result remains directionally consistent outside the development period.
7. No look-ahead information is used to select the replacement strike.

If those conditions are not met, the roll is retained as a failed/neutral research variant and the project does **not** proceed to a more complex defense state machine.

## Next escalation

Only if `ROLL_UNTESTED` clears the gate should the next experiments be:

1. **ROLL_OUT** — move the challenged structure to a later expiration using a deterministic DTE target and explicitly measure net credit/debit.
2. **INVERSION** — roll the untested leg through the tested strike using an explicit inversion-width rule.

These are separate experiments. They should not be combined into an optimizer until each mechanism has independent evidence.

This ordering matches the research objective: test the actual management problem first, then add complexity only when the preceding mechanism demonstrates measurable value.

## External methodology reference

tastylive describes short-strangle management as taking profits around 50% of credit or 21 DTE and identifies rolling the untested side, rolling out in time, and going inverted as defensive tactics. Its strangle material specifically describes rolling the untested side closer to the underlying after the tested side is breached. These are being used here as documented strategy concepts, not as proof that any particular mechanical implementation will work on the project's historical data. 

## Current status

The repository contains the deterministic control and `ROLL_UNTESTED` replay. The next factual decision depends on the generated historical results. Roll-out and inversion should remain unfrozen until that comparison is complete.
