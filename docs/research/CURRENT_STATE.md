# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Test whether a causally defined Fed tightening × market-trend overlay can address the canonical QQQ shock/recovery strategy's slow-bear weakness without giving away too much terminal wealth.  
**Starting capital:** $5,000.

## User's current direction

Start from the current reproducible ~$4.04M candidate and organically let evidence establish strengths, weaknesses, and whether any overlay is warranted. Do not block progress on recovering the separate historical ~$3.3M anti-fakeout strategy.

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
- [First stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md).
- [Stress windows and slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md).
- Period returns independently compounded inside each window: 2010–14 baseline +895.0% vs buy-hold +865.3%; 2015–19 +569.6% vs +434.0%; 2020–21 +325.6% vs +284.4%; 2022–24 +42.3% vs -1.4%; 2025–2026-10-07 +100.2% vs +114.4%.
- The baseline's ~73.5% max drawdown is severe. QQQ drawdown episodes reached -15.6% in 2010 and -16.1% in early 2016 without any -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% episode start.

## Candidate 1 — Fed-paused × below 200-DMA overlay: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA overlay result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- Rule: enter sticky defense when QQQ is below 200-DMA and the previous session's Fed state is TIGHTENING_PAUSED; exit when QQQ closes back at/above 200-DMA.
- Result: candidate $2,908,571 vs baseline $4,040,316 on the same run's common data; CAGR 46.57% vs 49.49%; max drawdown unchanged at -73.53%.
- It triggered six brief episodes in 2016/2019, missed 2022 entirely, and did not change COVID/2025 exposure. It sacrificed about 28% of ending wealth without reducing max drawdown.
- This rejects this exact paused-only overlay, not all Fed hypotheses.

## Fed state attribution: completed diagnostic

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution around baseline drawdowns](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- Artifact input hash: `b3a52cf47af93a200abf0b79efe37007d8ec6c591aae48b1cd759df8fff9bbf5`.
- The 2022 episode began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; the first -4.5% shock came 2022-05-05. TIGHTENING_PAUSED began only on 2023-10-26, after QQQ had reclaimed the 200-DMA.
- TIGHTENING_ACTIVE was also present during early 2016 and the 2018 bear. This makes an active-tightening × below-200-DMA rule worth one fixed-rule test, but it risks false positives in those earlier periods.
- COVID and 2025 drawdowns were classified EASING; 2010 was NEUTRAL; 2011 was NEUTRAL.

## Next experiment — one frozen candidate only

**Candidate 2:** baseline plus a sticky 0%-exposure overlay that enters when (a) QQQ adjusted close is below its existing 200-session SMA and (b) the one-session-lagged Fed lifecycle state is either TIGHTENING_ACTIVE or TIGHTENING_PAUSED; it exits when QQQ closes at/above the 200-DMA. Baseline shock/recovery defense remains independently active.

- No new DMA lengths, exposure grid, or threshold search.
- Same common market inputs, price fields, execution convention, $5,000 start, and cost model for baseline/candidate/buy-and-hold.
- Report terminal wealth, CAGR, max DD, rolling 12-month worst return, exposure, transitions, and period/window results for 2016, 2018, COVID, 2022, 2025, and 2010 slow correction.
- If the candidate does not show incremental value on ending wealth while addressing the slow-bear miss, reject it and then evaluate the already-frozen macro state as a separate hypothesis.
- Holdout must remain chronological and untouched; no AI layer or paper trading yet.

## Historical study boundaries

- Pre-2010 (1970s, 1987, 2000–2002) is signal-only index analysis unless a leveraged proxy is explicitly synthetic. TQQQ did not exist.
- Future outcome labels are diagnostics only, never inputs to live signal construction.
- The old ~$3.3M anti-fakeout variant is a separate historical rule and no longer blocks progress.
- The separate synthetic ~$3.7M Fed/DMA study and extraordinary synthetic-wealth outputs are not evidence of actual-TQQQ results.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** current comparison anchor, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Numerical reproduction is supported; ability to withstand all major downturn types remains unresolved.
