# Results — canonical structural state ablation

Date: 2026-10-09  
**Workflow passed. No state variant is acceptable as a production candidate.**

## Reproducibility
- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37912719777
- Job `ablation`: success; compile, run, and artifact upload passed.
- Artifact ID `11606304467`; SHA-256 `0bf75ad8bf27a72d004b0700cd298cecf49b274de65d907f746c28f30de4ee12`.
- Actual aligned TQQQ dates: 2010-02-11 through 2026-10-07, 4,189 observations; nine B0 events; $5,000 initial equity.
- Synthetic diagnostic: 6,938 QQQ/VIX observations from 1999-03-10 through 2026-10-07. Hypothetical 3x proxy only.
- Fixed settings: structural DMA 150, fast DMA 100, 63-session return -20%, 252-session drawdown -20%, VIX 30, structural exposure 25%.

## Actual TQQQ comparison

| Rule | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return | COVID window return | 2022 window return |
|---|---:|---:|---:|---:|---:|---:|
| B0 canonical | $4,040,317 | 49.49% | -73.53% | -72.64% | +24.58% | -69.83% |
| Original sticky hard defense | $727,051 | 34.86% | -59.47% | -53.43% | -8.63% | -51.45% |
| Hard override non-sticky; structural state sticky | $891,652 | 36.52% | -57.81% | -55.80% | -9.92% | -53.93% |
| Fully daily/non-sticky overlay | $1,355,428 | 40.00% | -60.49% | -58.61% | -9.92% | -56.86% |

All overlay variants use `min(B0, overlay)`, so none increases exposure or cancels B0 defense. The daily/non-sticky variant recovers some ending wealth versus the sticky variant, but still ends about 66.5% below B0. Every variant flips the COVID crash/rebound window from B0's +24.58% to a loss near 9–10%. The less-sticky variants still improve max drawdown by about 13–16 percentage points but fail the main objective of preserving the rebound and compounding.

## Synthetic 3x QQQ diagnostic

| Rule | Ending balance | CAGR | Max drawdown | Dot-com window return | GFC window return | COVID window return | 2022 window return |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 canonical | $836,042 | 20.40% | -99.37% | -98.17% | -53.50% | +26.34% | -68.81% |
| Original sticky hard defense | $681,890 | 19.51% | -95.42% | -89.39% | -19.41% | -8.60% | -51.30% |
| Hard override non-sticky | $986,439 | 21.12% | -94.68% | -85.89% | -18.35% | -10.03% | -53.52% |
| Fully daily/non-sticky | $1,338,170 | 22.47% | -94.68% | -85.89% | -27.45% | -10.03% | -56.28% |

This proxy is not calibrated to reproduce actual TQQQ fund financing, fees, tracking, or distributions. The near-total-loss B0 drawdown underscores why its wealth results cannot be presented as historical TQQQ performance. Treat only as signal-regime diagnostics.

## Decision
- The simple explanation “sticky hard defense alone caused the poor result” is incomplete. Removing hard-state stickiness improves ending wealth, but the overlay still severely impairs actual TQQQ compounding and still misses COVID's rebound.
- Stop parameter tuning of this structural matrix. The broader feature family is not supported for production.
- Next step should be attribution, not another grid: export the dates and duration of structural-defense intervals after each B0 recovery decision, especially COVID 2020 and 2022, and quantify which overlay intervals account for the wealth reduction. Then only consider a narrowly scoped, recovery-aware rule if it targets the false-recovery problem without blocking confirmed V-shaped recoveries.
