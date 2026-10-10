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

- Synthetic matrix run: [38032525509](https://github.com/eklu654/Trading-Bot/actions/runs/38032525509), success; common evaluation window 2000-03-03 to 2026-10-02, 6,686 observations, post-249-session warm-up.
- Actual-TQQQ cost-stress run: [38032468207](https://github.com/eklu654/Trading-Bot/actions/runs/38032468207), success; common evaluation window 2011-02-07 to 2026-10-02, $5,000 reset at the 250-session warm-up.
- Research tests: [38032525529](https://github.com/eklu654/Trading-Bot/actions/runs/38032525529), success, **148 passed, 1 warning**.
- Earlier assertion-only test failure on run [38032468104](https://github.com/eklu654/Trading-Bot/actions/runs/38032468104) was caused by a brittle test expecting the old inline expression. The test was corrected to match the factored `b0` variable; the subsequent test run passed. No strategy-code defect was indicated by that failure.

## Synthetic 3x-QQQ proxy: long-history survivability

The proxy is a daily-reset 3x QQQ return approximation before TQQQ's 2010 inception, not a tradable historical TQQQ record. Treat these figures as a stress proxy, not actual ETF performance.

| Strategy | Cost | Ending balance | Max drawdown |
|---|---:|---:|---:|
| B0 alone | 0 bps | $253,406 | -99.344% |
| B0 alone | 10 bps | $236,503 | -99.376% |
| B0 alone | 25 bps | $213,210 | -99.421% |
| B0 alone | 50 bps | $179,312 | -99.490% |
| B0 + 250-DMA / 25% below DMA | 0 bps | $905,730 | -85.986% |
| B0 + 250-DMA / 25% below DMA | 10 bps | $797,270 | -86.270% |
| B0 + 250-DMA / 25% below DMA | 25 bps | $658,323 | -86.687% |
| B0 + 250-DMA / 25% below DMA | 50 bps | $478,213 | -87.378% |
| B0 + 175-DMA / 25% below DMA | 0 bps | $685,998 | -95.019% |
| B0 + 175-DMA / 25% below DMA | 10 bps | $588,642 | -95.207% |
| B0 + 175-DMA / 25% below DMA | 25 bps | $467,790 | -95.476% |
| B0 + 175-DMA / 25% below DMA | 50 bps | $318,764 | -95.892% |
| B0 + 150-DMA / 25% below DMA | 0 bps | $547,730 | -95.393% |
| B0 + 150-DMA / 25% below DMA | 10 bps | $457,472 | -95.640% |
| B0 + 150-DMA / 25% below DMA | 25 bps | $349,104 | -95.985% |
| B0 + 150-DMA / 25% below DMA | 50 bps | $222,322 | -96.502% |

**2000-bear-market survivability answer:** in this full proxy run, B0's worst drawdown is -99.344% at zero costs and -99.376% at 10 bps, so it does **not** cross -99.9% in the tested path. However, it comes within roughly 0.6 percentage points of total loss; that is economically near-ruin even though the ending balance later recovers. The combined 250-DMA / 25% candidate has materially better proxy survivability, but its pre-2010 results remain synthetic.

For the specifically requested 125/150/175-DMA family, the 175-DMA / 25% combination is the strongest of these listed rows by terminal balance, but it still experiences about a -95% peak-to-trough loss. Cost stress lowers terminal wealth but does not erase the improvement over B0 alone in this proxy.

## Actual TQQQ: common post-warm-up window

The actual-TQQQ matrix uses 2011-02-07 through 2026-10-02 and the same $5,000 reset at the warm-up date. The B0 control and the combined rows use the same dates and execution convention.

| Strategy | Cost | Ending balance | Max drawdown |
|---|---:|---:|---:|
| B0 alone | 0 bps | $1,816,681 | -73.534% |
| B0 alone | 10 bps | $1,782,473 | -73.640% |
| B0 alone | 25 bps | $1,732,303 | -73.798% |
| B0 alone | 50 bps | $1,651,647 | -74.060% |
| B0 + 150-DMA / 75% below DMA | 0 bps | $1,517,184 | -65.708% |
| B0 + 150-DMA / 75% below DMA | 10 bps | $1,458,409 | -65.887% |
| B0 + 150-DMA / 75% below DMA | 25 bps | $1,374,436 | -66.155% |
| B0 + 150-DMA / 75% below DMA | 50 bps | $1,244,963 | -66.597% |
| B0 + 175-DMA / 75% below DMA | 0 bps | $1,485,550 | -64.173% |
| B0 + 175-DMA / 75% below DMA | 10 bps | $1,432,291 | -64.307% |
| B0 + 175-DMA / 75% below DMA | 25 bps | $1,355,909 | -64.507% |
| B0 + 175-DMA / 75% below DMA | 50 bps | $1,237,427 | -64.839% |

At 10 bps, the 150-DMA / 75% candidate retains about 81.8% of B0's ending wealth and improves maximum drawdown by about 7.75 percentage points. The 175-DMA / 75% candidate retains about 80.4% of B0's ending wealth and improves maximum drawdown by about 9.33 points. At 50 bps, both still show a meaningful drawdown reduction, but with lower terminal wealth than B0.

## Decision and next checks

- Do not promote a candidate based on the synthetic proxy alone.
- The actual-TQQQ results show a wealth/drawdown tradeoff, not a clear dominance over B0 under a wealth-first objective. The 150-DMA / 75% candidate preserves more terminal wealth; the 175-DMA / 75% candidate reduces drawdown more.
- The 250-DMA / 25% candidate is promising in the synthetic proxy, but must be tested against actual TQQQ and across held-out periods before any selection.
- Next: test fixed candidates on chronological holdouts / walk-forward segments, report worst-drawdown dates and recovery time, and preserve the same frozen inputs across variants. No live or paper-trading approval follows from this matrix.
