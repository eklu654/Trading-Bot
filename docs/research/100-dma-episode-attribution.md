# 100-DMA Episode Attribution — Current Findings

Status: frozen descriptive research, not parameter optimization.

## Baseline

The confirmed synthetic-TQQQ survivability experiment uses:

- $5,000 starting capital
- 1999-03-10 through 2026-10-03
- daily-reset 3x QQQ proxy
- QQQ adjusted close for the 100-DMA signal
- 100-DMA
- 100% exposure above the DMA
- 0% exposure below the DMA
- immediate re-entry
- next-open execution

The independently reproduced terminal balance is approximately $128.315 billion.

## First episode-level finding

The value is not evenly distributed across hundreds of small exits. It is dominated by a small number of long defensive episodes.

The most important defensive intervals identified from the confirmed equity path are:

| Exit | Re-entry | Flat trading days | Synthetic TQQQ buy-and-hold return while defensive |
|---|---:|---:|---:|
| 2000-04-12 | 2000-06-19 | 45 | -8.25% |
| 2000-09-25 | 2001-05-21 | 163 | -92.57% |
| 2002-03-12 | 2002-10-21 | 154 | -82.32% |
| 2008-08-29 | 2009-02-09 | 110 | -78.53% |
| 2022-04-05 | 2022-07-29 | 78 | -39.62% |

The longest 2000-2001 and 2002 defensive intervals are particularly important: the synthetic TQQQ proxy lost roughly 92.6% and 82.3%, respectively, while the strategy remained flat.

## False-positive / whipsaw evidence

The same 100-DMA rule also produces many short exits that are followed by positive returns before re-entry. Across the complete exit/re-entry sample, these are common in ordinary markets.

This is the central trade-off:

- In major persistent downtrends, the 100-DMA can prevent catastrophic compounding damage.
- In sideways or rapidly recovering markets, the same short DMA can exit repeatedly and sacrifice upside.
- Therefore the research question should not be "is 100-DMA best?" It should be "what distinguishes a trend break that will persist from one that will reverse?"

## Crisis comparison from the confirmed path

| Window | 100-DMA strategy return | Buy-and-hold synthetic TQQQ return |
|---|---:|---:|
| 2000-2003 | +509.6% | -99.61% |
| 2008-2009 | +254.8% | -61.31% |
| 2020 | +188.7% | +118.8% |
| 2022 | +14.2% | -78.2% |

These are window returns from the first to last trading observation in each calendar window, not standalone backtests with capital reset for each crisis.

## Fed context to test next

The Federal Reserve's official historical record shows the 1999-2000 tightening cycle reached 6.50% in May 2000 after repeated hikes. The first 100-DMA exit occurred on 2000-04-12, after the March 21, 2000 hike to 6.00% but before the final May 16 hike to 6.50%.

The 2008 episode is different: the 100-DMA exit on 2008-01-02 occurred after the Fed had already begun cutting rates, while the NBER later dated the recession's start to December 2007. The 2020 exit occurred on 2020-02-27 before the Fed's emergency March cuts. The 2022 exit occurred before the Fed's first March 2022 hike.

This strongly suggests that Fed direction may be useful as **regime context**, but a rate-hike/cut rule is unlikely to replace the market-price trigger. The next test should measure this systematically rather than assume it.

## Next research gate

For each 100-DMA exit/re-entry episode, add contemporaneously available macro variables:

1. Fed target rate and direction.
2. Days since last hike/cut.
3. Cumulative tightening/loosening from the preceding cycle trough.
4. Distance from the Fed cycle peak.
5. Yield-curve state.
6. Labor/activity/credit stress state.
7. Market decline magnitude and duration.
8. Subsequent recovery speed.

The purpose is classification, not threshold optimization. Only after the historical episode anatomy is understood should an adaptive rule be tested out-of-sample.
