# Next Diagnostic — Is the Active-Fed Filter Adding Value Beyond the 200-DMA?

**Date:** 2026-10-09 UTC  
**Status:** PRE-DECLARED RETROSPECTIVE ABLATION; not a candidate-selection or holdout test  
**Motivation:** F50/F75 clear the numerical cost/downside gates but fail the episode-diversification gate because their apparent net advantage is concentrated in the 2022 active-tightening episode. Before inventing a new signal, isolate whether the Fed condition adds value beyond the same existing 200-DMA structural rule.

## Question

Does requiring the lagged Fed state to be TIGHTENING_ACTIVE improve the results of a 200-DMA partial-exposure overlay, or does the overlay's apparent effect mostly come from the 200-DMA state itself?

## Frozen comparisons

Keep B0 unchanged and compare only:
- F50/F75: existing Fed-active + below-200-DMA sticky overlay, with 50%/75% TQQQ target exposure; B0 shock defense overrides to 0%.
- D50/D75: same 200-DMA sticky overlay and same 50%/75% exposure, but no Fed-state entry requirement. Enter defensive when QQQ adjusted close is below its existing 200-session SMA; exit when QQQ closes at/above the SMA. B0 shock defense overrides to 0%.
- TQQQ buy-and-hold remains a reference only.

Do not test new DMA lengths, exposure levels, shock thresholds, recovery thresholds, or new indicators. No parameter optimization. This is an ablation of one condition, not a broad search.

## Execution and data controls

- Use one aligned frozen QQQ/TQQQ market CSV for all five candidate families.
- Use the existing lagged Fed-state input for F50/F75 only; D50/D75 must not consult Fed state.
- Close[t] signal executes at open[t+1]. Overnight/intraday accounting remains identical across candidates.
- Record exact market and Fed-state hashes, code commit, workflow URL, row count and dates.
- Independently reconcile B0 returns with the existing execution loop.
- Include full equity/exposure timelines, period scorecard, 0/10/25/50 bp exposure-change cost sensitivities, and leave-one-overlay-episode-out diagnostics for both Fed-gated and DMA-only overlays.
- Keep the episode counterfactual interpretation cautious: episode effects are non-additive and do not prove causal attribution.

## What this can and cannot establish

This full modern sample has already been inspected and cannot be treated as an untouched holdout. The ablation can reveal whether the Fed condition is adding measurable value, whether DMA-only exposure catches slow corrections earlier, and whether the false-positive cost changes. It cannot establish future generalization or authorize paper/live trading.

A result where D50/D75 perform better does not automatically select DMA-only. A result where F50/F75 perform better does not repair their single-episode concentration issue. Candidate selection remains frozen until this ablation is documented and the broader decision is revisited.

## Deliverable

One reproducible workflow/artifact set comparing B0, F50, F75, D50, and D75 on identical frozen data. Record all results, including negative results, in a dated report and update `CURRENT_STATE.md`.
