# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery strategy's slow-bear weakness justifies a structural overlay while protecting terminal wealth.  
**Starting capital:** $5,000.

## User's current direction

Start from the current reproducible ~$4.04M candidate and organically let evidence establish strengths, weaknesses, and whether any overlay is warranted. Do not block progress on reconstructing the separate historical ~$3.3M anti-fakeout strategy.

## Frozen baseline

**Rule ID:** `qqq_shock45_recovery10_actual_tqqq_v1`

- Signal: QQQ adjusted-close daily return <= -4.5%.
- Defense: target 0% TQQQ exposure from the next open after the trigger close.
- Recovery: track post-trigger adjusted-close low; re-enter at next open after a close is >=10% above that low.
- Otherwise hold 100% TQQQ.
- Accounting: overnight return belongs to the position held before open execution; intraday return belongs to the position after open execution.
- No DMA, Fed, MACD, golden-cross, macro, inverse ETF, or AI filter is part of the baseline.
- $5,000 initial equity; actual-TQQQ comparison window 2010-02-11 to 2026-10-07.

Keep the baseline unchanged in every candidate comparison.

## Baseline verification and stress results

- Same-input daily curve reconciliation passed: [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Shared and independent engines matched every daily return/equity value and all nine events.
- Frozen input SHA-256: `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.
- Same-input baseline: **$4,040,313.79**, CAGR 49.49%, max DD -73.53%; TQQQ buy-and-hold **$2,094,668.95**, CAGR 43.70%, max DD -81.66%.
- Reports: [first stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md) and [stress windows / slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md).
- Period returns independently compounded within each window: 2010–14 baseline +895.0% vs buy-hold +865.3%; 2015–19 +569.6% vs +434.0%; 2020–21 +325.6% vs +284.4%; 2022–24 +42.3% vs -1.4%; 2025–2026-10-07 +100.2% vs +114.4%.
- Baseline max drawdown is severe. QQQ fell -15.6% in 2010 and -16.1% in early 2016 without a -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% episode start.

## Candidate 1 — Fed-paused × below 200-DMA: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA overlay result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- It reduced ending wealth by about 28% and did not improve max drawdown; it fired only during short 2016/2019 corrections and missed 2022 entirely.

## Fed-state attribution

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution around baseline drawdowns](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- 2022 drawdown began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; first -4.5% shock was 2022-05-05. TIGHTENING_PAUSED began only 2023-10-26, after QQQ reclaimed the 200-DMA.

## Candidate 2 — Fed-active × below 200-DMA: PARTIAL-EXPOSURE TRADE-OFF

- Binary 0%-exposure test: [run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946), report [here](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md).
- Predeclared 0/25/50/75% exposure sensitivity: [run 37886436961](https://github.com/eklu654/Trading-Bot/actions/runs/37886436961), report [here](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_EXPOSURE_SENSITIVITY_2026-10-09.md).
- Rule: enter when QQQ is below the existing 200-DMA and the previous-session Fed state is TIGHTENING_ACTIVE; exit when QQQ closes at/above the 200-DMA. The baseline shock/recovery defense independently overrides to 0%.
- Same-run ending balances: baseline $4,040,315; 0% overlay exposure $3,674,918; 25% $3,932,880; 50% $4,087,451; 75% $4,124,680; buy-and-hold $2,094,669.
- 50% overlay exposure ends ~$47k above baseline while improving max DD from -73.53% to -61.19% and worst rolling 252-session return from -72.64% to -59.88%.
- 75% overlay exposure ends ~$84k above baseline while improving max DD to -67.65% and worst rolling-year return to -66.56%.
- The 2022 calendar loss improves from -69.83% baseline to -57.21% at 50% exposure and -63.73% at 75% exposure.
- The principal opportunity cost is 2018–2019 trend chop. Leave-one-episode-out attribution shows the 2018-12-04 to 2019-02-04 overlay episode conditionally cost ~$794k at 0% overlay exposure, as it remained defensive after the baseline's 2019-01-07 recovery decision. The 2022-04-05 to 2023-01-25 episode conditionally contributed about +$1.50M at 0% exposure. These conditional effects are not additive.
- 50% and 75% are retained as working comparison candidates, not selected or validated. Full history has been inspected, so these are development results.

## Candidate 3 — Existing macro-regime overlay: REJECTED for the current slow-bear objective

- Workflow: [37886806226](https://github.com/eklu654/Trading-Bot/actions/runs/37886806226).
- Report: [actual-TQQQ macro overlay result](CANONICAL_SHOCK_RECOVERY_MACRO_OVERLAY_RESULT_2026-10-09.md).
- The existing frozen macro classifier was applied to actual TQQQ with an additional conservative month-start availability lag. Ending balances: baseline $4.040M; macro-light $3.308M; macro-medium $2.706M; macro-hard $2.180M.
- All macro variants retained the baseline's -73.53% max drawdown and -72.64% worst rolling-year return. Crucially, the classifier remained STRUCTURAL_EXPANSION through 2022, so it did not detect the target tightening bear. It reduced wealth without solving the main failure mode.
- This rejects the existing classifier as a baseline overlay, not all possible macro research. Do not combine it with Candidate 2 without evidence.

## Next actions

1. Freeze the compact actual-TQQQ comparison set: unchanged baseline, Candidate 2 at 50% overlay exposure, and Candidate 2 at 75% overlay exposure. Keep 0% and 25% results as sensitivity points.
2. Document the 2018–2019 opportunity-cost mechanism in the current research report: overlay exit/re-entry transitions, the baseline's 2019-01-07 recovery, and the missed rebound until 2019-02-05. Do not alter the exit rule and then call it validated.
3. Run a separate **signal-only historical stress audit** of the frozen baseline and Candidate 2 rule where QQQ exists (2000–2002), and S&P/Nasdaq-proxy signal studies for earlier eras (1987/1970s). Do not report actual TQQQ returns before TQQQ existed; any leveraged proxy must be explicitly synthetic.
4. Because the full modern sample has already been inspected, no historical slice can now be called an untouched holdout. Treat any new rule from these diagnostics as development; require a future chronological holdout before selecting or paper-trading a strategy.
5. No broad indicator fishing, DMA-length sweep, re-entry-delay search, AI layer, or paper trading yet.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** current comparison anchor or candidate, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Candidate 2 at 50%/75% overlay exposure is **WORKING TRADE-OFF, NOT SELECTED**. Numerical reproduction is supported; generalization across major downturn types remains unresolved.
