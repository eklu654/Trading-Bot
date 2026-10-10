# Frozen Fed Chronological Validation — Code Audit

**Date:** 2026-10-10  
**Status:** AUDIT FINDINGS — DO NOT INTERPRET AS TRADING VALIDATION  
**Branch:** `research/qqq-slow-bear-audit`  
**Audited script:** `research/fed_chronological_frozen_validation.py`  
**Protocol reference:** `docs/research/CANONICAL_SHOCK_RECOVERY_VALIDATION_PROTOCOL_2026-10-09.md`

## Decision summary

The current script is a post-hoc episode diagnostic, not a causal trading-rule test. Its own docstring says it is diagnostic only, but the printed “FROZEN RULE” / “warning” labels can be misread as a signal. Do not promote the rule or use its grouped forward returns as evidence that a real-time defense would work.

## Material findings

1. **Future-known duration is part of the warning rule.** `prolonged = (i-si)>DUR` is calculated only when the +10% recovery has already occurred, and `warning_rule = aggressive and prolonged` uses that outcome-known duration. A strategy cannot know at the shock date whether recovery will take more than 30 sessions. At best, this is a retrospective label for event classification, not an executable signal.
2. **Fed condition is also measured at recovery, not at a decision timestamp.** `fed_63d_bp` compares the target at recovery with the target 63 calendar days earlier. The warning is therefore assembled after the episode has recovered. The separate `candidate_persistent_tightening` explicitly compares recovery-time rates to the shock-time rate. These are outcome diagnostics, not evidence of an early exit rule.
3. **Unrecovered final episode is silently dropped.** `ledger()` appends an event only after the +10% recovery condition becomes true. If the final shock episode never recovers before the data ends, it remains armed and is omitted from the event ledger. That creates right-censoring / survivorship risk if the output is read as a census of all shocks. A censored episode must be emitted explicitly and excluded only from metrics that require a completed recovery.
4. **Forward-horizon endpoints are not consistently censored.** The script takes whatever observations remain in `px.loc[d:].iloc[:n+1]` and calculates a return whenever there is at least one later observation. Near the data end, a purported 120- or 252-session return can therefore be based on a shorter horizon and then enter summary statistics alongside full-horizon returns. Require a complete horizon or mark it censored/NaN.
5. **Shock/event handling is one event at a time.** A shock arms the ledger until +10% from the running low, then resets. This creates non-overlapping recovery episodes by construction; it does not count every shock day or every independent signal. Reports must define the unit as “shock-to-recovery episode,” and overlapping forward-return windows must not be summed as if independent.
6. **Data/provenance limitations.** The workflow fetches current vendor data at run time and does not freeze/hash inputs in the script. The workflow is configured for push/path or manual dispatch. A check of the current recent Actions run listing found no run for this workflow, so no output artifact/result is claimed here.

## What remains useful

- The script can serve as an exploratory retrospective table of completed shock-to-recovery episodes after fixing the censoring and horizon labels.
- The frozen thresholds (Fed target increase >=50 bp over 63 calendar days; recovery duration >30 trading sessions) should not be changed merely to improve results.
- These event labels may help characterize prolonged episodes, but they must not be fed back into position construction.

## Required correction before interpreting any run

1. Emit explicit right-censored events when an episode remains armed at the final observation.
2. Mark 60/120/252-session forward returns only when the full horizon exists; otherwise use NaN and report censored counts.
3. Rename fields/output labels to make clear that `warning_rule` is a **retrospective episode label**, not a live signal.
4. If a tradable candidate is later studied, define a separate causal decision-time rule using only values available then; run it as an actual-TQQQ portfolio backtest under the existing protocol, with next-open execution and frozen inputs.
5. Record data hashes, date coverage, and dependency versions. Do not describe any result as untouched out-of-sample evidence.

## Conclusion

**No strategy rule was changed and no backtest was run in this audit.** The code-level finding is enough to block promotion: the current “warning rule” uses future-known recovery duration and recovery-time Fed state, omits unrecovered terminal episodes, and may mix incomplete forward horizons. Correct those reporting/measurement defects before interpreting its event summaries. Keep B0 as the working control; no paper or live trading is authorized.
