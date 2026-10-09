# Results — canonical shock/recovery plus structural matrix

Date: 2026-10-09  
**Status: RUN PASSED; overlay family rejected as a production candidate on current evidence.**

## Reproducibility
- Workflow run: https://github.com/eklu654/Trading-Bot/actions/runs/37912413316
- Result: job `compare` completed successfully; compile, execution, and artifact upload all passed.
- Artifact: `canonical-plus-structural-matrix`, ID `11607472004`, SHA-256 `8714513d2f7390f562cdddfcaf6e228ef0e187bfcc5ac4bd5dabe805afef3afd`.
- Artifact data manifest: 6,938 synthetic rows from 1999-03-10 to 2026-10-07; 4,189 aligned live-TQQQ rows from 2010-02-11 to 2026-10-07; $5,000 start; nine baseline events; frozen actual input SHA-256 `8f23d72b2b4b281b66210755ad4b8f08bb942d4a754c6e8ba5153abc3f4352ba`.
- 144 parameter combinations per overlay family/source, with a B0 control. Both structural+fast and fast-only were compared. The combined target is `min(B0, overlay)`.

## Actual TQQQ: live fund history only

| Strategy | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return |
|---|---:|---:|---:|---:|
| B0 canonical -4.5% / +10% | $4,040,315 | 49.49% | -73.53% | -72.64% |
| Best structural+fast by ending balance | $727,050 | 34.86% | -59.47% | -53.43% |
| Best structural+fast by max drawdown | $579,625 | 33.03% | -57.24% | -55.31% |
| Best fast-only by ending balance | $534,157 | 32.38% | -71.36% | -70.07% |
| Best fast-only by max drawdown | $319,593 | 28.36% | -67.84% | -65.56% |

Best structural+fast terminal-balance row: structural DMA 150, fast DMA 100, 63-session return threshold -20%, 252-session drawdown threshold -20%, VIX 30, structural exposure 25%. It still ended about 82.0% below B0. The least-bad max-drawdown row used the same DMAs and return/drawdown thresholds, VIX 28, exposure 25%; drawdown improved about 16.3 percentage points, but terminal wealth fell about 85.7% versus B0.

### Stress windows
- COVID crash/rebound window: B0 returned **+24.6%**; best structural+fast by ending balance returned **-8.6%**. This fails the recovery-preservation objective.
- Calendar 2022: B0 returned **-69.8%**; best structural+fast by ending balance returned **-51.5%**; least-bad drawdown candidate returned **-53.4%**. The improvement in 2022 did not compensate for lost long-run compounding and the COVID false defense.
- The matrix overlays are therefore **REJECTED as a current production candidate**. Do not choose the best row just because it improves drawdown.

## Pre-TQQQ synthetic 3x QQQ proxy — diagnostic only

| Strategy | Ending balance | CAGR | Max drawdown | Dot-com window return | GFC window return | COVID window return | 2022 window return |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 canonical | $836,052 | 20.40% | -99.37% | -98.17% | -53.50% | +26.34% | -68.81% |
| Best structural+fast by ending balance | $1,456,991 | 22.85% | -88.65% | -72.64% | +36.43% | -9.16% | -60.24% |
| Best fast-only by ending balance | $1,496,338 | 22.97% | -81.25% | -68.40% | -33.32% | -8.34% | -73.34% |

The synthetic overlay's better terminal wealth is not proof of historical TQQQ performance. This approximation has a near-total-loss B0 drawdown and is not fully calibrated for financing, fees, distributions, tracking, or all real fund mechanics. It is only a signal-regime diagnostic. Its failure to preserve the COVID rebound also argues against promoting these matrix rules.

## Interpretation / decision
1. The user's correction was implemented: the matrix was tested **in tandem with** the canonical shock/recovery baseline, not as a standalone strategy.
2. The overlay cannot raise exposure above B0 and cannot cancel a B0 defensive episode.
3. The result is decisive enough to stop sweeping this exact matrix: it reduces live-TQQQ drawdown but destroys too much terminal wealth and misses too much COVID rebound.
4. Do not run another parameter search over this same matrix. Next useful work is audit the specific state transitions responsible for the false COVID defense and compare only a small, predeclared, non-sticky or recovery-aware overlay ablation against B0. Any new rule remains development-only because the full modern history has already been inspected.
5. Keep the canonical B0 result ($4.040M on its recorded frozen input) as the working control; do not replace it with the proxy result or a best-in-grid overlay.

## Known implementation caveat
The previous matrix's sticky-hard-defense state is preserved: once the fast-shock override arms, it remains at 0% until QQQ closes at/above the selected structural DMA, even if the immediate fast-shock condition ceases. This likely explains some excessive time out of market and should be explicitly ablated before any further candidate selection. The script's output uses the same established close-to-next-open execution helper for both actual and proxy returns.


## Same-input correction rerun
- Corrected run: [37914258527](https://github.com/eklu654/Trading-Bot/actions/runs/37914258527); artifact ID `11609270400`, SHA-256 `50232ef0bb2c7090a7ee6113f322d02cbdd39789d48d2eb71b0206d88a7d1a8c`.
- The live-period overlay indicators now retain pre-inception QQQ lookback history but use the exact frozen QQQ adjusted closes used by B0 on all actual-TQQQ dates. The actual-TQQQ result is unchanged to displayed precision: B0 $4.040M; best structural+fast $727k; COVID window -8.63% vs B0 +24.58%. Rejection remains.
