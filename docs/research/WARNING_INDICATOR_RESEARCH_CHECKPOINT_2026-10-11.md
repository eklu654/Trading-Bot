# Warning-Indicator Research Checkpoint — 2026-10-11

## Scope
Continue searching for a causal warning signal that helps the frozen B0 strategy avoid catastrophic drawdowns. This is a research checkpoint, not a strategy change.

## Frozen control
- B0 remains the QQQ daily shock/recovery rule: a QQQ daily close return <= -4.5% arms defense; re-entry occurs after QQQ closes at least 10% above the post-shock low.
- Starting equity: $5,000.
- Recorded actual-TQQQ-era benchmark: approximately $4.040M at 0 bp, maximum drawdown -73.53%; the exact result depends on the documented frozen input/window.
- Do not modify B0, tune its parameters, or promote a candidate during detector research.

## Evidence reviewed
1. `FAILED_BOUNCE_FEATURE_AUDIT_RESULTS_2026-10-09.md`: only nine actual-TQQQ-era canonical events, with seven successful labels, one failed, and one censored. The sole resolved failure is the July 2022 recovery. Long-DMA damage and negative intermediate returns also occurred at successful 2018–2019, COVID-2020, and April-2025 recoveries. This sample cannot validate a reliable veto.
2. `CANONICAL_STRUCTURAL_STATE_ABLATION_RESULTS_2026-10-09.md`: tested structural-state variants reduced maximum drawdown but materially damaged ending wealth and turned B0's positive COVID window negative. The less-sticky variants did not fix the failure.
3. `STRUCTURAL_MATRIX_COMBINED_INVESTIGATION_SUMMARY_2026-10-09.md`: the structural flag had only 60.9% precision and 47.1% specificity for a new low within 60 sessions in a selected in-sample event set. Recovery-gated and bounded-delay variants also failed to beat B0's wealth/drawdown trade-off.
4. `LONG_HISTORY_BEAR_RALLY_SIGNAL_AUDIT_RESULTS_2026-10-09.md`: on S&P 500 1970–2026, failed recoveries descriptively had more trend damage and weaker intermediate-horizon returns than successful recoveries, but there were only 16 resolved events. This is hypothesis-generating, not validation.
5. `100-dma-episode-attribution.md`: 100-DMA exits coincided with severe synthetic 3x-proxy losses during long 2000–2002 and 2008–2009 episodes, and exited ahead of the 2020 emergency Fed response; however, it also whipsawed during COVID. This is not actual TQQQ performance before inception.

## Current conclusion
The simple indicators tested so far show the familiar trade-off: defensive rules can reduce drawdown, but the tested overlays sacrificed too much compounding or blocked fast recoveries. The evidence does not justify claiming any one warning indicator is reliable enough to protect B0 from near-total loss. A long, grinding bear remains a key survivability scenario, but the test must include abrupt shocks and V-shaped recoveries too.

## Next bounded investigation
Before inventing another indicator, inspect and report the existing causal walk-forward bear-discriminator and crash/persistent-bear-filter experiments, including their actual-TQQQ results, chronological test splits, false-defense episodes, and any code/data leakage risks. Do not rerun broad parameter grids. If no existing result is adequately audited, specify one small predeclared test that distinguishes a prolonged structural bear from a fast rebound, while preserving a strictly causal close-to-next-open execution convention.

## Guardrails
- Research branch only; no merge to main.
- No B0 edits or benchmark replacement.
- No paper/live trading authorization.
- Clearly label synthetic 3x QQQ results as diagnostics, not historical TQQQ returns.


## Existing crash/persistent-bear filter result found after checkpoint
The checked-in `data/research/crash_persistent_bear_filter.csv` contains a completed 18-row modern actual-TQQQ matrix plus a synthetic diagnostic matrix. The actual-TQQQ rows report ending equity from about $1.13M to $3.27M, all below the recorded B0 ~$4.04M, with max drawdowns from about -62.7% to -80.6%. The strongest wealth row in this matrix is the -4.5% shock / 20-session positive-momentum / 50-DMA confirmation variant: about $3.274M, max DD -72.31%, versus B0 about $4.04M and -73.53%. It therefore sacrifices roughly $766k ending wealth for only about 1.2 percentage points of max-DD improvement; it is not a satisfactory detector.
- The 100-DMA confirmation variants are notably weaker in this table (about $1.70M–$1.85M ending wealth and roughly -78.5% max DD for the -4.5% shock rows).
- This filter is specifically a post-shock re-entry confirmation gate, not an independent early warning signal. It cannot protect against a long decline before a qualifying shock arms the defensive state.
- The code uses close-based conditions and rolls exposure forward one session, which is directionally consistent with next-session execution. However, the checked-in script directly downloads QQQ/TQQQ through yfinance and does not visibly freeze/hash the inputs in the script itself; its matrix is not directly comparable to B0 unless the exact dates, adjusted/close fields, and data snapshots are aligned. Treat the table as a negative screening result, not a final controlled comparison.


## 2026-10-11 follow-up: causal walk-forward code audit

### Confirmed from source
- `research/bear_discriminator_walkforward.py` implements a -4.5% QQQ daily close shock trigger, then tests 10% recovery versus slower 15/20/30/40% recovery targets when QQQ 60-session return is weak, with or without a below-100-DMA requirement.
- Declared folds: train 2010–2017 / test 2018–2021; train 2010–2021 / test 2022–2026.
- Exposure is rolled one session (`np.roll(invested, 1)`), so the intended convention is close signal -> next-session asset return.
- The structural override only exists while the shock-armed state is active. It is not an independent warning of a gradual bear that does not produce the qualifying daily shock.
- The related `bear_discriminator_modern.py` evaluates 25 rule variants and writes `data/research/bear_discriminator_modern.csv`. It downloads data live and reports full-window terminal equity/DD; no chronological held-out evaluation is evident in that script. It should not be described as walk-forward evidence.

### Results availability / reproducibility
- The exact walk-forward output CSV and its result report are absent from the checked-in branch tree at the paths expected by the script; therefore no defensible out-of-sample balance, DD, false-defense count, or fold-wise metric can be reported yet.
- Script downloads data live via yfinance, so a reproducible result needs frozen input files and hashes, exact symbols/fields/date windows, and a saved output artifact.
- Retrospective failed-bounce labels use up to 252 future sessions. They may be used as labels for model evaluation only, never as live features; split boundaries must purge observations whose label horizons cross into the test period.

### Cross-check against adjacent experiments
- The S&P 500 1970–2026 selected-event audit has 18 events (10 failed, 6 successful, 2 censored); it finds trend damage / weak intermediate momentum descriptively associated with failed recoveries, but only 16 resolved observations and no validated thresholds.
- The actual-TQQQ event audit has nine events (seven successful, one failed, one censored). Successful 2018–19, COVID-2020, and April-2025 recoveries contradict simple long-DMA or negative-momentum vetoes.
- Structural overlay ablation on aligned actual TQQQ reduced DD but ended at $727k–$1.355M versus B0 $4.040M and changed the COVID window from +24.58% to roughly -9% to -10%; those candidates remain rejected.

### Decision and next test
Do not claim the discriminator is validated and do not launch another parameter grid. The next useful experiment is a frozen-input, small predeclared evaluation of a *pre-shock* slow-bear warning separately from the post-shock failed-recovery classifier. The warning test must include every qualifying index decline, including those with no -4.5% daily shock, and score lead time, loss accumulated before signal, fraction of event loss avoided, false defenses, and missed fast crashes / V-shaped recoveries. Keep B0 unchanged as the control.


## 2026-10-11: QQQ rolling-decline warning candidate added

- Hypothesis: trigger when QQQ adjusted close is X% below its trailing Y-session maximum close. This can capture multi-day/gradual deterioration that never produces a single -4.5% daily shock.
- Pre-registered 20-cell screen: X = 5%, 7.5%, 10%, 12.5%, 15%; Y = 10, 20, 40, 60 sessions.
- Signal-only event audit added at `research/qqq_rolling_decline_warning_audit.py`; manual workflow at `.github/workflows/qqq-rolling-decline-warning-audit.yml`; protocol at `docs/research/QQQ_ROLLING_DECLINE_WARNING_HYPOTHESIS_2026-10-11.md`.
- Script freezes its retrieved QQQ adjusted-close CSV into the artifact set and records SHA-256, retrieval timestamp, source, coverage, 20% peak-to-trough event coverage, first warning date, sessions from peak to warning, drawdown at warning, warning episodes, and warning-day fraction.
- Important limitation: this is a signal-only screen. It does not yet simulate B0/TQQQ portfolio effects, re-entry, false-alarm cost, or opportunity cost. Those require a separate predeclared overlay test after inspecting event results. Do not choose a threshold from the full history and call it out-of-sample validation.
- No B0 changes; no candidate promoted. Benchmark remains frozen at about $4.04M / -73.53% max DD as the current recorded control.


### Rolling-decline audit execution note / correction
- First workflow run `38113063154` completed successfully and produced artifacts, but inspection found the original event segmenter merged the 2000–02 decline with later years until the old peak recovered, hiding the 2007–09 bear as a separate event. Its five-event detection-rate table is therefore invalid for comparing broad bear-event coverage and must not be used as a result.
- Fixed the event ledger in commit `62c772e6ddb3e2d73b5d95ed9e50866412083bfc`: events now begin when QQQ falls at least 20% below a trailing 252-session high and close after drawdown stays shallower than 10% for 20 consecutive sessions. This is an explicit operational event definition, not the only possible definition; inspect the resulting event dates before interpreting detection rates.
- Corrected workflow run `38113127827` was queued after the fix. Do not rely on the first run's event count or detection rates. After corrected run completes, inspect the event ledger, especially 2000–02, 2007–09, 2020, 2022, and 2025, before interpreting threshold trade-offs.


### Corrected rolling-decline screen: initial signal-only findings
- Corrected run `38113127827` completed successfully (artifact ID `11691854022`, created 2026-10-11). Event segmentation now separates six qualifying QQQ episodes, including 2000–02 and 2007–09, plus 2018, COVID-2020, 2022, and 2025.
- In this six-event screen, X=10% within Y=10 sessions warned before the trough in 6/6 events, produced 77 distinct warning episodes, and marked 3.08% of sessions as warning days. X=7.5%/10 sessions also warned before all six but marked 6.67% of sessions; X=5%/10 sessions marked 14.01%. X=15%/10 sessions only warned before 3/6 events. Longer Y windows increased time in warning state.
- Event-level examples for X=10%/Y=10: warning on 2000-04-03 (5 sessions after the event peak; QQQ already down 12.58% from the peak), 2007-11-08 (6 sessions; down 6.00%), 2018-12-21 (79 sessions; down 20.83%, almost at the trough), 2020-02-27 (6 sessions; down 13.22%), 2022-01-25 (20 sessions; down 14.47%), 2025-04-04 (32 sessions; down 21.54%, very late). Thus the same threshold can be fast in some events and uselessly late in others.
- These six selected events are not a complete independent benchmark, and 6/6 detection is not a reliable hit-rate estimate. The rule is inherently a drawdown detector; it necessarily triggers once the decline reaches X, so the key question is whether it triggers early enough and whether defensive action improves actual TQQQ portfolio outcomes.
- First run `38113063154` had an event-ledger bug that merged the 2000 bear through its eventual old-peak recovery and omitted 2007–09 as a separate episode. Do not use that first artifact. The corrected run fixes segmentation; script metadata was subsequently corrected to match the actual 252-session/20%-start/10%-recovery-for-20-sessions event definition.
- Next step: after metadata-correction workflow completes, confirm the output matches the corrected run, then build a separate frozen-control portfolio simulation with explicit causal defense/re-entry logic and chronological holdout. Do not optimize further based on this six-event screen alone.


## Follow-up 2026-10-11: workflow verified; connect signal screen to existing B0 counterfactual

### Run and artifact verification
- Metadata-correction workflow `38113172397` completed successfully; all steps, including upload, passed. Artifact ID `11692303519`; artifact SHA-256 `670affaea81793171ce58272643a1b3229cceeeb49e2f101f4f6bf4635ddaac9`.
- Frozen screen input: 6,939 QQQ adjusted-close rows, 1999-03-10 through 2026-10-08; SHA-256 `69820e00b10c43548871c864877a10b8e8544625a4c0cd7c826538a23bfa4b3d`.
- The six event windows are 2000–02, 2007–09, 2018, COVID-2020, 2022, and 2025 under the operational rule (20% below trailing 252-session high to start; 20 sessions continuously shallower than 10% drawdown to close). This is a small event set, not a broad enough sample to validate 100% detection claims.

### Signal-screen interpretation
- The 10%-within-10-sessions rule flags all six event troughs before they occur, but it is too late to count as meaningful protection in 2018 and 2025: first signal is 79 and 32 sessions after the event peak, with QQQ already down 20.83% and 21.54%, respectively.
- It is faster in 2000, 2007, 2020, and 2022 (5, 8, 6, and 20 sessions after the recorded event peak; drawdown at warning -12.58%, -11.45%, -13.22%, and -14.47%).
- The apparent fraction of peak-to-trough loss "avoided" is a price-path diagnostic only, assuming exit at the warning close. Actual next-open execution, leveraged daily path, B0's existing signal, and re-entry all alter realized portfolio results. Do not treat this metric as simulated TQQQ savings.
- The report text still contains an older generic event-definition sentence ("non-overlapping peak-to-recovery episodes...") even though metadata and code now state the rolling-252 / 20%-start / 10%-for-20-sessions rule. Correct report-generation wording before relying on generated report text; CSV + metadata have the operational definition.

### Critical existing result discovered: the portfolio counterfactual already exists
- Do not create a duplicate B0 overlay experiment. Existing script `research/qqq_drawdown_warning_b0_counterfactual.py` already tested 252-session high drawdown warning with next-open execution, hysteresis, exposure caps, costs, and the canonical B0 baseline.
- Its report `docs/research/B0_QQQ_DRAWDOWN_WARNING_COUNTERFACTUAL_2026-10-10.md` records B0 at $4,040,315 / -73.53% max DD. DD15 with 75% warning exposure finished $3,239,394 (-19.8% vs B0) and improved max DD by only 3.32 percentage points. DD10 with 75% finished $1,834,217 (-54.6%) despite a 8.74pp max-DD improvement; DD10/0% finished $100,639. All candidates were rejected.
- That prior overlay uses 252-session peak thresholds (-10%/-15%) and re-entry at -5%/-10%; it is not the same as the new X%-within-10/20-session family. Nevertheless, it demonstrates the central tradeoff: a long-lived drawdown warning can preserve some capital but block powerful recoveries and destroy terminal wealth.
- Next step should be to audit the exact short-window X/Y signal and test whether a *bounded/temporary* exposure reduction improves tail risk while promptly restoring exposure, rather than simply repeating long-lived hysteresis. First correct report wording, then predeclare only a few candidates (e.g. 7.5%/10 sessions and 10%/10 sessions) and one re-entry rule. Compare against frozen B0 on the same canonical frozen input and costs; no threshold selection from the same holdout.
