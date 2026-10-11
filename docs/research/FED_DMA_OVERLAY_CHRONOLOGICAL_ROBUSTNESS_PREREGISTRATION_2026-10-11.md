# Frozen Fed/200-DMA Overlay — Chronological Robustness Protocol

**Registered:** 2026-10-11 UTC  
**Branch:** `research/qqq-slow-bear-audit`  
**Status:** Protocol frozen before the next robustness run; no strategy is selected.

## Question

Does the already-defined Fed-active / QQQ-below-200-DMA partial-exposure overlay retain a defensible wealth/risk trade-off across distinct actual-TQQQ market regimes, or is its apparent full-period benefit concentrated in the 2022 tightening bear?

## Frozen comparison set

No new candidates or thresholds may be added in this run.

1. **B0 control:** unchanged QQQ adjusted-close daily return <= -4.5% exits TQQQ at the next open; re-enter at next open after QQQ closes >=10% above the post-shock low.
2. **F50:** B0 plus 50% TQQQ target while QQQ is below its existing 200-session SMA and the one-session-lagged Fed state is `TIGHTENING_ACTIVE`; remain armed until QQQ closes at/above the 200-DMA. B0's own defense overrides the overlay.
3. **F75:** same state rule, with 75% TQQQ target while armed.

The 0% and 25% variants are not part of the primary comparison; they remain historical sensitivity references only. No AI, new signal, threshold changes, or position-sizing optimization.

## Data, execution, and accounting

- Starting balance: $5,000 for the full-period replay.
- Use the canonical frozen QQQ/TQQQ adjusted input when available; record SHA-256 for all inputs and report the actual date range.
- Signal calculated using information available at close[t]; execute exposure at open[t+1].
- Assign overnight returns to the position held before the open and intraday returns to the position after execution.
- Report 0, 10, 25, and 50 bps per full exposure change. Costs are a sensitivity, not a claim to model all slippage, taxes, spreads, or fills.
- All reported returns are actual-TQQQ-era only. No pre-inception synthetic series is included in this test.

## Chronological windows (fixed, no tuning)

Evaluate inherited-equity returns and local drawdown within each window, without resetting signals or indicators at window boundaries:

- 2010-02-11–2014-12-31: early bull/correction period.
- 2015-01-01–2019-12-31: slow corrections and 2018–2019 rebound / false-positive risk.
- 2020-01-01–2021-12-31: COVID crash and rapid rebound.
- 2022-01-01–2024-12-31: tightening bear and recovery.
- 2025-01-01 through the last common available session: recent regime.
- Whole available period: aggregate reference only; it is not an untouched holdout because this history has already been inspected.

These are descriptive chronological regime checks, not independent statistical samples and not a genuinely untouched out-of-sample test. A candidate chosen after these results must be evaluated prospectively on new data before promotion.

## Required outputs

For B0, F50, and F75, at each cost level and window, report:
- beginning and ending equity, compounded return, local maximum drawdown and peak/trough dates;
- worst rolling 252-session return where the window has enough sessions;
- sessions exposed at 100%, partial exposure, and 0%;
- difference in ending equity and max drawdown versus B0;
- performance during the fixed 2018-12-04–2019-03-29 recovery-risk window, 2020-02-19–2020-08-31 crash/rebound window, and 2022-01-03–2023-12-29 tightening window.

Also record input hashes, code commit, workflow run, and pass/fail status of tests.

## Decision gates (predeclared)

These gates are screening rules, not claims of statistical significance:

1. **No hidden ruin:** no negative/undefined equity and no modeled zero crossing.
2. **Wealth retention:** F50/F75 must retain at least 90% of B0 terminal equity at 25 bps on the full period.
3. **Risk improvement:** at 25 bps, a candidate must improve full-period max drawdown by at least 5 percentage points versus B0, and improve worst rolling 252-session return by at least 5 percentage points.
4. **Regime integrity:** candidate must not underperform B0 by more than 15 percentage points in either the fixed COVID crash/rebound window or the fixed 2018–2019 recovery-risk window. This prevents a good 2022 result from concealing severe recovery damage.
5. **No single-regime claim:** report whether the candidate's incremental ending-equity advantage disappears when the 2022–2024 window is excluded, as a concentration diagnostic only; do not re-fit the strategy to that counterfactual.
6. **Promotion rule:** even if a candidate passes all retrospective gates, it remains research-only. No paper/live promotion without prospective shadow testing and a separate execution/reconciliation review.

If neither F50 nor F75 passes all gates, reject both for promotion and preserve B0 as a research control. Do not relax gates after seeing results.
