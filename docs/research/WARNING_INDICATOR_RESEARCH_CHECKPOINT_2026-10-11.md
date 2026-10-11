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
