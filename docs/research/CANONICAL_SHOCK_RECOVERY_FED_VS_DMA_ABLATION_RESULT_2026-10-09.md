# Fed Filter vs. DMA-Only Overlay — Frozen-Input Ablation Result

**Date:** 2026-10-09 UTC  
**Plan:** [predeclared ablation plan](CANONICAL_SHOCK_RECOVERY_FED_VS_DMA_ABLATION_PLAN_2026-10-09.md)  
**Workflow:** [run 37889360594](https://github.com/eklu654/Trading-Bot/actions/runs/37889360594)  
**Artifact:** `canonical-shock-recovery-frozen-overlay-comparison`, ID `11597189873`  
**Status:** PASS — diagnostic comparison only; no candidate selected.

## 1. Frozen data and accounting

- 4,189 aligned sessions, 2010-02-11 through 2026-10-07.
- Market input SHA-256: `eea8ba3291428ec6e386002bab09de94a54e16508648c17f2a947b5e80731c1e`.
- Lagged Fed-state SHA-256: `cb6d59cc792ceedfd561a4e64780b4807192a546f7fc9d0d38eb60b4d1de0ea1`.
- B0 event/position logic independently reconciled. All candidates share the same market rows and next-open accounting.
- Candidate definitions are frozen as in the ablation plan. This is retrospective development evidence, not an untouched holdout.

## 2. Headline results

| Candidate | Overlay condition | Ending balance | Max drawdown | Worst rolling 252-session return | Defensive sessions |
|---|---|---:|---:|---:|---:|
| B0 | Shock/recovery baseline | $4,040,314 | -73.53% | -72.64% | 274 |
| F50 | Active Fed + below 200-DMA; 50% TQQQ | $4,087,451 | -61.19% | -59.88% | 473 |
| F75 | Active Fed + below 200-DMA; 75% TQQQ | $4,124,680 | -67.65% | -66.56% | 473 |
| D50 | Below 200-DMA regardless of Fed; 50% TQQQ | $1,988,183 | -60.38% | -59.04% | 701 |
| D75 | Below 200-DMA regardless of Fed; 75% TQQQ | $2,939,995 | -67.11% | -66.00% | 701 |
| TQQQ buy-and-hold | No defense | $2,094,669 | -81.66% | -81.04% | 0 |

The DMA-only variants substantially reduced drawdown, but paid for it with too many defensive sessions and much lower ending wealth. D50 finished below TQQQ buy-and-hold in this run; D75 finished above buy-and-hold but about $1.10M below B0. F50/F75 preserved much more wealth because the Fed condition filtered out many DMA-only defensive episodes.

## 3. Cost sensitivity

At 25 bp per full exposure change:
- B0: $3.853M
- F50: $3.830M
- F75: $3.899M
- D50: $1.746M
- D75: $2.690M

The simple DMA-only overlay does not pass the wealth-retention gate. The Fed condition is clearly material to this sample's result; it is not merely redundant with the 200-DMA.

## 4. Regime behavior

| Segment | B0 reset return | F50 reset return | F75 reset return | D50 reset return | D75 reset return |
|---|---:|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +895.0% | +895.0% | +644.0% | +764.5% |
| 2015–2019 | +569.6% | +473.5% | +522.4% | +311.4% | +429.1% |
| 2020–2021 | +325.6% | +325.6% | +325.6% | +287.3% | +306.7% |
| 2022–2024 | +42.3% | +68.1% | +56.3% | +71.6% | +58.9% |
| 2025–2026-10-07 | +100.2% | +100.2% | +100.2% | +95.5% | +98.8% |

Returns reset to 1.0 at the beginning of each segment; they are not the continuous account's period return. The DMA-only overlay underperformed heavily in earlier periods and through COVID, while it did help in 2022. The Fed filter avoided many earlier false-positive periods, but its measured benefit still depends heavily on the single modern tightening bear.

## 5. Interpretation

1. **The Fed condition adds meaningful selectivity versus below-200-DMA alone.** In this sample, removing the Fed entry condition increases defensive sessions from 473 to 701 for the tested partial-exposure candidates and damages terminal wealth materially.
2. **The 200-DMA is not enough by itself at these exposure levels.** D50/D75 reduce max drawdown but fail the wealth-retention objective.
3. **The active-Fed candidate remains unvalidated.** Its benefit is concentrated in the 2022 tightening episode, and the historical sample does not contain multiple independent post-2010 tightening-driven bear markets to establish repeatability.
4. **Do not optimize the Fed rule against this sample.** The result supports retaining the Fed-state hypothesis for future research, not approving F50/F75 or tuning state boundaries.
5. **No strategy is selected and no paper/live trading is authorized.** B0 remains the control; F50/F75 remain diagnostic candidates that failed the episode-diversification gate; D50/D75 fail the wealth-retention gate.

## Reproducibility

The artifact includes the frozen market CSV, lagged Fed-state CSV, manifest, summary, chronological segments, cost sensitivity, daily target exposure/equity, shock/recovery event ledger, Fed/DMA transitions, and leave-one-episode-out counterfactuals.
