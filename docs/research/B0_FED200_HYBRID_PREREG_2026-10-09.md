# B0 + Fed-Hike / 200-DMA State Modifier — Preregistration (2026-10-09)

## Hypothesis

The simple 250-DMA overlay materially reduced modern actual-TQQQ ending wealth and failed its preregistered gate. This experiment tests a narrower state modifier: preserve B0's shock/recovery exits, but reduce exposure only when QQQ is below its 200-session DMA and the Fed target rate is at least 0.25 percentage point higher than 126 QQQ trading sessions earlier. This targets a tightening-cycle risk state rather than every below-DMA period.

This is exploratory, not independent confirmation. The Fed rate event table is the existing frozen series in `research/tqqq_three_layer_event_attribution.py`; no new data source is introduced.

## Frozen rule

B0 remains the control:
- QQQ adjusted-close daily return <= -4.5% sets target exposure to 0.
- While defensive, restore exposure after a 10% rebound from the running low.
- Signals known at close execute at the next open.

The modifier state at close is true only when both conditions hold:
1. QQQ adjusted close is below its 200-session moving average.
2. Fed target rate now minus the target rate 126 QQQ sessions earlier is at least 0.25 percentage point.

For each fixed exposure p in {50%, 75%}: if B0 target is 0, the candidate stays at 0; if B0 target is 1 and the modifier state is true, target exposure is p; otherwise retain B0 target exposure. Candidates are `B0_FED200_50` and `B0_FED200_75`. Do not add other rate thresholds, lookback lengths, DMA lengths, or exposure levels after seeing results.

## Evaluation and execution

- Start balance: $5,000 per strategy.
- Synthetic daily-reset 3x QQQ proxy: QQQ adjusted-price input from 1999-03-10 through 2026-10-02; evaluation begins after the shared 250-session warm-up (2000-03-03). Use the corrected synthetic overnight/intraday return helper and shared causal execution engine.
- Actual TQQQ: evaluation window 2011-02-07 through 2026-10-02, after the same 250-session warm-up from TQQQ inception. Fed/QQQ signals use the full QQQ history and are aligned to actual TQQQ dates.
- Cost stress: 0, 10, 25, and 50 basis points per executed exposure change, using the shared causal cost engine.
- Report terminal balance, CAGR, max drawdown, worst rolling 252-session return, minimum equity/date, average target exposure, exposure changes, synthetic first crossings of -99%/-99.9% drawdown and zero, plus 2020 and 2022 window returns.
- All comparisons within each sample use the same frozen QQQ/TQQQ input and evaluation dates.

## Fixed decision gate

A candidate is eligible for chronological holdout testing only if, at 10 bps, all four conditions hold:
1. Actual-TQQQ ending balance is at least 90% of B0.
2. Actual-TQQQ max drawdown improves by at least 3 percentage points versus B0.
3. Synthetic ending balance is at least 90% of B0 on the common synthetic window.
4. Synthetic max drawdown improves by at least 3 percentage points versus B0.

If neither candidate passes, reject this family without adjusting the rate lookback, threshold, DMA, or exposure levels after seeing results. Passing the full sample is not sufficient for deployment; any candidate that passes must still complete chronological holdout/walk-forward validation and review 2020 rebound retention and 2022 performance before paper trading.

## Limitations

- Fed rate history is a hand-maintained event table, not a live economic-data feed; verify dates and values before deployment.
- Synthetic pre-inception returns are not actual TQQQ and omit fees, financing, tracking error, and brokerage-specific execution.
- No candidate is approved for paper or live trading by this experiment.
