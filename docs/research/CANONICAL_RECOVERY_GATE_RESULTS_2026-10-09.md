# Recovery-gated structural confirmation — results

Date: 2026-10-09  
Status: **REJECTED as currently specified; diagnostic findings retained.**

## Reproducibility
- Workflow: [run 37913598899](https://github.com/eklu654/Trading-Bot/actions/runs/37913598899), job `gate` passed, all output files uploaded.
- Artifact ID: `11607946132`; artifact digest: `sha256:0e9e84b2492c26692a3c0f7194e8ae0cdb8d71f41f5bca5448e945de942d916a`.
- Manifest status PASS. Actual-TQQQ common input: 4,189 aligned rows, 2010-02-11 through 2026-10-07, SHA-256 `1b4993c21e5dd211a71d0bda23934e07ade383d00eeb17f24645f9c03f8095b1`. Synthetic QQQ proxy: 6,938 rows, 1999-03-10 through 2026-10-07.
- Starting capital: $5,000. Canonical B0: QQQ adjusted-close daily return <= -4.5%; remain out until QQQ closes >= 10% above post-trigger low; signals execute next TQQQ open.

## Actual TQQQ results

| Strategy | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return | COVID window return | 2022 window return |
|---|---:|---:|---:|---:|---:|---:|
| B0 unchanged | $4,040,314 | 49.49% | -73.53% | -72.64% | +24.58% | -69.83% |
| Gate, fast exception 5 sessions | $1,724,457 | 42.04% | -80.99% | -80.35% | -6.67% | -78.33% |
| Gate, fast exception 8 sessions | $3,101,939 | 47.13% | -79.68% | -78.99% | +24.58% | -76.83% |
| Gate, fast exception 10 sessions | $3,101,939 | 47.13% | -79.68% | -78.99% | +24.58% | -76.83% |

The overlay failed the core objective: all variants ended below B0 and worsened maximum drawdown and worst rolling-year return. The 5-session exception also destroyed the COVID rebound result. The 8- and 10-session variants preserved the defined COVID window, but still ended about $938k below B0 and worsened drawdown by about 6.1 percentage points.

The 2022 loss improved by only about 2.5 percentage points at the 8/10-session setting (-76.83% versus -69.83% is actually **worse**, not better). The candidate held out longer during the 2022 rebound attempt and then re-entered after the matrix cleared; it did not improve the calendar-year result.

## Important event-level diagnosis
- 2019-01-07 B0 recovery was vetoed by the 5-session variant, despite the eventual strong rebound. The 8/10-session exception released this recovery.
- 2020-03-26 COVID recovery was vetoed by the 5-session variant due to the fast-shock flag; the 8/10-session exceptions released it.
- 2022-07-19 recovery was slow (21 sessions from low) and flagged by both structural and fast-shock conditions. All three settings vetoed it repeatedly until 2022-08-10, when the matrix cleared. The strategy therefore remained defensive through a large portion of the summer rebound and still did not improve full-year return.
- The attempt CSV records repeated daily +10%-above-low checks while a recovery is vetoed. These are repeated decision opportunities, not independent market events; do not count them as independent samples.

## Synthetic pre-inception diagnostics — not actual TQQQ
The hypothetical 3x QQQ proxy produced $836,044 for B0, versus $534,492 (5-session), $749,261 (8-session), and $832,677 (10-session). Its max drawdown is approximately -99% and it is not a calibrated TQQQ simulation; these figures are not suitable as fund-performance claims or as validation for 1999–2009.

## Decision
Reject this recovery gate as a trading candidate. It did not improve the primary terminal-wealth objective or drawdown. Do not search more exception thresholds within this same design. The evidence says the frozen structural/fast-shock flags can remain active during powerful recoveries and the 2022 gate delays re-entry without delivering a calendar-year benefit.

## Next experiment
Do not resume broad matrix tuning. Inspect B0's recovery decisions and the 2022 path for a more selective **post-recovery confirmation** that does not simply delay exposure until a DMA clears. Any next candidate should be a separately specified, small hypothesis test with a fixed parameter set and the unchanged B0 control. If no causal rule shows a credible improvement, retain B0 rather than adding complexity.

