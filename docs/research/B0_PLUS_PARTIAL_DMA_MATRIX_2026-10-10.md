# B0 + Partial-DMA Matrix Audit — 2026-10-10

## Why this rerun exists

The earlier partial-DMA matrix tested DMA exposure rules as standalone strategies. That is useful as a diagnostic, but it was not the intended experiment. The intended candidate is **B0 combined with a DMA overlay**:

- B0 signal: exit after QQQ close-to-close return is at or below -4.5%; remain defensive until QQQ rebounds 10% from the running low.
- Execution: close signal executes at the next open; overnight return uses the prior exposure and intraday return uses the newly executed exposure.
- Combined exposure: `min(B0 exposure, DMA exposure)`. Thus B0's defensive state takes precedence. Outside a B0 defensive window, exposure is 100% when QQQ is above its DMA and the fixed matrix exposure when QQQ is below it.
- DMA re-entry is immediate; no additional re-entry delay is introduced.
- DMA-only rows remain in the CSV as `DMA_ONLY_DIAGNOSTIC`; they are not candidates for selection.
- Initial capital is $5,000. Cost stress charges 0/10/25/50 bps per absolute exposure change. No cash yield is assumed.

## Validation

- Synthetic matrix run: [38033073261](https://github.com/eklu654/Trading-Bot/actions/runs/38033073261), success; common evaluation window 2000-03-03 to 2026-10-02, 6,686 observations, post-249-session warm-up.
- Actual-TQQQ cost-stress run: [38033073266](https://github.com/eklu654/Trading-Bot/actions/runs/38033073266), success; common evaluation window 2011-02-07 to 2026-10-02, $5,000 reset at the 250-session warm-up.
- Research tests: [38033073292](https://github.com/eklu654/Trading-Bot/actions/runs/38033073292), success, **151 passed, 1 warning**.
- Earlier assertion-only test failure on run [38032468104](https://github.com/eklu654/Trading-Bot/actions/runs/38032468104) was caused by a brittle test expecting the old inline expression. The test was corrected to match the factored `b0` variable; the subsequent test run passed. No strategy-code defect was indicated by that failure.

## Synthetic 3x-QQQ proxy: long-history survivability

The proxy is a daily-reset 3x QQQ return approximation before TQQQ's 2010 inception, not a tradable historical TQQQ record. Treat these figures as a stress proxy, not actual ETF performance.

| Strategy | Cost | Ending balance | Max drawdown |
|---|---:|---:|---:|
| B0 alone | 0 bps | $253,405 | -99.344% |
| B0 alone | 10 bps | $236,502 | -99.376% |
| B0 alone | 25 bps | $213,209 | -99.421% |
| B0 alone | 50 bps | $179,312 | -99.489% |
| B0 + 250-DMA / 25% below DMA | 0 bps | $905,733 | -85.986% |
| B0 + 250-DMA / 25% below DMA | 10 bps | $797,273 | -86.270% |
| B0 + 250-DMA / 25% below DMA | 25 bps | $658,325 | -86.687% |
| B0 + 250-DMA / 25% below DMA | 50 bps | $478,215 | -87.378% |
| B0 + 175-DMA / 25% below DMA | 0 bps | $686,007 | -95.019% |
| B0 + 175-DMA / 25% below DMA | 10 bps | $588,649 | -95.207% |
| B0 + 175-DMA / 25% below DMA | 25 bps | $467,796 | -95.476% |
| B0 + 175-DMA / 25% below DMA | 50 bps | $318,768 | -95.892% |
| B0 + 150-DMA / 25% below DMA | 0 bps | $547,731 | -95.393% |
| B0 + 150-DMA / 25% below DMA | 10 bps | $457,473 | -95.640% |
| B0 + 150-DMA / 25% below DMA | 25 bps | $349,105 | -95.985% |
| B0 + 150-DMA / 25% below DMA | 50 bps | $222,323 | -96.502% |

**2000-bear-market survivability answer:** in this full proxy run, B0's worst drawdown is -99.344% at zero costs and -99.376% at 10 bps, so it does **not** cross -99.9% in the tested path. However, it comes within roughly 0.6 percentage points of total loss; that is economically near-ruin even though the ending balance later recovers. The combined 250-DMA / 25% candidate has materially better proxy survivability, but its pre-2010 results remain synthetic.

For the specifically requested 125/150/175-DMA family, the 175-DMA / 25% combination is the strongest of these listed rows by terminal balance, but it still experiences about a -95% peak-to-trough loss. Cost stress lowers terminal wealth but does not erase the improvement over B0 alone in this proxy.

## Actual TQQQ: common post-warm-up window

The actual-TQQQ matrix uses 2011-02-07 through 2026-10-02 and the same $5,000 reset at the warm-up date. The B0 control and the combined rows use the same dates and execution convention.

| Strategy | Cost | Ending balance | Max drawdown |
|---|---:|---:|---:|
| B0 alone | 0 bps | $1,816,679 | -73.534% |
| B0 alone | 10 bps | $1,782,471 | -73.640% |
| B0 alone | 25 bps | $1,732,301 | -73.798% |
| B0 alone | 50 bps | $1,651,645 | -74.060% |
| B0 + 150-DMA / 75% below DMA | 0 bps | $1,517,183 | -65.708% |
| B0 + 150-DMA / 75% below DMA | 10 bps | $1,458,408 | -65.887% |
| B0 + 150-DMA / 75% below DMA | 25 bps | $1,374,435 | -66.155% |
| B0 + 150-DMA / 75% below DMA | 50 bps | $1,244,962 | -66.597% |
| B0 + 175-DMA / 75% below DMA | 0 bps | $1,485,548 | -64.172% |
| B0 + 175-DMA / 75% below DMA | 10 bps | $1,432,289 | -64.307% |
| B0 + 175-DMA / 75% below DMA | 25 bps | $1,355,908 | -64.507% |
| B0 + 175-DMA / 75% below DMA | 50 bps | $1,237,425 | -64.839% |

At 10 bps, the 150-DMA / 75% candidate retains about 81.8% of B0's ending wealth and improves maximum drawdown by about 7.75 percentage points. The 175-DMA / 75% candidate retains about 80.4% of B0's ending wealth and improves maximum drawdown by about 9.33 points. At 50 bps, both still show a meaningful drawdown reduction, but with lower terminal wealth than B0.

## Decision and next checks

- Do not promote a candidate based on the synthetic proxy alone.
- The actual-TQQQ results show a wealth/drawdown tradeoff, not a clear dominance over B0 under a wealth-first objective. The 150-DMA / 75% candidate preserves more terminal wealth; the 175-DMA / 75% candidate reduces drawdown more.
- The 250-DMA / 25% candidate is promising in the synthetic proxy, but must be tested against actual TQQQ and across held-out periods before any selection.
- Next: test fixed candidates on chronological holdouts / walk-forward segments, report worst-drawdown dates and recovery time, and preserve the same frozen inputs across variants. No live or paper-trading approval follows from this matrix.


## Fixed-period diagnostics — added 2026-10-10

The matrix now emits separate period summaries and explicit full-window maximum-drawdown peak/trough dates. Period returns are rebased to $5,000 at the start of each period; they are **not chained across periods**. This is intentional for era comparison, and must not be confused with the full-window terminal balance.

- Reference synthetic matrix run for the reported tables: [38033073261](https://github.com/eklu654/Trading-Bot/actions/runs/38033073261), success; artifact ID `11663241877`, ZIP SHA-256 `74a0eed85943992a5affbb30eed3086bf36acff710932b3a9ee8911ab42963f4`. Artifact includes frozen input, full-window matrix, period CSV, and manifest. Frozen-input SHA-256: `882fbed45c55f0aa0694b28e58dd1ddf4ced36f609a3b363d85f6a58a4efa944`; matrix SHA-256: `e71bdf6e0332c498ef57737e907deba32aca950e9df0b08c7206901b87f0b417`; period SHA-256: `141005972f54b7f4ec7cdec7350189bbf249c751ca87253a668eb9f320a8fcd0`. Frozen input: 6,935 rows.
- Reference actual-TQQQ matrix run for the reported tables: [38033073266](https://github.com/eklu654/Trading-Bot/actions/runs/38033073266), success; artifact ID `11663067050`, ZIP SHA-256 `6248c3c6aabf614079d19bc117a661c8406ca3aef9cf35c27277681be0ccff78`. Artifact includes frozen input, full-window matrix, period CSV, and manifest. Frozen-input SHA-256: `42ee24b2060d4d7b67308c030fc58d6fd72dc48b36053937db24349588f7708c`; matrix SHA-256: `14792062a0e2c6d29ca868fc89a1d286f7f7da9ea900d93a8c30461564ae6669`; period SHA-256: `012c8bc31d8db14b280f26027f23693ba84d313dc431610816b10f74802ec687`. Frozen input: 4,186 rows.
- Research tests after adding frozen-input manifests: [38033073292](https://github.com/eklu654/Trading-Bot/actions/runs/38033073292), success, **151 passed, 1 warning**.

### Dot-com bear and maximum-drawdown timing

At 10 bps, the synthetic B0 period summary ends the dot-com-bear window (2000-03-03 through 2002-12-31) at about **$85 from $5,000**, with a period maximum drawdown of **-99.19%** and a minimum equity near **$45.72**. So it technically survives the period, but the path is near-ruin.

Across the full 2000-03-03 through 2026-10-02 proxy path, B0's worst drawdown peak/trough dates are **2000-03-27 to 2009-03-09**. Its 10-bps full-window maximum drawdown is **-99.376%**, so the tested path does not hit -99.9%; the deepest drawdown spans the dot-com collapse and subsequent financial-crisis period rather than ending in 2002.

For B0 + 250-DMA / 25% below DMA at 10 bps, the dot-com-bear period ends near **$1,063**, period max drawdown is **-84.31%**, and the full-path drawdown trough occurs on 2003-04-09. This is a substantial survivability improvement in the proxy, but still a synthetic return history before TQQQ existed.

### Actual-TQQQ era comparison

At 10 bps, B0's full-window maximum drawdown peak/trough dates are **2021-11-19 to 2022-12-28**. The combined 175-DMA / 50%-below-DMA candidate has the same peak/trough dates, but its full-window ending balance is about **$1.065M** versus **$1.782M** for B0, while maximum drawdown improves from **-73.64% to -53.20%**.

Rebased to $5,000 for each era, the 175-DMA / 50% candidate shows a clear regime tradeoff:

| Era | B0 ending balance | B0 max DD | B0 + 175-DMA / 50% ending balance | Combined max DD |
|---|---:|---:|---:|---:|
| 2011–2015 | $26,988 | -39.89% | $16,975 | -39.01% |
| 2016–2019 | $28,503 | -38.14% | $21,145 | -33.99% |
| 2020–2021 | $21,153 | -47.11% | $19,248 | -44.55% |
| 2022–2024 | $7,088 | -72.71% | $9,937 | -51.56% |
| 2025–2026-10-02 | $9,659 | -56.21% | $9,694 | -42.56% |

The overlay sacrifices wealth during the earlier bull-market eras, but reduces drawdown in every listed era and beats B0's rebased period ending balance during 2022–2024 and slightly during 2025–2026. This is evidence for a fixed-candidate holdout test, not proof of future performance.

## Updated research priority

1. Keep B0 as the wealth-first control.
2. Carry forward a small, predeclared Pareto set for walk-forward/holdout evaluation: 150-DMA / 75% below DMA (more wealth, smaller drawdown improvement), 175-DMA / 75% (slightly less wealth, lower drawdown), and 175-DMA / 50% (larger drawdown improvement, lower terminal wealth). Retain 250-DMA / 25% only as a separate synthetic-survivability candidate pending actual-TQQQ validation.
3. Compare candidate behavior by era and cost on identical frozen inputs; do not optimize exposure thresholds using the reported test eras.
4. No paper or live-trading approval follows from these results.


## B0 control cross-check and event-level attribution

A separate successful robustness run, [38032984399](https://github.com/eklu654/Trading-Bot/actions/runs/38032984399), used the canonical inception-start actual-TQQQ path from 2010-03-11 through 2026-10-02 (not the warm-up-reset window used by the DMA matrix). Its cost-free results were:

- B0 / canonical shock-recovery: **$4,040,312**, max drawdown **-73.534%**.
- TQQQ buy-and-hold: **$2,094,669**, max drawdown **-81.660%**.
- At 10 bps, B0 ends near **$3,964,233**, max drawdown **-73.640%**, across 19 trades.

The period audit shows B0 outperforming buy-and-hold in 2010–2014, 2015–2019, 2020–2021, and 2022–2024, but lagging buy-and-hold in 2025 through the current cutoff. This supports keeping B0 as the control, while avoiding the claim that every exit event helps.

Event-level counterfactual attribution makes that limitation concrete. The 2020-02-27 shock event (low 2020-03-16, decision 2020-03-26) added about **$1.345M** of terminal wealth relative to removing that one defensive event. But the 2020-06-11 event (decision 2020-07-06) cost about **$1.019M** versus its no-defense counterfactual, and the 2020-09-03 event cost about **$328k**. Later negative event contributions included approximately **-$236k** for the 2025-04-03 signal and **-$47k** for the 2026-06-05 signal. These are single-event counterfactuals, not additive causal components; removing one event changes the compounding path.

**Implication:** B0's broad protection is valuable over the full sample, but its fixed trigger can exit during recoveries and miss upside. The DMA overlay changes the wealth/drawdown tradeoff; it does not solve the signal-quality problem by itself. Future work should test fixed candidates without tuning on the same reported eras, then examine whether a separate regime/context layer can distinguish crash-protection events from false-positive exits.


A subsequent rerun after adding workflow path filters confirmed the matrix workflows still pass without changing the research scripts: synthetic [38033247815](https://github.com/eklu654/Trading-Bot/actions/runs/38033247815) (artifact `11662173129`, ZIP SHA-256 `de2bd89ce0683613554daba25161058a552859184d9c5821f6d7095e858aada0`) and actual TQQQ [38033247884](https://github.com/eklu654/Trading-Bot/actions/runs/38033247884) (artifact `11663222288`, ZIP SHA-256 `370fcfedfa5f6e66d6e66be6e8aca3db7eb69d45f5bd2cf361ba53b46d4fae8d`). Each rerun carries its own frozen-input and output hashes; use the reference-run hashes above to reproduce the specific tables in this document.
