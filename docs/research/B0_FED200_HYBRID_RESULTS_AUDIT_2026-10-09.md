# B0 + Fed-Hike / 200-DMA Hybrid — Results Audit (2026-10-09)

## Provenance

- Preregistration: [B0_FED200_HYBRID_PREREG_2026-10-09.md](B0_FED200_HYBRID_PREREG_2026-10-09.md).
- Workflow: [TQQQ Dot-Com Survivability Research, run 37925444055](https://github.com/eklu654/Trading-Bot/actions/runs/37925444055), completed successfully.
- Test suite: [run 37925444134](https://github.com/eklu654/Trading-Bot/actions/runs/37925444134), completed successfully: **137 passed, 1 warning**.
- Artifact ID: `11613862201`, ZIP SHA-256 `fc9ed8fb3dc9885b8c1c02400381ef59a294fcf2d500b184408b94ff1e7a6094`.
- Summary CSV SHA-256: `120b1afdc9748e23c1b3b4b19694a97582321fa4817e49e3d7d99d0f132c166d`.

## Fixed rule

B0 cash exits take precedence. Only when B0 otherwise wants 100% exposure does the candidate reduce to 50% or 75%, and only when QQQ is below its 200-session DMA and the Fed target rate is at least 0.25 percentage point higher than 126 QQQ sessions earlier. The Fed rate series is the existing hand-maintained event table in `research/tqqq_three_layer_event_attribution.py`. Signals are close-known and execute next open. All candidates use the same corrected synthetic return helper, actual TQQQ return legs, and causal cost engine.

## Results at 10 bps

### Synthetic daily-reset 3× QQQ proxy

| Candidate | Ending balance | CAGR | Max drawdown | Worst 252-session return | Average exposure | First -99% DD crossing |
|---|---:|---:|---:|---:|---:|---|
| B0 | $236,502 | 15.61% | -99.38% | -91.30% | 89.67% | 2002-09-23 |
| B0 + Fed/200-DMA / 50% | $195,170 | 14.78% | -99.39% | -88.44% | 86.43% | 2002-10-07 |
| B0 + Fed/200-DMA / 75% | $220,927 | 15.32% | -99.38% | -89.93% | 88.05% | 2002-09-30 |

Neither Fed candidate improved synthetic maximum drawdown by even 0.1 percentage point. The 50% version made the first -99% crossing two weeks later but ultimately had slightly worse max drawdown and 17.5% less ending wealth than B0. The 75% version was also slightly worse on full-period max drawdown and ended 6.6% below B0.

### Actual TQQQ

| Candidate | Ending balance | CAGR | Max drawdown | Worst 252-session return | Average exposure |
|---|---:|---:|---:|---:|---:|
| B0 | $1,782,472 | 45.57% | -73.64% | -72.75% | 93.04% |
| B0 + Fed/200-DMA / 50% | $1,548,103 | 44.26% | -62.60% | -61.34% | 90.25% |
| B0 + Fed/200-DMA / 75% | $1,687,198 | 45.06% | -68.30% | -67.23% | 91.64% |

The 75% candidate retained 94.65% of B0's actual ending wealth and improved max drawdown by 5.34 percentage points. It also reduced the actual 2022 loss from -70.79% to -65.46% while preserving 2020's +104.32% return. However, it failed the preregistered synthetic max-drawdown gate: its synthetic drawdown was effectively unchanged from B0 (-99.377% versus -99.376%). The 50% candidate failed both wealth-retention gates and also failed to improve the synthetic tail.

## Cost sensitivity — ending balance

| Sample / candidate | 0 bps | 10 bps | 25 bps | 50 bps |
|---|---:|---:|---:|---:|
| Synthetic B0 | $253,406 | $236,502 | $213,210 | $179,312 |
| Synthetic Fed/200-DMA 50% | $214,843 | $195,170 | $168,960 | $132,811 |
| Synthetic Fed/200-DMA 75% | $239,935 | $220,927 | $195,175 | $158,697 |
| Actual TQQQ B0 | $1,816,680 | $1,782,472 | $1,732,302 | $1,651,646 |
| Actual Fed/200-DMA 50% | $1,596,864 | $1,548,103 | $1,477,677 | $1,367,193 |
| Actual Fed/200-DMA 75% | $1,729,926 | $1,687,198 | $1,625,020 | $1,526,297 |

## Preregistered gate outcome

**Rejected. Neither candidate passes all four preregistered gates.**

- 50%: actual ending wealth is 86.85% of B0, synthetic ending wealth is 82.52% of B0, and synthetic max drawdown is marginally worse.
- 75%: actual ending wealth (94.65%) and synthetic ending wealth (93.41%) both pass the 90% retention checks; actual drawdown improves by 5.34 points. But synthetic max drawdown does not improve by the required 3 points.
- Per preregistration, do not retune the rate threshold, 126-session lookback, 200-DMA, or 50%/75% exposures after seeing these results.

## Interpretation and next step

The Fed-hike/200-DMA state did reduce modern actual-TQQQ drawdown and 2022 losses, especially at 75% exposure, but it did not address the synthetic dot-com/GFC near-ruin tail. It therefore does not solve the cross-era problem under the agreed gate. Keep B0 as the control; no paper/live approval follows. Any next experiment should be an orthogonal, preregistered risk-state signal and must be evaluated on both actual TQQQ and the corrected synthetic proxy, without relaxing the gate after results.
