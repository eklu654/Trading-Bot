# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery strategy's slow-bear weakness justifies a structural overlay while protecting terminal wealth.  
**Starting capital:** $5,000.

## User's direction

Start from the reproducible ~$4.04M candidate and organically let evidence establish strengths, weaknesses, and whether any overlay is warranted. Do not block progress on reconstructing the separate historical ~$3.3M anti-fakeout strategy.

## Frozen baseline

**Rule ID:** `qqq_shock45_recovery10_actual_tqqq_v1`

- Signal: QQQ adjusted-close daily return <= -4.5%.
- Defense: target 0% TQQQ exposure from the next open after the trigger close.
- Recovery: track post-trigger adjusted-close low; re-enter at next open after a close is >=10% above that low.
- Otherwise hold 100% TQQQ.
- Accounting: overnight return belongs to the position held before open execution; intraday return belongs to the position after open execution.
- No DMA, Fed, MACD, golden-cross, macro, inverse ETF, or AI filter is part of the baseline.
- $5,000 initial equity; actual-TQQQ window 2010-02-11 through 2026-10-07.

Every candidate comparison keeps this baseline unchanged.

## Baseline verification and modern stress results

- Same-input daily curve reconciliation passed: [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Shared and independent engines matched every daily return/equity value and all nine events.
- Frozen input SHA-256: `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.
- Same-input baseline: **$4,040,313.79**, CAGR 49.49%, max DD -73.53%; TQQQ buy-and-hold **$2,094,668.95**, CAGR 43.70%, max DD -81.66%.
- Reports: [first stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md) and [stress windows / slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md).
- Period returns independently compounded within each window: 2010–14 baseline +895.0% vs buy-hold +865.3%; 2015–19 +569.6% vs +434.0%; 2020–21 +325.6% vs +284.4%; 2022–24 +42.3% vs -1.4%; 2025–2026-10-07 +100.2% vs +114.4%.
- Main weakness: QQQ fell -15.6% in 2010 and -16.1% in early 2016 without a -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% drawdown episode began.

## Candidate 1 — Fed-paused × below 200-DMA: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- Ending wealth fell ~28% versus baseline and max drawdown did not improve. It fired only during brief 2016/2019 corrections and missed 2022 entirely.

## Fed-state attribution

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- 2022 drawdown began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; first shock was 2022-05-05. TIGHTENING_PAUSED began only 2023-10-26, after QQQ reclaimed the 200-DMA.

## Candidate 2 — Fed-active × below 200-DMA: PARTIAL-EXPOSURE TRADE-OFF

- Binary test: [run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946); [result report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md).
- Exposure sensitivity: [run 37886436961](https://github.com/eklu654/Trading-Bot/actions/runs/37886436961); [report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_EXPOSURE_SENSITIVITY_2026-10-09.md).
- Rule: enter when QQQ is below the existing 200-DMA and previous-session Fed state is TIGHTENING_ACTIVE; exit when QQQ closes at/above the 200-DMA. Baseline shock defense independently overrides to 0%.
- Same-run ending balances: baseline $4.040M; 0% overlay exposure $3.675M; 25% $3.933M; 50% $4.087M; 75% $4.125M; buy-and-hold $2.095M.
- 50% overlay exposure ends ~$47k above baseline while improving max DD from -73.53% to -61.19% and worst rolling 252-session return from -72.64% to -59.88%.
- 75% overlay exposure ends ~$84k above baseline while improving max DD to -67.65% and worst rolling-year return to -66.56%.
- 2022 calendar loss: -69.83% baseline, -57.21% at 50% overlay exposure, -63.73% at 75%.
- The main opportunity cost is 2018–2019 trend chop. Leave-one-episode-out counterfactuals show the 2018-12-04 to 2019-02-04 episode conditionally cost ~$794k at 0% overlay exposure because it stayed defensive after the baseline's 2019-01-07 recovery decision. The 2022-04-05 to 2023-01-25 episode conditionally contributed ~$1.50M at 0% overlay exposure. Conditional effects are not additive.
- 50% and 75% remain working comparison candidates, not selected or validated. This is in-sample development evidence.

## Candidate 3 — Existing macro-regime overlay: REJECTED for current slow-bear objective

- Workflow: [37886806226](https://github.com/eklu654/Trading-Bot/actions/runs/37886806226).
- Report: [actual-TQQQ macro overlay result](CANONICAL_SHOCK_RECOVERY_MACRO_OVERLAY_RESULT_2026-10-09.md).
- Existing frozen classifier applied to actual TQQQ with an additional conservative month-start availability lag. Ending balances: baseline $4.040M; macro-light $3.308M; macro-medium $2.706M; macro-hard $2.180M.
- All variants retained the baseline's -73.53% max drawdown and -72.64% worst rolling-year return. The classifier stayed STRUCTURAL_EXPANSION through 2022 and failed to detect the target bear. It reduced wealth without solving the main failure mode.

## Historical signal-only audit

- Workflow: [37887083424](https://github.com/eklu654/Trading-Bot/actions/runs/37887083424).
- Report: [historical signal-only stress audit](CANONICAL_SHOCK_RECOVERY_HISTORICAL_SIGNAL_AUDIT_2026-10-09.md).
- S&P 500 proxy: the 1973–1974 episode fell ~48.2% peak-to-trough without any -4.5% daily-shock trigger. The 1987 episode did trigger, eight sessions after the -5% episode start.
- QQQ signal-only: the 2000–2002 dot-com bear fell ~83.0% peak-to-trough. The daily shock/recovery rule fired repeatedly. The Fed-active × 200-DMA condition activated only intermittently early in the decline and did not remain defensive through the full bear as the Fed state shifted to EASING.
- These are signal/index diagnostics, not TQQQ returns. No actual TQQQ result is claimed before its inception.

## Next actions

1. Keep the compact actual-TQQQ comparison set: baseline, Candidate 2 at 50% overlay exposure, and Candidate 2 at 75% overlay exposure. Keep 0%/25% as sensitivity points.
2. Freeze the comparison and write down a chronological validation protocol. The entire modern sample has already been inspected; no historical slice can now be called an untouched holdout. Any future rule change becomes a development candidate and requires a future untouched holdout.
3. Use historical signal-only studies to understand whether these rules would have recognized prior regimes, but do not convert proxy signals into actual TQQQ performance.
4. Do not change the 200-DMA exit rule after seeing the 2018 result and then call it validated. The missed 2019 recovery is a known trade-off to assess, not an automatic reason to optimize.
5. No broad indicator fishing, DMA-length sweep, re-entry-delay search, AI layer, or paper trading yet.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** comparison anchor or candidate, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Candidate 2 at 50%/75% overlay exposure is **WORKING TRADE-OFF, NOT SELECTED**. Numerical reproduction is supported; generalization across major downturn types remains unresolved.

## Validation protocol frozen — 2026-10-09

- Protocol: [canonical shock/recovery validation protocol](CANONICAL_SHOCK_RECOVERY_VALIDATION_PROTOCOL_2026-10-09.md), committed at `fa3e491cf973ca680ea869c4664cf63ef516fd28`.
- The protocol formalizes the unchanged B0 baseline, F50 and F75 development candidates, F00/F25 sensitivity controls, data/causality assertions, required cost and segment scorecards, candidate gates, and what does/does not count as out-of-sample evidence.
- Critical honesty rule: the full 2010–2026 sample has already been inspected. Historical subperiods are retrospective stability diagnostics, not untouched holdouts. Only a genuinely frozen prospective test can become new out-of-sample evidence.
- Candidate advancement gates: at least 95% of baseline ending wealth after 25 bp exposure-change costs; at least 5 percentage points improvement in max drawdown and worst rolling 252-session return; no material unaccounted deterioration in COVID/2018 windows; and evidence the benefit is not entirely one episode.
- No candidate selected. B0 remains WORKING CONTROL; F50/F75 remain WORKING DEVELOPMENT CANDIDATES; the existing macro classifier remains REJECTED for the current objective. AI and paper trading remain deferred.
- Next engineering task: a single workflow/run that freezes one aligned QQQ/TQQQ/Fed input set, runs B0/F50/F75 from it, independently checks causality/accounting, and emits one comparable artifact set. Existing sensitivity output is useful, but its market-input hash differs from the canonical baseline hash; do not describe its dollar figures as exact same-input comparisons until that is reconciled.

