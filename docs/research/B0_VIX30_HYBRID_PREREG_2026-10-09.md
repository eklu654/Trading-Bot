# B0 + VIX-30 Exposure Modifier — Preregistration (2026-10-09)

## Hypothesis

The Fed-hike/200-DMA modifier improved actual-TQQQ drawdown and 2022 losses but did not improve the corrected synthetic near-ruin tail. This experiment tests a distinct, directly observable volatility state: when VIX closes at or above 30, reduce exposure only if B0 otherwise wants to be invested. B0's own cash exits remain authoritative.

The threshold 30 is fixed before running this experiment; no 28/30/35 threshold sweep is allowed. This is exploratory and not independent confirmation.

## Frozen rule

B0 remains the control:
- QQQ adjusted-close daily return <= -4.5% sets target exposure to 0.
- While defensive, restore exposure after a 10% rebound from the running low.
- Signals known at close execute at the next open.

For each fixed p in {50%, 75%}:
- If B0 target is 0, the candidate stays at 0.
- If B0 target is 1 and VIX close is >= 30, target exposure is p.
- Otherwise retain B0 target exposure.

Candidates are `B0_VIX30_50` and `B0_VIX30_75`. Do not add other VIX thresholds, exposure levels, DMA gates, or re-entry delays after seeing results.

## Evaluation and execution

- Start balance: $5,000 per strategy.
- Synthetic daily-reset 3x QQQ proxy: QQQ and VIX input from 1999-03-10 through 2026-10-02; common evaluation begins after the 250-session warm-up (2000-03-03). Use the corrected synthetic overnight/intraday return helper and shared causal execution engine.
- Actual TQQQ: evaluation window 2011-02-07 through 2026-10-02, after the same 250-session warm-up from TQQQ inception. VIX/QQQ signals use the close and execute next open.
- Cost stress: 0, 10, 25, and 50 basis points per executed exposure change, using the shared causal cost engine.
- Report terminal balance, CAGR, max drawdown, worst rolling 252-session return, minimum equity/date, average target exposure, exposure changes, synthetic first crossings of -99%/-99.9% drawdown and zero, plus 2020 and 2022 window returns.
- Each sample's strategies use the same frozen inputs and evaluation dates. VIX values are aligned to QQQ sessions and forward-filled only over missing dates; no future VIX observations are used.

## Fixed decision gate

A candidate is eligible for chronological holdout testing only if, at 10 bps, all four conditions hold:
1. Actual-TQQQ ending balance is at least 90% of B0.
2. Actual-TQQQ max drawdown improves by at least 3 percentage points versus B0.
3. Synthetic ending balance is at least 90% of B0 on the common synthetic window.
4. Synthetic max drawdown improves by at least 3 percentage points versus B0.

If neither candidate passes, reject this VIX-30 family without adjusting the threshold or exposure levels after seeing results. Passing the full sample is not sufficient for deployment; any candidate that passes must still complete chronological holdout/walk-forward validation and review 2020 rebound retention and 2022 performance before paper trading.

## Limitations

- VIX is an index, not an investable asset. Vendor history, closing timestamps, and any missing-value handling must be audited.
- Synthetic pre-inception returns are not actual TQQQ and omit fees, financing, tracking error, and brokerage-specific execution.
- No candidate is approved for paper or live trading by this experiment.
