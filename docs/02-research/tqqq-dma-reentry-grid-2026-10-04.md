# TQQQ DMA × Re-entry Sensitivity — 2026-10-04

## Purpose

This is the corrected two-dimensional TQQQ trend-control test. It exists specifically to prevent the earlier mistake of treating a 5-session re-entry confirmation as a fixed truth.

## Common test contract

- Starting capital: **$5,000**
- Instrument: **TQQQ**
- Period: **2010-03-11 → 2026-10-02** for every row in this matrix
- Adjusted-close daily returns
- Prior-session signal with next-session return
- Exit when the prior close is below the selected DMA
- Cash earns 0%
- Buy-and-hold is the control
- DMA: **100 / 125 / 150 / 175 / 200 / 225 / 250 / 300**
- Re-entry confirmation: **0 / 1 / 3 / 5 / 10 / 15 / 20 sessions**

This is an apples-to-apples comparison **within the TQQQ experiment**. The later ETF-031 cross-instrument control period begins 2010-03-11, so TQQQ matrix values should not be mixed with cross-instrument terminal values without first re-running the matrix on that common endpoint.

## Headline results

| Strategy | Ending $5k | CAGR | Max DD |
|---|---:|---:|---:|
| TQQQ buy-and-hold | **$1,558,429** | **41.44%** | -81.66% |
| 225-DMA + immediate | **$357,051** | **29.40%** | -49.96% |
| 200-DMA + 3-session | **$329,908** | **28.78%** | **-48.14%** |
| 200-DMA + immediate | **$329,963** | **28.78%** | -50.01% |
| 250-DMA + 5-session | **$368,356** | **29.64%** | -49.73% |
| 250-DMA + 10-session | **$400,921** | **30.31%** | **-48.70%** |
| 200-DMA + 5-session | **$278,890** | **27.48%** | **-48.14%** |
| 300-DMA + 5-session | **$331,574** | **28.82%** | -53.47% |

## What the grid proves

### 1. The old 5-session rule was not uniquely optimal

For 200-DMA:

- immediate/0: **$329,963**, -50.01% DD
- 1-session: **$329,963**, -50.01% DD
- 3-session: **$329,908**, **-48.14% DD**
- 5-session: **$278,890**, **-48.14% DD**
- 10-session: **$144,147**, -50.62% DD
- 15-session: **$100,526**, -52.11% DD
- 20-session: **$70,834**, -49.10% DD

Thus 5 sessions is clearly not something we should have assumed. In this sample, **3 sessions dominates 5 sessions for the 200-DMA configuration** on both terminal wealth and maximum drawdown.

### 2. The best terminal-wealth trend configuration was 225-DMA with immediate re-entry

The strongest terminal-wealth configuration was **250-DMA + 10-session re-entry**, producing about **$400.9k from $5k** with a **48.70% maximum drawdown**.

The 250-DMA + 5-session configuration produced about **$368.4k** with **49.73%** drawdown, while the 200-DMA + 3-session configuration produced about **$329.9k** with **48.14%** drawdown.

This makes the 250-DMA/10-session configuration the current terminal-wealth leader among the tested DMA controls, while 200-DMA/3-session remains an important lower-drawdown challenger.

### 3. Re-entry delay has a highly nonlinear effect

Longer confirmation is not monotonically safer or better.

Examples:

- 200-DMA: 3 sessions → **$330k**, 5 → **$279k**, 10 → **$144k**, 20 → **$71k**.
- 250-DMA: immediate → **$196k**, 5 → **$368k**, 10 → **$401k**, 20 → **$188k**.
- 150-DMA: immediate → **$252k**, 3 → **$150k**, 10 → **$108k**.

Therefore re-entry timing interacts strongly with the DMA window. It must be optimized/researched jointly, not independently.

### 4. 0 and 1 session are currently identical

The implementation records 0 as immediate and 1 as one-session confirmation, but under the prior-close signal convention they produce identical paths in this test. This is an implementation/timing consequence, not evidence that two economically different strategies have independently tied.

### 5. Buy-and-hold remains the terminal-wealth control

On this TQQQ-specific period, buy-and-hold turns **$5,000 into approximately $1.558 million**, versus roughly $401k for the strongest DMA configuration. The DMA controls therefore sacrifice substantial historical terminal wealth in exchange for substantially lower maximum drawdown.

That does **not** mean buy-and-hold should automatically be selected. It means the defensive value of the DMA exit must be evaluated explicitly against the wealth sacrificed.

## Current research interpretation

The most interesting TQQQ candidates emerging from this grid are:

1. **250-DMA + 10-session**
2. **250-DMA + 5-session**
3. **225-DMA + immediate/1-session**
4. **200-DMA + 3-session**
5. **200-DMA + 5-session**

The next test should not blindly select #1 by terminal wealth. The candidates should be subjected to the same return-first survivability analysis already applied to the broader controls: drawdown frequency, minimum equity, dollar drawdown, recovery duration, start-date/rolling robustness, execution sensitivity, and cost sensitivity.

## Important next comparison

The next clean comparison should put these TQQQ candidates beside:

- TQQQ buy-and-hold;
- TQQQ 200-DMA/cash;
- TQQQ 200-DMA/next-open;
- SOXL buy-and-hold;
- SPXL buy-and-hold;
- frozen family rotation;
- and the bull/bear switching challengers.

The common cross-strategy period should be **2010-03-11 → 2026-10-02** when all instruments are required.

