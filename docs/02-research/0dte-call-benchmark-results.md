# 0DTE Call-Credit-Spread Benchmark Results

**Status:** Completed, preliminary  
**Source:** User-provided 0DTESPX preview results JSON  
**Strategy:** SPX 0DTE call-credit spreads, entered 09:35, 50% profit target, time exit 15:55  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012 per configuration  
**Platform starting capital:** $100,000 per preview

## Configurations

| ID | Short call delta | Long call delta | Entry | Exit |
|---|---:|---:|---|---|
| CALL_16D_0935_50TP | 0.16 | 0.06 | 09:35 | 50% profit target or 15:55 |
| CALL_20D_0935_50TP | 0.20 | 0.10 | 09:35 | 50% profit target or 15:55 |
| CALL_25D_0935_50TP | 0.25 | 0.15 | 09:35 | 50% profit target or 15:55 |

## Reported results

| Metric | 16-delta | 20-delta | 25-delta |
|---|---:|---:|---:|
| Ending NLV | $81,989.40 | $74,264.40 | $71,149.28 |
| Total return | -18.0106% | -25.7356% | -28.8507% |
| CAGR | -4.8246% | -7.1412% | -8.1268% |
| Annualized Sharpe | -0.6502 | -0.9721 | -1.1495 |
| Annualized Sortino | -0.1842 | -0.3302 | -0.4702 |
| Maximum drawdown | -19.4960% | -29.1217% | -31.0199% |
| Win rate | 90.6126% | 87.4505% | 82.9051% |
| Profit factor | 0.8040 | 0.7572 | 0.7565 |
| Expectancy per day | -$17.80 | -$25.43 | -$28.51 |
| Best day | $505.12 | $570.12 | $710.12 |
| Worst day | -$3,334.88 | -$2,639.88 | -$3,379.88 |
| Fees | $4,855.60 | $4,855.60 | $4,850.72 |
| Slippage | $9,950.00 | $9,950.00 | $9,940.00 |

## Paired comparison with the put benchmark

The put and call files cover the same 1,012 sessions and use the same entry/exit template, allowing a paired directional comparison.

| Short delta | Put-vs-call daily result |
|---|---:|
| 16Δ | Put won 668 sessions; call won 257; 87 ties |
| 20Δ | Put won 626; call won 307; 79 ties |
| 25Δ | Put won 544; call won 416; 52 ties |

For the 16Δ configuration, the put spread's average daily net P/L exceeded the call spread by approximately $18.82 across the paired sample. The difference was strongly related to the underlying's daily direction: on positive benchmark days, the 16Δ put averaged about +$87.38 while the call averaged about -$97.75; on negative benchmark days, the put averaged about -$105.33 while the call averaged about +$79.93.

This is evidence that the two defined-risk verticals can serve as directional complements. It is not evidence that either side has a persistent standalone edge.

## Interpretation

1. None of the three call-credit configurations produced a positive full-sample return.
2. The 16Δ call spread was the least negative of the tested call configurations, but still lost 18.01% with a -19.50% maximum drawdown.
3. Increasing the short-call delta from 16Δ to 25Δ increased the full-sample loss and drawdown in this benchmark.
4. All configurations had high win rates, but the large losing sessions dominated the economics. This is the same high-win-rate/tail-loss pattern observed in the put tests.
5. The benchmark underlying gained approximately 109.46% over the same 1,012-session period, so these short-call results should not be interpreted as a general market-performance comparison; they represent a specific short-premium strategy under the tested execution assumptions.
6. These are $100,000 platform previews, not $2,000 account results, and none is deployment-approved.

## Important 0DTE methodology finding

The tested 15:55 time exit is not the only 0DTE management approach worth testing. Official tastylive research has specifically examined opening-window 0DTE short premium and reported favorable results for positions opened near the market open and managed after roughly 90 minutes, while warning about late-day short-premium entry behavior. Separate tastylive research emphasizes that 0DTE gamma increases substantially as expiration approaches and recommends active management rather than simply carrying short premium into the close.

Therefore, the next 0DTE experiment should be a **frozen management-timing matrix**, not another arbitrary strike search:

- same 16Δ/6Δ, 20Δ/10Δ, and 25Δ/15Δ structures;
- both put and call spreads;
- 50% profit target;
- early mechanical exits around the first 90 minutes;
- additional midday exits;
- the existing 15:55 control;
- explicit loss-management variants;
- identical fill/fee/slippage assumptions across every cell.

Only after that should the matrix be stratified by volatility/regime.

## Limitations

- These results do not establish feasibility at the project's $2,000 account size.
- They do not test portfolio-level BPR, Delta, concentration, or the ETF/options switch.
- They do not prove that the platform's simulated slippage matches broker-realized fills.
- They do not constitute a complete implementation of all tastytrade/tastylive 0DTE research.
- The results are historical simulations and are not a guarantee of future performance.

## Reproducibility

Source file: `0dte_call_benchmark.json`.

The three configurations contain platform source hashes in the supplied JSON and should be preserved when comparing future reruns.
