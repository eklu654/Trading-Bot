# Research Continuation Log — 2026-10-10

## Scope of this pass

Reviewed the existing Fed/macro/200-DMA research and the new isolated slow-bear counterfactuals before selecting another experiment. This is a decision/audit note; no strategy rule or backtest result was changed in this pass.

## Repository state

- Work remains isolated on branch `research/qqq-slow-bear-audit`.
- Branch head when this note was prepared: `9be27e6ef9d53b1bdc7fc9caf5c108ad6ac60c94`.
- No changes from this branch were merged to `main`.
- Canonical B0 remains the control: QQQ adjusted-close daily return <= -4.5% exits TQQQ at the next open; re-enter after QQQ closes >=10% above the post-shock low; $5,000 initial capital.
- Do not treat retrospective 2010–2026 results as an untouched holdout.

## New slow-bear evidence

- Corrected signal-to-exit interval audit: [Actions run 38040543637](https://github.com/eklu654/Trading-Bot/actions/runs/38040543637).
- Full-portfolio QQQ drawdown-warning counterfactual: [Actions run 38041217122](https://github.com/eklu654/Trading-Bot/actions/runs/38041217122).
- Reports: [slow-bear exposure audit](QQQ_SLOW_BEAR_EXPOSURE_AUDIT_2026-10-10.md) and [full B0 warning counterfactual](B0_QQQ_DRAWDOWN_WARNING_COUNTERFACTUAL_2026-10-10.md).

The corrected audit found that in 2022 QQQ first crossed -10% from its rolling 252-session high on 2022-04-05, but the baseline's daily shock exit did not occur until 2022-05-05. TQQQ's adjusted return from the threshold close through the exit open was -29.54%. This establishes a delayed-trigger exposure interval, not proof that an earlier exit would improve terminal wealth.

At 0 bp, B0 ended at $4,040,315 with -73.53% maximum drawdown. The best wealth-retaining simple warning candidate (DD15 / 75% cap) ended at $3,239,394 with -70.21% max drawdown: roughly $801k less ending wealth for 3.32 percentage points of drawdown improvement. DD10 variants sacrificed still more wealth. None should be promoted.

## Existing Fed research checked to prevent duplicate work

1. [Fed-vs-DMA ablation](CANONICAL_SHOCK_RECOVERY_FED_VS_DMA_ABLATION_RESULT_2026-10-09.md): the Fed condition materially improved selectivity versus DMA-only overlays in the observed sample, but its benefit was concentrated in the 2022 tightening bear. F50/F75 are not independently validated.
2. [Active-tightening overlay](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md): 50% overlay exposure improved max drawdown from -73.53% to -61.19% and worst rolling-year return from -72.64% to -59.88%, but ending wealth fell from about $4.040M to $3.675M in that run. The 2018–2019 trend-chop / recovery period is a major opportunity cost.
3. [Fed/200-DMA hybrid audit](B0_FED200_HYBRID_RESULTS_AUDIT_2026-10-09.md): on the actual-TQQQ sample, 75% retained 94.65% of B0 ending wealth and improved drawdown by 5.34 pp, but failed the preregistered synthetic max-drawdown gate; the 50% variant failed additional wealth gates.
4. [Existing macro overlay](CANONICAL_SHOCK_RECOVERY_MACRO_OVERLAY_RESULT_2026-10-09.md): reduced terminal wealth, did not improve whole-period max drawdown or worst rolling-year return, and failed to flag 2022 as macro deterioration.
5. [Validation protocol](CANONICAL_SHOCK_RECOVERY_VALIDATION_PROTOCOL_2026-10-09.md): retrospective segment analysis is stability diagnostics, not an untouched holdout; paper trading is not authorized by the protocol.

## Decision

- Keep B0 as the control.
- Do not promote a QQQ drawdown-warning threshold, the macro classifier, or the Fed/200-DMA overlay based on these results.
- Do not repeat already-run 50%/75% Fed-vs-DMA ablations or run another broad threshold sweep.
- Preserve the Fed hypothesis as a research candidate, but explicitly acknowledge that modern actual-TQQQ evidence has only one major post-2010 tightening-driven bear episode.

## Next work with highest information value

Before designing a new signal, use the already-generated event/equity ledgers to answer a narrow, decision-relevant question: **is the 2018–2019 opportunity cost of the frozen Fed/200-DMA candidate caused by one specific defense interval that overlaps a baseline recovery, and how much of the whole-period advantage disappears when that interval is removed?** The repo already has leave-one-overlay-episode-out diagnostics; inspect those outputs rather than inventing a new exit rule. If this attribution is already fully reported, the next useful step is a source/timing audit of the hand-maintained Fed state dates against the documented policy chronology—not parameter tuning.

Any new strategy modification after examining these same dates is development data and requires a newly frozen prospective test. No paper/live trading approval follows from this note.
