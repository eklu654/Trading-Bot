# Structural overlay episode attribution — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; Actions result pending.**

## Purpose
Quantify when the fixed representative structural overlay reduces TQQQ exposure after the canonical B0 rule has returned to 100%, and which contiguous overlay intervals account for the terminal-wealth difference. This is attribution only; it does not search or optimize parameters.

## Fixed rule
- B0: canonical QQQ adjusted-close daily shock <= -4.5%, defensive until 10% rebound from running post-shock low.
- Overlay parameters: structural DMA 150, fast DMA 100, 63-session return -20%, 252-session drawdown -20%, VIX 30, structural exposure 25%.
- State variants: original sticky hard defense; non-sticky hard override with sticky structural defense; fully daily/non-sticky.
- Actual TQQQ aligned frozen sample; $5,000; close-to-next-open execution.
- Episode is a contiguous interval where overlay target < 100% while B0 itself targets 100%. For each interval, remove only that interval's overlay restriction and recompute terminal wealth. Contributions are conditional, non-additive because compounding interacts.

## Output
- Interval start/end, duration, mean/min overlay exposure, whether interval intersects COVID/2022/2018–19, most recent B0 recovery decision before interval, candidate ending balance, counterfactual ending balance, conditional difference.
- This identifies opportunity-cost episodes without choosing new thresholds.

## Audit
- Code: `research/canonical_structural_overlay_attribution.py`
- Workflow: `.github/workflows/canonical-structural-overlay-attribution.yml`
- Code commits: `93a1f7965a989adb85cfcfb206500ddeb5918b02`, follow-up correction `9b223700c1f67e24f70c56a76acfdb9834b30d9d`
- Workflow commit: `1bfef275bf4a368986731016e19a135f746f7e4f`
- Append run status, artifact metadata, and interpretation here when the job finishes.
