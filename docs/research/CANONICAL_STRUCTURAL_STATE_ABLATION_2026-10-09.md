# Canonical structural state ablation — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; awaiting Actions result.**

## Why
The previous combined matrix run rejected its overlay family because it severely reduced actual-TQQQ terminal wealth and missed the COVID rebound. A concrete implementation detail is that a fast-shock trigger can hold exposure at 0% until the structural DMA is reclaimed, even after the fast-shock condition itself ends. This experiment isolates state persistence rather than retuning thresholds.

## Frozen parameters
Representative setting held fixed from the prior grid's highest-ending-balance structural+fast row:
- Structural DMA 150; fast DMA 100.
- 63-session return threshold -20%; 252-session drawdown threshold -20%; VIX threshold 30.
- Structural exposure 25%.
These parameters are reused only to compare state-machine behavior. Because they were selected after inspecting the same modern sample, this is a diagnostic ablation, not independent validation or a new winner search.

## Variants
- B0: canonical QQQ -4.5% daily shock / +10% from post-shock low recovery.
- `sticky_original`: previous matrix logic, with the 0% hard-shock state sticky until close >= structural DMA.
- `hard_nonsticky`: structural defensive state remains sticky until close >= structural DMA, but 0% exposure applies only while today's fast-shock condition is true; afterward the overlay returns to 25% exposure while structurally armed.
- `daily_nonsticky`: no state carry; today's structural conjunction yields 25%, today's fast-shock condition yields 0%, otherwise 100%.
- Every candidate target is `min(B0, overlay)`; overlays cannot increase B0 exposure or cancel B0 defense.

## Evaluation
Same $5,000 initial balance, close-to-next-open execution convention, actual TQQQ aligned frozen sample, and separately labeled hypothetical 3x QQQ proxy from 1999. Report final balance, CAGR, maximum drawdown, worst rolling 252-session return, exposure and transition counts, and dot-com/GFC/COVID/2022 diagnostics. Synthetic results are not actual TQQQ returns.

## Audit trail
- Code: `research/canonical_structural_state_ablation.py`
- Workflow: `.github/workflows/canonical-structural-state-ablation.yml`
- Code commit: `aac440d1246dbf3f67cd7aaacd9daf4ce8b8cc50`
- Workflow commit: `202ee55a43e905447d12d7b3a6135bbbbfcf4ea9`
- Results will be appended here after the workflow completes. Do not treat the ablation as deployment evidence.
