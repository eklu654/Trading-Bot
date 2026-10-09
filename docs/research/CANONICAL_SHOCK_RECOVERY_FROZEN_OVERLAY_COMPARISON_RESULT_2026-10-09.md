# Frozen-Input Overlay Comparison — Results and Gate Assessment

**Date:** 2026-10-09 UTC  
**Workflow:** [run 37888844274](https://github.com/eklu654/Trading-Bot/actions/runs/37888844274)  
**Artifact:** `canonical-shock-recovery-frozen-overlay-comparison`, ID `11597820453`  
**Code commit:** `191490af99a1cefa1b46c0012b9b24c194b1e0b0`  
**Workflow definition commit:** `1083830aece25d82ed79ba7a1b19a258ef512617`  
**Status:** SAME-RUN COMPARISON PASSED; candidates remain unselected and retrospective.

## 1. Input and reproducibility

- Common QQQ/TQQQ observations: 4,189 rows, 2010-02-11 through 2026-10-07.
- Frozen market CSV SHA-256: `e79530cf7bda1557adee2eacbdf9b8621f8cde16daf7c533a444be46c68ee2c0`.
- One-session-lagged Fed-state CSV SHA-256: `cb6d59cc792ceedfd561a4e64780b4807192a546f7fc9d0d38eb60b4d1de0ea1`.
- $5,000 starting balance; actual TQQQ; QQQ adjusted close drives signals.
- Close[t] signal executes at open[t+1]. Overnight returns belong to the position held before the open trade; intraday returns belong to the executed position.
- The baseline's event ledger and signal array were checked against a separate event implementation, and its daily return path matched an independent execution loop.
- Nine canonical shock/recovery events. No future outcome labels are used to decide the position signal.
- The same market input is used for B0, F00, F25, F50, F75, and buy-and-hold within this run. Vendor data can be revised between separate runs, so use this manifest hash for this artifact's exact reproduction.

## 2. Zero-cost headline comparison

| Candidate | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return |
|---|---:|---:|---:|---:|
| B0 — baseline | $4,040,315 | 49.49% | -73.53% | -72.64% |
| F00 — 0% in overlay | $3,674,919 | 48.64% | -57.34% | -47.11% |
| F25 — 25% in overlay | $3,932,882 | 49.25% | -57.34% | -52.81% |
| F50 — 50% in overlay | $4,087,452 | 49.59% | -61.19% | -59.88% |
| F75 — 75% in overlay | $4,124,681 | 49.67% | -67.65% | -66.56% |
| TQQQ buy-and-hold | $2,094,669 | 43.70% | -81.66% | -81.04% |

F50 and F75 are still the two candidates worth retaining for further diagnostic work. F50 is the stronger downside compromise in this sample; F75 is more growth-oriented. Neither is selected.

## 3. Predeclared 25 bp cost gate

| Candidate | Ending balance at 25 bp | Max drawdown | Worst rolling 252-session return | Gate status |
|---|---:|---:|---:|---|
| B0 | $3,852,657 | -73.80% | -72.91% | Control |
| F00 | $3,383,558 | -57.56% | -47.77% | Fails wealth gate |
| F25 | $3,652,983 | -57.56% | -53.37% | Fails 95% wealth gate narrowly |
| F50 | $3,829,979 | -61.62% | -60.33% | Passes numerical wealth/downside gates |
| F75 | $3,898,852 | -67.99% | -66.91% | Passes numerical wealth/downside gates |

The predeclared numerical screen requires at least 95% of B0 ending wealth after 25 bp costs, and at least 5 percentage points of improvement in both max drawdown and worst rolling-year return. F50 and F75 clear those numerical conditions in this run. F00 sacrifices too much wealth; F25 narrowly misses the wealth floor.

**Passing numerical gates does not select a candidate.** The remaining gates require the COVID/2018 trade-off to be quantified and the benefit not to depend on one isolated overlay episode.

## 4. Concentration / false-positive counterfactuals

The episode-contribution artifact compares each full candidate against a counterfactual where one overlay episode at a time is removed. These conditional effects are not additive; they should be read as sensitivity diagnostics, not as a decomposition whose rows can be summed.

| Overlay episode | F50 conditional terminal contribution | F75 conditional terminal contribution |
|---|---:|---:|
| 2018-12-04 to 2019-02-04 | -$410,121 | -$199,639 |
| 2019-02-06 to 2019-02-13 | -$117,673 | -$58,376 |
| 2019-03-07 to 2019-03-08 | -$202,395 | -$100,441 |
| 2022-04-05 to 2023-01-25 | +$1,065,518 | +$613,339 |

The 2022 episode lasted 203 sessions, of which 110 were incremental defensive sessions and 93 overlapped the baseline's own shock defense. It is the dominant positive episode for both candidates. Several 2018–2019 whipsaw episodes were negative, with larger opportunity costs at 50% than at 75% exposure.

This is an important warning: the whole-period net advantage over B0 is small compared with the conditional contribution attributed to the 2022 defense episode. Since these effects are non-additive, this does not prove that the entire advantage is literally caused by one event, but it makes concentration risk a central unresolved concern. The protocol's diversification-across-episodes gate is **not yet demonstrated**.

## 5. Chronological segment trade-off

Independent-reset period returns also show the 2018–2019 opportunity cost:
- 2015–2019: B0 +569.6%; F50 +473.5%; F75 +522.4%.
- 2022–2024: B0 +42.3%; F50 +68.1%; F75 +56.3%.
- COVID-period behavior in 2020–2021 matches B0 because the overlay condition did not activate during the easing-state crash/rebound.
- 2025 through 2026-10-07: B0 +100.2%; F50 and F75 also +100.2% as the overlay did not change exposure in this segment.

The figures make the trade-off explicit: F50 buys stronger defense in the 2022 tightening bear, at the cost of lower growth through the 2018–2019 whipsaws. F75 reduces that opportunity cost but provides less drawdown improvement.

## 6. Gate decision and next action

- **B0:** remains the frozen control.
- **F00:** reject as a practical candidate because it fails the wealth-retention gate.
- **F25:** do not advance; it narrowly misses the 95% wealth gate after 25 bp costs.
- **F50/F75:** retain as development candidates only. They pass the numerical wealth/downside screen, but episode concentration and historical selection bias remain unresolved. No winner selected.
- **No AI, paper trading, or broad indicator search** until this compact comparison has been audited and the strategy decision gate is explicitly revisited.

The full daily curve, exposure timeline, event ledger, Fed/DMA transitions, cost sensitivity, and hashes are preserved in the workflow artifact. The entire 2010–2026 sample has already been inspected; these are retrospective development findings, not out-of-sample validation.
