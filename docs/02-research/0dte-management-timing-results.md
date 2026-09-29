# 0DTE Management-Timing Matrix Results

**Status:** Completed, preliminary research result  
**Source:** 0DTESPX strategy-preview runs via GitHub Actions  
**Workflow run:** 36527403745  
**Historical window:** 2022-06-16 through 2026-09-28  
**Sessions:** 1,012 per configuration  
**Starting capital:** $100,000 per platform preview  
**Entry:** 09:35 ET  
**Profit target:** 50%  
**Time exits:** 11:05, 12:00, 13:30, 15:00, 15:55  
**Configurations:** 45

## Purpose

This was a frozen management-timing experiment. Strike deltas and structure were held constant while only the mechanical time exit changed.

## Key results

| Structure / delta | 11:05 | 12:00 | 13:30 | 15:00 | 15:55 |
|---|---:|---:|---:|---:|---:|
| Put 16D/6D | -9.80% | -13.46% | -9.15% | +0.46% | **+1.04%** |
| Put 20D/10D | -11.07% | -14.98% | -15.31% | -10.17% | -15.65% |
| Put 25D/15D | -16.39% | -19.23% | -20.80% | -12.94% | -18.92% |
| Call 16D/6D | -21.16% | -22.31% | -18.49% | -17.99% | -18.13% |
| Call 20D/10D | -21.29% | -21.68% | -18.53% | -21.55% | -25.88% |
| Call 25D/15D | -18.08% | -18.38% | -18.55% | -27.35% | -29.01% |
| IC 16D/6D | -7.89% | -13.35% | -4.47% | +7.11% | **+14.01%** |
| IC 20D/10D | -11.17% | -17.54% | -13.65% | -6.11% | -12.18% |
| IC 25D/15D | -11.06% | -15.09% | -19.11% | -10.88% | -21.43% |

## 16D/6D iron condor, 15:55 control

- Ending NLV: **$114,014.72**
- Total return: **+14.01%**
- Annualized Sharpe: **0.419**
- Annualized Sortino: **0.152**
- Maximum drawdown: **-9.14%**
- Win rate: **86.56%**
- Profit factor: **1.091**
- Expectancy: **+$13.85/day**
- Best day: **+$1,070.24**
- Worst day: **-$3,929.76**
- Fees: **$9,678.28**
- Slippage: **$9,905.00**

This reproduces the earlier 15:55 iron-condor benchmark, which is useful as an internal consistency check.

## Main findings

### 1. Exit timing is a major strategy dimension

For the 16D/6D iron condor, the result changed from negative at all three early exits to positive at 15:00 and 15:55. The corresponding Sharpe ratios were approximately -0.390, -0.508, -0.123, +0.252, and +0.419.

The timing choice therefore cannot be treated as a cosmetic implementation detail.

### 2. The result is concentrated in the lowest tested delta pair

The 20D/10D and 25D/15D iron condors were negative at every tested exit. The 16D/6D iron condor was positive only at 15:00 and 15:55.

The same general delta sensitivity appears in the one-sided spreads.

### 3. Calls were negative across the entire matrix

Every call-credit configuration lost money over the full sample. This does not prove that call spreads can never be useful; it shows that these frozen variants did not produce a positive full-sample result in this historical window.

### 4. Earlier exits did not automatically reduce drawdown

For the 16D/6D iron condor, maximum drawdown was approximately:

- 11:05: -18.57%
- 12:00: -22.05%
- 13:30: -17.30%
- 15:00: -12.02%
- 15:55: -9.14%

So simply exiting earlier did not produce lower historical drawdown in this test.

### 5. Tail losses remain the dominant risk

The strongest cell still experienced a roughly **-$3,930** day on a $100,000 preview. Its average daily expectancy was only about **+$13.85**.

The high win rate therefore cannot be treated as the primary quality signal.

## Calendar-year behavior of the 16D/6D 15:55 iron condor

| Year | Ending NLV | Return vs. prior year-end |
|---|---:|---:|
| 2022 | $95,930.72 | -4.07% |
| 2023 | $97,214.24 | +1.34% |
| 2024 | $96,021.12 | -1.23% |
| 2025 | $106,324.44 | +10.73% |
| 2026* | $114,014.72 | +7.23% |

*2026 is partial through 2026-09-28.

The positive full-sample result was therefore not smooth across calendar years. Chronological validation is essential.

## Multiple-testing warning

There are 45 related hypotheses in this matrix. The best full-sample cell will naturally benefit from selection across many candidates.

Therefore the +14.01% result is **not an out-of-sample claim** and is not a production selection.

The candidate set must now be frozen before chronological validation. Further optimization on the same full sample would increase selection bias.

## Next research sequence

1. Freeze a small candidate/control set rather than optimizing more cells on the full sample.
2. Run chronological train/validation/holdout testing.
3. Condition performance on volatility/VIX and market-direction regimes.
4. Test bounded loss-management rules.
5. Stress fees and slippage.
6. Replay survivors at $2,000, $5,000, $10,000, and $20,000 with the project's account-level risk gates.
7. Compare the surviving option candidate against the leveraged-ETF strategy as a regime-dependent portfolio component.
8. Keep 0DTE research-only until account feasibility, out-of-sample behavior, and execution safety are separately validated.

## Reproducibility

Artifact: `0dte-timing-matrix-36527403745`  
Artifact SHA-256: `fd827598119f17395719f42dc540357fae22ea36726bc4590a628fc9e2fbd926`

The repository also contains `tools/0dte/analyze_timing_matrix.py` for repeatable analysis of the sanitized JSON.
