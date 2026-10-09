# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery strategy's slow-bear weakness justifies a structural overlay, while protecting terminal wealth.  
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
- The baseline's ~73.5% max drawdown is severe. QQQ drawdown episodes reached -15.6% in 2010 and -16.1% in early 2016 without a -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% episode start.

## Fed-state attribution

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution around baseline drawdowns](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- 2022 drawdown began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; first -4.5% shock was 2022-05-05. TIGHTENING_PAUSED began only 2023-10-26, after QQQ had reclaimed the 200-DMA.
- TIGHTENING_ACTIVE was also present in early 2016 and 2018, so active-state overlays have both potential benefits and false-positive risk.

## Candidate 1 — Fed-paused × below 200-DMA: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA overlay result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- It reduced ending wealth by about 28% and did not improve max drawdown; it fired only during short 2016/2019 corrections and missed 2022 entirely.

## Candidate 2 — Fed-active × below 200-DMA: EXPOSURE TRADE-OFF

- Binary 0%-exposure test: [run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946), documented in [candidate result report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md).
- Predeclared exposure sensitivity: [run 37886436961](https://github.com/eklu654/Trading-Bot/actions/runs/37886436961), documented in [partial-exposure sensitivity report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_EXPOSURE_SENSITIVITY_2026-10-09.md).
- Frozen rule: enter an overlay when QQQ is below the existing 200-DMA and the previous-session Fed state is TIGHTENING_ACTIVE; exit when QQQ closes at/above the 200-DMA. The baseline shock/recovery defense independently sets exposure to 0%.
- Same-run ending balances: baseline $4,040,315; 0% TQQQ in overlay $3,674,918; 25% TQQQ $3,932,880; 50% TQQQ $4,087,451; 75% TQQQ $4,124,680; buy-and-hold $2,094,669.
- 50% exposure ends ~$47k above baseline and improves max DD from -73.53% to -61.19% and worst rolling 252-session return from -72.64% to -59.88%.
- 75% exposure ends ~$84k above baseline and improves max DD to -67.65% and worst rolling-year return to -66.56%.
- In the 2022 calendar window, losses were -69.83% baseline, -43.68% at 0% overlay exposure, -50.45% at 25%, -57.21% at 50%, and -63.73% at 75%. In 2018 Q4, overlay opportunity cost is substantial, though partial exposure reduces it.
- This family is promising but remains **in-sample development evidence**, not a selected/live-approved strategy. Exposure variants were compared after the relevant history had already been inspected.

## Next actions

1. Diagnose the 2018–2019 false-positive episodes from the candidate's leave-one-overlay-episode-out counterfactual artifact. The longest costly episode was 2018-12-04 to 2019-02-04; quantify exactly how it overlaps the baseline's re-entry and the 2019 rebound.
2. Keep the baseline, 50% overlay, and 75% overlay as the compact comparison set for now. The 0% and 25% variants remain in the report as sensitivity points, not preferred candidates.
3. Do not tweak the exit rule after looking at the 2018 result and then report it as validated. The full historical sample has been inspected; any change creates a new development candidate. A future chronological holdout is required before selection.
4. After documenting the 2018 opportunity-cost mechanism, decide whether to test the existing macro state as a separate, frozen hypothesis. No broad indicator fishing, DMA-length sweep, re-entry-delay search, AI layer, or paper trading yet.
5. Keep pre-2010 signal-only index research separate from actual TQQQ performance; do not use future outcome labels to decide whether a signal trades.

## Historical study boundaries

- Pre-2010 (1970s, 1987, 2000–2002) is signal-only index analysis unless a leveraged proxy is explicitly synthetic. TQQQ did not exist.
- The old ~$3.3M anti-fakeout variant is a separate historical rule and no longer blocks progress.
- Synthetic leveraged wealth results are not actual-TQQQ evidence.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** current comparison anchor or candidate, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Candidate 2 at 50%/75% overlay exposure is **WORKING TRADE-OFF, NOT SELECTED**. Numerical reproduction is supported; generalization across major downturn types remains unresolved.
