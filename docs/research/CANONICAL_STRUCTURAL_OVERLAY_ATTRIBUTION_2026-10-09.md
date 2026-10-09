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


## Results and interpretation

- Corrected successful run: [workflow 37913116036](https://github.com/eklu654/Trading-Bot/actions/runs/37913116036); artifact ID `11606389641`; artifact SHA-256 `1f78aae47b60f8a4983208b6dd845cfb3058299ac3844797096dd205952480a7`.
- The first run's attribution label used execution dates when determining the prior recovery. The code was corrected to compare signal-close dates; the corrected run is the source of truth for interval labels. Wealth numbers are essentially unchanged.
- B0 returned to 100% on its recovery decision close; the overlay was already defensive on that same close, so the next-open B0 re-entry was blocked. Most important examples:
  - **2019-01-07 to 2019-02-14**, the B0 recovery-decision close at the start of the interval: conditional terminal contribution of overlay interval was about -$158k (sticky), -$140k (hard-nonsticky), and -$213k (daily-nonsticky).
  - **2020-03-26 onward**, the B0 recovery-decision close at the start of the COVID interval: conditional contribution about -$230k (sticky), -$299k (hard-nonsticky), and -$454k (daily-nonsticky). These are leave-one-interval-out differences, not additive.
  - **2022-07-19**, another B0 recovery decision, also starts a defensive overlay interval and has conditional cost around -$220k / -$231k / -$351k for sticky / hard-nonsticky / daily-nonsticky.
  - The overlay also helps in other 2022 intervals (e.g. 2022-03-30 to 2022-05-04, conditional contribution about +$258k / +$280k / +$426k respectively), showing the trade-off is highly path-dependent.
- Interpretation: the structural matrix's biggest failure is not simply remaining defensive after B0 recovery. It is **blocking B0's re-entry exactly on the recovery decision close**, including the sharp COVID rebound. Yet the same signal helps during some 2022 stretches. A useful future candidate must distinguish these contexts; merely changing sticky state does not do so.
- Do not sum interval contributions: they are conditional leave-one-out counterfactuals under compounding and are explicitly non-additive.
