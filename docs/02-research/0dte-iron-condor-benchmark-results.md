# 0DTE Iron Condor Benchmark Results

**Status:** Completed, preliminary  
**Source:** User-provided 0DTESPX preview results JSON  
**Strategy:** Symmetric SPX 0DTE iron condors, entered 09:35, 50% profit target, time exit 15:55  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012 per configuration  
**Platform starting capital:** $100,000 per preview

## Configurations

| ID | Short put/call delta | Long put/call delta | Entry | Exit |
|---|---:|---:|---|---|
| IC_16D_6D_0935_50TP | 0.16 / 0.16 | 0.06 / 0.06 | 09:35 | 50% profit target or 15:55 |
| IC_20D_10D_0935_50TP | 0.20 / 0.20 | 0.10 / 0.10 | 09:35 | 50% profit target or 15:55 |
| IC_25D_15D_0935_50TP | 0.25 / 0.25 | 0.15 / 0.15 | 09:35 | 50% profit target or 15:55 |

## Reported results

| Metric | 16D/6D | 20D/10D | 25D/15D |
|---|---:|---:|---:|
| Ending NLV | $114,014.72 | $88,206.00 | $78,883.24 |
| Total return | +14.0147% | -11.7940% | -21.1168% |
| CAGR | +3.3199% | -3.0767% | -5.7355% |
| Annualized Sharpe | 0.4193 | -0.2734 | -0.6131 |
| Annualized Sortino | 0.1517 | -0.1274 | -0.3506 |
| Maximum drawdown | -9.1447% | -25.9398% | -31.8710% |
| Calmar/MAR | 0.3630 | -0.1186 | -0.1800 |
| Win rate | 86.5613% | 79.3478% | 72.0356% |
| Profit factor | 1.0906 | 0.9346 | 0.8898 |
| Expectancy per day | +$13.85 | -$11.65 | -$20.87 |
| Best day | $1,070.24 | $1,165.24 | $1,325.24 |
| Worst day | -$3,929.76 | -$4,674.76 | -$3,339.76 |
| Fees | $9,678.28 | $9,654.00 | $9,668.76 |
| Slippage | $9,905.00 | $9,875.00 | $9,885.00 |

## Interpretation

The 16D/6D iron condor is the first 0DTE configuration tested in this benchmark set with a clearly positive full-sample result and a positive risk-adjusted result: +14.01% total return, 0.419 Sharpe, 1.091 profit factor, and -9.14% maximum drawdown.

That result is materially better than the corresponding 16D/6D one-sided put and call verticals in the same preview framework. However, this is a structural observation, not a deployment conclusion. The 20D/10D and 25D/15D condors both lost money, so widening the short strikes toward higher delta did not preserve the result.

The high win rate remains important but insufficient on its own. The 16D/6D condor still had a worst day of approximately -$3,930 on a $100,000 preview basis, and its reported costs were approximately $19,583 combined fees plus slippage.

## Current 0DTE structural picture

Across the three completed benchmark families:

- **16D/6D put credit spread:** +1.04% total return, 0.072 Sharpe, -16.57% max drawdown.
- **16D/6D call credit spread:** -18.01% total return, -0.650 Sharpe, -19.50% max drawdown.
- **16D/6D iron condor:** +14.01% total return, 0.419 Sharpe, -9.14% max drawdown.
- **20D and 25D variants:** generally deteriorated across all three families, with the notable exception that the 20D/10D and 25D/15D condors still provide useful controls for determining whether the apparent 16D/6D result is robust to delta changes.

This makes the 16D/6D condor a particularly important **research control**, but not a chosen production strategy. The next test should determine whether its result survives different exit timing, chronological validation, volatility/regime stratification, and realistic small-account constraints.

## Critical limitations

1. These are $100,000 platform previews, not $2,000 account results.
2. The benchmark uses one fixed entry time and one fixed 50% profit target/time exit.
3. No conclusion about account feasibility, buying power, portfolio allocation, or broker fills follows from these results.
4. The platform's reported slippage and fee treatment must be independently audited before relying on the absolute P/L.
5. The result is full-sample historical performance. It has not yet passed chronological train/validation/holdout testing.
6. This benchmark does not implement the full tastytrade/tastylive 0DTE research/methodology set.

## Next test

The next frozen experiment is a **management-timing matrix** using the same structures rather than searching for more favorable strikes:

- Put credit spreads: 16D/6D, 20D/10D, 25D/15D.
- Call credit spreads: 16D/6D, 20D/10D, 25D/15D.
- Iron condors: 16D/6D, 20D/10D, 25D/15D.
- Entry fixed at 09:35.
- 50% profit target fixed.
- Time exits tested at approximately 90 minutes, noon, early afternoon, 15:00, and 15:55.
- Identical platform, cost, and historical window for every cell.

After that matrix, the surviving structures should be evaluated against historical volatility/regime labels and then through the $2,000/$5,000/$10,000 feasibility gate.

## Reproducibility

Source file: `0dte_iron_condor_benchmark.json`.

The supplied JSON contains three platform source hashes; preserve them when comparing future reruns.
