# First 0DTE Historical Benchmark Results

**Status:** Completed, preliminary  
**Source:** User-provided 0DTESPX preview results JSON  
**Strategies:** SPX 0DTE put-credit spreads, entered 09:35, 50% profit target, time exit 15:55  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012 per configuration  
**Platform starting capital:** $100,000 per preview

## Configurations

| ID | Short put delta | Long put delta | Entry | Exit |
|---|---:|---:|---|---|
| PUT_16D_0935_50TP | 0.16 | 0.06 | 09:35 | 50% profit target or 15:55 |
| PUT_20D_0935_50TP | 0.20 | 0.10 | 09:35 | 50% profit target or 15:55 |
| PUT_25D_0935_50TP | 0.25 | 0.15 | 09:35 | 50% profit target or 15:55 |

## Reported results

| Metric | 16-delta | 20-delta | 25-delta |
|---|---:|---:|---:|
| Ending NLV | $101,036.60 | $84,453.60 | $81,170.60 |
| Total return | +1.0366% | -15.5464% | -18.8294% |
| CAGR | +0.2571% | -4.1202% | -5.0622% |
| Annualized Sharpe | 0.0724 | -0.4859 | -0.6467 |
| Annualized Sortino | 0.0177 | -0.1446 | -0.2299 |
| Maximum drawdown | -16.5736% | -22.8967% | -27.9478% |
| Calmar/MAR | 0.0155 | -0.1799 | -0.1811 |
| Win rate | 92.4901% | 89.8221% | 86.5613% |
| Profit factor | 1.0117 | 0.8598 | 0.8422 |
| Expectancy per day | $1.02 | -$15.36 | -$18.61 |
| Best day | $535.12 | $595.12 | $675.12 |
| Worst day | -$4,549.88 | -$5,379.88 | -$4,124.88 |
| Fees | $4,851.40 | $4,856.40 | $4,861.40 |
| Slippage | $9,925.00 | $9,925.00 | $9,925.00 |

## Initial interpretation

- The 16-delta configuration was slightly positive over the tested sample, but the return was small relative to its 16.57% maximum drawdown and near-zero Sharpe. It is not evidence of an attractive or deployment-ready edge.
- The 20- and 25-delta configurations lost 15.55% and 18.83%, respectively, and had negative Sharpe ratios and profit factors below 1.
- All three had high daily win rates, but the average losing day was much larger than the average winning day:
  - 16-delta: average positive day approximately $95.98; average negative day approximately -$1,531.10.
  - 20-delta: average positive day approximately $104.90; average negative day approximately -$1,304.75.
  - 25-delta: average positive day approximately $114.73; average negative day approximately -$1,011.32.
- The 16-delta configuration had 58 losing sessions, 936 winning sessions, and 18 zero-P/L sessions. The 20-delta configuration had 85 losing, 909 winning, and 18 zero-P/L sessions. The 25-delta configuration had 118 losing, 876 winning, and 18 zero-P/L sessions.
- The platform reports $9,925 of slippage for each configuration, in addition to roughly $4,850 of fees. Net results reflect both costs. Cost assumptions must be preserved and independently checked before further interpretation.

## Important limitations

1. These previews use a $100,000 platform starting-capital basis. They do not establish that any configuration is feasible at the intended $2,000 account size, nor do they model the bot's portfolio allocation and buying-power controls.
2. These are single-strategy, one-lot, put-credit-spread tests. They do not test calls, iron condors, butterflies, regime selection, or the combined ETF/options portfolio.
3. The high win rates should not be interpreted without loss size, drawdown, and transaction-cost analysis.
4. The platform results are historical simulations, not live fills or a guarantee of future performance.
5. The tested exit is a simple 50% profit target with a 15:55 time exit. It is not a complete implementation of tastytrade's multi-day management rules, nor should it be represented as a verified tastytrade 0DTE rule set.

## Decision and next tests

**No configuration is approved for live deployment.** The 20- and 25-delta versions should not advance as baseline candidates in their current form. The 16-delta version may remain a comparison/control because it is marginally positive, but it must pass additional validation before any promotion.

Next work, in order:

1. Verify platform fill, fee, and slippage semantics and preserve the exact preview configuration.
2. Analyze daily losses, tail concentration, equity-curve drawdowns, and results by calendar year/regime.
3. Test defined-risk alternatives (including call spreads, iron condors, and butterflies) using a frozen benchmark matrix rather than selecting only the best full-sample result.
4. Evaluate account feasibility at $2,000, $5,000, $10,000, and $20,000 using explicit max-loss and buying-power constraints.
5. Use chronological train/validation/holdout splits and sensitivity tests before considering any strategy for paper deployment.
6. Keep 0DTE as unvalidated for autonomous deployment until execution and operational controls are tested separately.

## Reproducibility

The original sanitized result file was supplied by the user as `0dte_first_benchmark.json`. The three source hashes are:

- 16-delta: `e4c79c46771c777f042d4d1d0377deb36ffba773d3687f264a9c007b675a4f43`
- 20-delta: `8045b16014049746e11dcb67d861251818fb7940c2bd2324f9fe1705315f3e15`
- 25-delta: `5d435f7197258ff45839ff8812f09e419e870535d39994a5752415aff91e3052`
