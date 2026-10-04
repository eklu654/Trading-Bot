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

- immediate/0: **$365,195**, -50.01% DD
- 1-session: **$365,195**, -50.01% DD
- 3-session: **$369,948**, **-48.14% DD**
- 5-session: **$306,150**, **-48.14% DD**
- 10-session: **$158,114**, -50.62% DD
- 15-session: **$114,603**, -52.11% DD
- 20-session: **$75,443**, -49.10% DD

Thus 5 sessions is clearly not something we should have assumed. In this sample, **3 sessions dominates 5 sessions for the 200-DMA configuration** on both terminal wealth and maximum drawdown.

### 2. The best terminal-wealth trend configuration was 225-DMA with immediate re-entry

It produced about **$380k from $5k**, with a **49.96% maximum drawdown**.

The 200-DMA/3-session configuration was extremely close at about **$370k**, while improving maximum drawdown to **48.14%**.

This makes the 200-DMA/3-session configuration a particularly important challenger because it is near the terminal-wealth frontier while having the best drawdown observed in the top group.

### 3. Re-entry delay has a highly nonlinear effect

Longer confirmation is not monotonically safer or better.

Examples:

- 200-DMA: 3 sessions → **$370k**, 5 → **$306k**, 10 → **$158k**, 20 → **$75k**.
- 250-DMA: immediate → **$204k**, 5 → **$329k**, 10 → **$317k**, 20 → **$196k**.
- 150-DMA: immediate → **$254k**, 3 → **$152k**, 10 → **$109k**.

Therefore re-entry timing interacts strongly with the DMA window. It must be optimized/researched jointly, not independently.

### 4. 0 and 1 session are currently identical

The implementation records 0 as immediate and 1 as one-session confirmation, but under the prior-close signal convention they produce identical paths in this test. This is an implementation/timing consequence, not evidence that two economically different strategies have independently tied.

### 5. Buy-and-hold remains the terminal-wealth control

On this TQQQ-specific period, buy-and-hold turns **$5,000 into approximately $1.974 million**, versus roughly $380k for the strongest DMA configuration. The DMA controls therefore sacrifice substantial historical terminal wealth in exchange for substantially lower maximum drawdown.

That does **not** mean buy-and-hold should automatically be selected. It means the defensive value of the DMA exit must be evaluated explicitly against the wealth sacrificed.

## Current research interpretation

The most interesting TQQQ candidates emerging from this grid are:

1. **225-DMA + immediate/1-session**
2. **200-DMA + 3-session**
3. **250-DMA + 5-session**
4. **250-DMA + 10-session**
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

