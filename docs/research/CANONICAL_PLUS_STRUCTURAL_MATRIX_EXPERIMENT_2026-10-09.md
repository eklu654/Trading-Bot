# Canonical shock/recovery + structural matrix experiment

Date: 2026-10-09  
Status at commit: **IMPLEMENTED; GitHub Actions run queued; no performance result claimed yet.**

## Question
Does the prior structural/fast-shock matrix add value when used as a strictly defensive overlay on the canonical QQQ shock/recovery strategy, rather than tested alone?

## Frozen control and combination rule
- B0: QQQ adjusted-close daily return <= -4.5% arms a defensive event; remain at 0% TQQQ until QQQ closes at least 10% above the running low since the shock; otherwise 100% TQQQ.
- Initial balance $5,000.
- Actual TQQQ analysis uses the same QQQ/TQQQ aligned frozen input produced by `tqqq_canonical_same_input_reconciliation.make_frozen_input()`.
- Signal at close[t] executes at open[t+1]; prior exposure earns overnight, new exposure earns intraday.
- Combined signal is `min(B0_signal, overlay_signal)`. An overlay cannot increase exposure or undo B0's recovery state.
- Parameter grid: structural DMA 100/150/200; fast DMA 50/100; 63-session return threshold -15%/-20%; 252-session drawdown threshold -20%/-25%; VIX threshold 28/30; structural exposure 25%/50%/75%.
- Two ablations per parameter set: (1) structural + fast-shock matrix, (2) fast-shock-only. B0 is included as a control.

## Sources / interpretation
- Actual-TQQQ results cover the aligned live-fund sample only.
- The 1999-onward extension is a hypothetical daily-reset 3x QQQ proxy using the prior matrix study's approximation. It is not realized TQQQ history, and is not fully calibrated for fund financing, fees, tracking, and distributions. Use it for signal-regime diagnostics only, not as evidence of actual historical TQQQ account returns.
- The grid is exploratory and in-sample; the best row is subject to selection bias. No winner is selected for deployment from this run alone.
- The fast-shock override is sticky until QQQ closes at/above the selected structural DMA, matching the previous matrix state logic. This can keep a 0% override active beyond the shock itself; results should be read with that exact behavior in mind.

## Output contract
Workflow should upload:
- `canonical_plus_structural_matrix_results.csv`
- `canonical_plus_structural_matrix_manifest.json`
- `tqqq_canonical_frozen_common_input.csv`

Summary metrics include final balance, CAGR, maximum drawdown, worst rolling 252-session return, average target exposure, exposure changes, and stress-window returns/drawdowns for dot-com, GFC, COVID, and 2022.

## Audit trail
- Experiment code: `research/canonical_plus_structural_matrix.py`
- Workflow: `.github/workflows/canonical-plus-structural-matrix.yml`
- Code commit adding script: `40e0c9b60390614d98b5e3906439eb9ae636f75d`
- Workflow commit: `b83b6c9c88c7b4349e229cff15fa4dd9fe3dbd30`
- Triggered run: https://github.com/eklu654/Trading-Bot/actions/runs/37912413316
- This report records implementation and the pending run only. Add the run conclusion, artifact ID/hash, data endpoints, actual result tables, and any code defects here after inspecting the completed artifact.
