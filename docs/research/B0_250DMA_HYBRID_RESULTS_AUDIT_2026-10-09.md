# B0 + 250-DMA Hybrid — Results Audit (2026-10-09)

## Provenance and verification

- Preregistration: [B0_250DMA_HYBRID_PREREG_2026-10-09.md](B0_250DMA_HYBRID_PREREG_2026-10-09.md).
- Workflow: [TQQQ Dot-Com Survivability Research, run 37925030292](https://github.com/eklu654/Trading-Bot/actions/runs/37925030292), completed successfully.
- Research tests: [run 37925030219](https://github.com/eklu654/Trading-Bot/actions/runs/37925030219), completed successfully: **135 passed, 1 existing warning**.
- Artifact: `tqqq-dotcom-survivability`, ID `11613501873`, SHA-256 `e482d0b906b388bba0fd50c28b67a27662ad400aed6e47e4a4014f161057d548`.
- Summary CSV SHA-256: `aea1a8fdb27d5b85288a1f4cb56a7463b44f6c2ae62ce0a8dbf8092b12f69c5c`.
- Frozen QQQ input SHA-256: `88dd4a95e43efd9c659ce18126d34f7a397abae274e0c57a1aed519ced8c43ae`.

The workflow used the corrected shared synthetic leverage helper, actual TQQQ returns, common post-warm-up evaluation windows, the causal close-to-next-open engine, and the preregistered 0/10/25/50-bp exposure-change cost model.

## Rule tested

B0's cash exit always takes precedence. Only when B0 otherwise wants 100% exposure does the hybrid cap exposure at 25%, 50%, or 75% when QQQ closes below its 250-session DMA. Above the DMA, B0's target is unchanged. No new shock thresholds or re-entry delays were introduced.

- Synthetic window: 2000-03-03 through 2026-10-02; $5,000 start.
- Actual TQQQ window: 2011-02-07 through 2026-10-02; $5,000 start.
- The 250-DMA choice was informed by previous in-sample grid results; this remains exploratory. The preregistered wealth/drawdown gate was fixed before running this hybrid.

## Results at 10 bps

### Synthetic daily-reset 3× QQQ proxy

| Candidate | Ending balance | CAGR | Max drawdown | Worst 252-session return | Average exposure | First -99% DD crossing |
|---|---:|---:|---:|---:|---:|---|
| B0 | $236,502 | 15.61% | -99.38% | -91.30% | 89.67% | 2002-09-23 |
| B0 + 250-DMA / 25% below | $797,275 | 21.02% | -86.27% | -73.38% | 77.17% | Not crossed |
| B0 + 250-DMA / 50% below | $705,695 | 20.47% | -93.50% | -79.79% | 81.33% | Not crossed |
| B0 + 250-DMA / 75% below | $471,321 | 18.65% | -97.58% | -85.88% | 85.50% | Not crossed |
| Pure 250-DMA / 25% below (diagnostic) | $305,422 | 16.73% | -93.44% | -88.05% | 81.44% | Not crossed |

The hybrid substantially improves synthetic tail behavior. At 10 bps, the 25% variant raises synthetic ending wealth to 3.37× B0 and improves max drawdown by 13.11 percentage points. The 50% variant raises ending wealth to 2.98× B0 and improves max drawdown by 5.88 points. This is not enough to approve either: synthetic-only performance is not the primary objective, and the actual-TQQQ gate must also pass.

### Actual TQQQ

| Candidate | Ending balance | CAGR | Max drawdown | Worst 252-session return | Average exposure |
|---|---:|---:|---:|---:|---:|
| B0 | $1,782,472 | 45.57% | -73.64% | -72.75% | 93.04% |
| B0 + 250-DMA / 25% below | $440,747 | 33.14% | -66.01% | -60.84% | 86.09% |
| B0 + 250-DMA / 50% below | $750,295 | 37.74% | -65.40% | -64.23% | 88.40% |
| B0 + 250-DMA / 75% below | $1,195,391 | 41.90% | -69.36% | -68.32% | 90.72% |
| Pure 250-DMA / 25% below (diagnostic) | $335,225 | 30.83% | -67.83% | -62.93% | 89.90% |

The 75% hybrid is the closest to retaining B0's wealth, but at 10 bps it still ends **32.9% below B0**. It improves actual max drawdown by 4.28 percentage points, but its synthetic max-drawdown improvement is only 1.80 points, below the preregistered 3-point gate. The 25% and 50% variants have larger drawdown reductions but retain only 24.7% and 42.1% of B0's actual ending balance, respectively.

## Cost sensitivity — ending balance

| Sample / candidate | 0 bps | 10 bps | 25 bps | 50 bps |
|---|---:|---:|---:|---:|
| Synthetic B0 | $253,405 | $236,502 | $213,209 | $179,312 |
| Synthetic B0 + 250-DMA / 25% | $905,736 | $797,275 | $658,327 | $478,216 |
| Synthetic B0 + 250-DMA / 50% | $786,203 | $705,695 | $600,051 | $457,791 |
| Synthetic B0 + 250-DMA / 75% | $514,949 | $471,321 | $412,668 | $330,588 |
| Actual TQQQ B0 | $1,816,680 | $1,782,472 | $1,732,302 | $1,651,646 |
| Actual B0 + 250-DMA / 25% | $472,009 | $440,747 | $397,654 | $334,900 |
| Actual B0 + 250-DMA / 50% | $790,355 | $750,295 | $693,939 | $609,164 |
| Actual B0 + 250-DMA / 75% | $1,238,602 | $1,195,391 | $1,133,341 | $1,036,895 |

More frequent exposure changes increase the hybrids' cost sensitivity: B0 has 18 exposure changes on the actual window, while each hybrid has 92. The 250-DMA hybrid's synthetic advantage persists at tested costs, but it does not recover the actual-TQQQ wealth sacrificed.

## 2020 and 2022 behavior

At 10 bps, actual-TQQQ 2020 returns were +104.3% for B0, +76.3% for the 25% hybrid, +85.7% for the 50% hybrid, and +95.1% for the 75% hybrid. In 2022, the same rows returned -70.8%, -60.0%, -62.9%, and -66.6%, respectively. The overlay reduced 2022 losses but also reduced participation in the 2020 recovery; this is the expected trade-off, not evidence of a free improvement.

## Preregistered gate outcome

**Rejected. No hybrid qualifies for further holdout testing under the preregistered gate.**

At 10 bps, every hybrid fails the requirement to retain at least 90% of B0's actual-TQQQ ending balance. The 75% hybrid also fails the synthetic drawdown-improvement requirement. Per preregistration, do not retune the 250-DMA or 25/50/75% levels after seeing these results. Keep B0 as the control and do not paper/live trade these hybrid candidates.

## Next research direction

The experiment supports the original concern that the synthetic dot-com/GFC tail and modern compounding objective conflict under simple DMA overlays. The next candidate should be an orthogonal, preregistered state modifier (rather than another post-hoc DMA grid), and it must preserve the actual-TQQQ wealth gate while being evaluated on the same corrected synthetic proxy. No strategy is approved for live deployment.
