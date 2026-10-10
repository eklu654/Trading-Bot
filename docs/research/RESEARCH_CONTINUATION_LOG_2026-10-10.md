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

## Fed source reconciliation and timing sensitivity follow-through

- Reconciled all 78 hand-maintained Fed events against FRED daily target rates. All 78 listed new rates appear on/after their listed event dates and within seven calendar days. Flags: one missing prior-rate annotation for 1999-06-30; FRED records the new target one day before the effective-date rows for the 2015-12-17 and 2016-12-15 hikes.
- Official FOMC statements and implementation notes confirm announcement/effective-date distinctions for those two hikes. The hand-maintained event table is not auto-corrected; the timestamp convention is documented in [Fed event-table/FRED reconciliation result](FED_EVENT_TABLE_FRED_RECONCILIATION_RESULT_2026-10-10.md).
- Ran a full-input one-session timing sensitivity on the existing Fed-paused/200-DMA overlay: [Actions run 38043580560](https://github.com/eklu654/Trading-Bot/actions/runs/38043580560). Same 4,189 sessions, 2010-02-11–2026-10-07, same classifier, baseline, DMA, execution, and costs; only the Fed-state market-calendar lag changed.
- Fed state labels differed on 21 sessions, but actual candidate exposure differed on only 2016-03-15. Ending balances: B0 $4.040M; one-session-lag overlay $2.909M; same-session diagnostic $2.833M (0 bp). All had the same -73.53% max drawdown at 0 bp. At 10 and 25 bp, lagged mapping remained ahead of same-session mapping, but both overlay variants remained well below B0.
- This broad lag sensitivity is not a targeted portfolio counterfactual for only the 2015/2016 hikes. Those two date flags did not themselves create an overlay-signal disagreement in this run. Do not replace the conservative one-session lag.
- Report: [Fed-state timing sensitivity result](FED_STATE_TIMING_SENSITIVITY_RESULT_2026-10-10.md). Artifacts: [reconciliation run 38042891664](https://github.com/eklu654/Trading-Bot/actions/runs/38042891664) and [timing run 38043580560](https://github.com/eklu654/Trading-Bot/actions/runs/38043580560).
- Decision: retain B0, retain the existing one-session Fed lag, and do not optimize the paused-Fed/200-DMA candidate. Its drawdown did not improve in this test and its terminal-wealth penalty was about 28% at zero costs.

## Targeted 2015/2016 announcement-versus-effective-date check

- Workflow [run 38089561632](https://github.com/eklu654/Trading-Bot/actions/runs/38089561632) completed successfully; artifact [11683576764](https://github.com/eklu654/Trading-Bot/actions/runs/38089561632/artifacts/11683576764).
- Changed only the FRED announcement-date target observations for 2015-12-16 (0.375% -> prior 0.125%) and 2016-12-14 (0.625% -> prior 0.375%), leaving the documented effective-date observations intact.
- Compared 4,216 QQQ sessions from 2010-01-04 through 2026-10-07. Fed-state labels changed on four dates (2015-12-17, 2016-03-16, 2016-12-15, 2017-03-15), but the sticky Fed-paused/200-DMA overlay exposure changed on **zero** sessions.
- Because no candidate position changes, no portfolio backtest was run. This is a signal-level result, not a return estimate.
- Classifier, one-session lag, and overlay state machine were checked against `research/canonical_shock_recovery_fed_dma_overlay.py`. Diagnostic classifies the full FRED history before mapping, unlike the portfolio script's start-date clipping; this boundary difference does not affect the 2015/2016 comparison dates.
- Report: [targeted Fed effective-date signal diagnostic](FED_2015_2016_EFFECTIVE_DATE_SIGNAL_DIAGNOSTIC_2026-10-10.md).
- Decision unchanged: keep B0 as the control, retain the conservative one-session lag and current Fed source convention, do not promote the Fed/200-DMA overlay, and do not authorize paper/live trading.

## Actual-TQQQ partial-DMA matrix audit

- Inspected completed workflow [run 38089556724](https://github.com/eklu654/Trading-Bot/actions/runs/38089556724), artifact [11682898823](https://github.com/eklu654/Trading-Bot/actions/runs/38089556724/artifacts/11682898823). Manifest status PASS; frozen input SHA-256 `8b2b45074b9608ecd08ee2bb2242d4f8ebd61480ac2bf00c653cf2d29c1bd35d`; 4,186 rows; common evaluation 2011-02-07–2026-10-02; $5,000 reset after 250-session warmup.
- Tested 100/125/150/175/200/250-session DMAs and 100/75/50/25/0% exposure below DMA at 0/10/25/50 bp, combining DMA exposure with B0 by taking the minimum exposure. Close signals execute at next open.
- Best wealth-retaining reduced-exposure candidate at 25 bp was 150-DMA/75% below: $1.374M vs B0 $1.732M (79.3% retained), max DD -66.16% vs -73.80% (7.64 pp improvement). A more defensive 175-DMA/25% candidate reached -48.11% max DD but ended at only $658k (38.0% of B0).
- No partial-DMA candidate meets the existing >=95% of B0 terminal-wealth gate at 25 bp. Decision: reject this simple overlay family; do not tune further parameters on this same matrix.
- Report: [actual-TQQQ partial-DMA matrix audit](ACTUAL_TQQQ_PARTIAL_DMA_MATRIX_AUDIT_2026-10-10.md). This is retrospective, not an untouched holdout. B0 remains the working control; no paper/live trading is authorized.
