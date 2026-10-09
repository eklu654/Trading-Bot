# Canonical Shock/Recovery + Existing Macro-Regime Overlay — Actual TQQQ Test

**Date:** 2026-10-09 UTC  
**Classification:** **REJECTED FOR THIS BASELINE / SLOW-BEAR OBJECTIVE**  
**Workflow:** [run 37886806226](https://github.com/eklu654/Trading-Bot/actions/runs/37886806226)  
**Artifact:** `canonical-shock-recovery-macro-overlay`, ID 11597160393  
**Market + mapped-state SHA-256:** `a363c49cdda884bb6062978b3d92398195171dc6f51a5fcf6f2f2a14ef367732`.

## What was tested

This was an actual-TQQQ comparison, not the older synthetic leveraged-QQQ study. The control is the unchanged `qqq_shock45_recovery10_actual_tqqq_v1` baseline. The candidates add the existing frozen macro classifier from `research/test_tqqq_macro_regime.py`, using its four dimensions and persistence/hysteresis:
- labor stress from unemployment;
- activity stress from industrial production;
- credit stress from Baa spreads;
- curve stress from the 10Y–3M spread.

The existing classifier's three exposure policies were retained:
- **Light:** 100% in structural expansion, 75% in deterioration, 25% in crisis.
- **Medium:** 100% in expansion, 50% in deterioration, 0% in crisis.
- **Hard:** 100% in expansion, 25% in deterioration, 0% in crisis.

Availability caution: the original classifier labels a full month's last observation with the month start and then applies a one-month offset. To avoid making that observation usable at the start of the immediately following month, this test adds one more month-start lag before mapping state to the trading calendar. That is intentionally conservative; exact release-date/vintage reconstruction is still required before any macro state could be called production-ready.

## Whole-period actual-TQQQ result

| Strategy | Ending balance from $5,000 | CAGR | Max drawdown | Worst rolling 252-session return |
|---|---:|---:|---:|---:|
| Baseline shock/recovery | $4,040,315 | 49.49% | -73.53% | -72.64% |
| Macro light | $3,308,216 | 47.70% | -73.53% | -72.64% |
| Macro medium | $2,706,346 | 45.93% | -73.53% | -72.64% |
| Macro hard | $2,179,761 | 44.05% | -73.53% | -72.64% |
| TQQQ buy-and-hold | $2,094,669 | 43.70% | -81.66% | -81.04% |

None of the three macro variants reduced the whole-period maximum drawdown or the worst rolling-year return relative to the baseline. All three reduced ending wealth, with stronger defense producing a larger wealth penalty. The hard variant finished only slightly above TQQQ buy-and-hold.

## The central slow-bear failure

The mapped macro-state timeline was:
- 2019-08-01: MACRO_DETERIORATION
- 2019-12-02: STRUCTURAL_EXPANSION
- 2020-05-01: MACRO_DETERIORATION
- 2020-07-01: MACRO_CRISIS
- 2020-08-03: MACRO_DETERIORATION
- 2021-02-01: STRUCTURAL_EXPANSION
- 2024-03-01: MACRO_DETERIORATION
- 2025-05-01: STRUCTURAL_EXPANSION

**It never entered MACRO_DETERIORATION or MACRO_CRISIS during the 2022 tightening-driven bear.** Both 2022 baseline shock dates (May 5 and September 13) were classified STRUCTURAL_EXPANSION. The strategy therefore remained governed by the shock/recovery rule during the very episode this macro overlay was intended to help detect.

The state did activate during 2020, but only after the initial COVID shock. That reduced exposure during the rebound: from February 19 through July 31, the baseline account rose 24.58%, while macro-light rose only 8.93%, macro-medium fell 2.17%, and macro-hard fell 10.42%. The local maximum drawdown was still the same for those strategies in that window.

The macro state helped the 2025 correction window, but it did so after the large 2022 drawdown had already set the whole-period maximum drawdown. Its whole-period drawdown metric therefore did not improve.

## Decision

**Reject the existing macro-only overlay family as a solution to the canonical baseline's slow-bear weakness.** It adds substantial defensive duration and opportunity cost without reducing the measured whole-period maximum drawdown or worst rolling-year return, and it failed to identify 2022 as deterioration.

This is not proof that macro information is useless. It says the existing four-indicator classifier, with a conservative availability lag, is not sufficiently responsive to the 2022 tightening regime to justify overlaying it on the current baseline.

Do not combine it with the Fed overlay just to add complexity: the macro layer did not flag the target bear, so a composite cannot rely on it to add early 2022 warning under this definition. Any revised macro classifier would be a new hypothesis requiring separate development and release-date validation.

## Research direction after this test

Keep the compact actual-TQQQ comparison set:
1. Unchanged shock/recovery baseline.
2. Fed-active × below-200-DMA overlay at 50% exposure.
3. The same overlay at 75% exposure.

The 50% variant gives more drawdown protection; the 75% variant preserves more wealth. Both ended above the baseline in the inspected sample, but this remains in-sample development evidence. The next task is not another indicator sweep: it is to freeze the comparison, document the 2018 recovery opportunity cost, and establish a chronological validation plan. Pre-2010 studies remain signal-only or explicitly synthetic, never actual-TQQQ returns.

## Reproducibility

- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37886806226
- Script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_macro_overlay.py
- Workflow definition: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-macro-overlay.yml
- Existing frozen macro classifier: https://github.com/eklu654/Trading-Bot/blob/main/research/test_tqqq_macro_regime.py
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
