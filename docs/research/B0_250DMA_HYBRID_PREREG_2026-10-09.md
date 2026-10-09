# B0 + 250-DMA Partial-Exposure Hybrid — Preregistration (2026-10-09)

## Why this experiment exists

The corrected synthetic common-window matrix found that a pure 250-DMA rule with 25% exposure below the DMA had higher ending wealth and lower drawdown than B0 on the 2000-03-03 to 2026-10-02 synthetic proxy window. On actual TQQQ over 2011-02-07 to 2026-10-02, the same pure DMA rule ended far below B0. This hybrid tests a narrower hypothesis: preserve B0's shock/recovery cash exits and apply the 250-DMA exposure reduction only when B0 otherwise wants to be invested. The 250-DMA choice is informed by prior in-sample grid results, so this is exploratory and not independent confirmation.

## Frozen candidate definitions

Let B0 target exposure be the preregistered QQQ shock/recovery rule:
- Exit target exposure to 0 after a QQQ adjusted-close daily return <= -4.5%.
- While defensive, restore exposure after a 10% rebound from the running low.
- Signal at close executes at the next open.

For each fixed below-DMA exposure (p in {25%,50%,75%}), define the hybrid target at close (t):
- If B0 target is 0, hybrid target remains 0 regardless of the DMA.
- If B0 target is 1 and QQQ adjusted close is at or above its 250-session DMA, target remains 100%.
- If B0 target is 1 and QQQ adjusted close is below its 250-session DMA, target is (p).
- No other gates, re-entry delays, thresholds, or discretionary exceptions.

Candidates are named `B0_250DMA_25`, `B0_250DMA_50`, and `B0_250DMA_75`. B0 remains the control. A pure 250-DMA/25% strategy is retained as a diagnostic reference, not a candidate for promotion.

## Evaluation windows and execution

- Starting balance: $5,000 per strategy.
- Synthetic daily-reset 3x QQQ proxy: 1999-03-10 through 2026-10-02 input; common evaluation starts after the 250-session lookback, on the first session where the 250-DMA is defined. All strategies use the same frozen QQQ input, corrected daily-reset leverage legs, and `research/causal_execution.py`.
- Actual TQQQ: 2010 inception-era data, common evaluation window 2011-02-07 through 2026-10-02 after the 250-session warm-up. B0 signals use QQQ history available before evaluation; each candidate starts with $5,000 on the common evaluation start.
- Actual TQQQ overnight/intraday returns are measured from the fund's adjusted open/close. Synthetic proxy legs use the corrected shared helper: overnight exposure is 3x, while intraday leverage adjusts for the overnight gap so the two legs compound to 3x QQQ's close-to-close daily return when neither leg is clipped at a total loss.
- Cost stress: 0, 10, 25, and 50 basis points per executed exposure change, using the shared causal cost engine. No cash yield, tax, margin interest, or additional market-impact model.
- Report ending balance, CAGR, max drawdown, worst rolling 252-session return, minimum equity/date, average exposure, exposure changes, synthetic first crossings of -99%/-99.9% drawdown and zero, plus 2020 and 2022 window returns. The same candidate/date/cost conventions apply across strategies.

## Decision gate (fixed before results)

A hybrid is eligible for further chronological holdout testing only if, at **10 bps**:
1. Actual-TQQQ ending balance is at least 90% of B0's ending balance;
2. Actual-TQQQ max drawdown improves by at least 3 percentage points versus B0;
3. Synthetic ending balance is at least 90% of B0's common-window ending balance; and
4. Synthetic max drawdown improves by at least 3 percentage points versus B0.

These are joint gates; passing only one sample is not enough. If no candidate passes all gates, reject the hybrid family without adjusting the 250-DMA or exposure levels after seeing results. If one or more pass, do not select a winner from the full sample; require chronological holdout/walk-forward validation and inspect 2020 rebound retention and 2022 losses before any paper-trading decision.

## Known limitations

- The synthetic pre-TQQQ series is not actual TQQQ and does not model fund fees, financing, tracking error, or brokerage-specific fills.
- The 250-DMA was surfaced by prior in-sample matrix results; the test is therefore exploratory and may be subject to selection bias.
- Historical terminal balances do not imply future returns. No candidate is approved for live deployment by this experiment.
