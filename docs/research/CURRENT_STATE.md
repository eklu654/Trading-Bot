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
- [First stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md).
- [Stress windows and slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md).
- Period returns independently compounded within each window: 2010–14 baseline +895.0% vs buy-hold +865.3%; 2015–19 +569.6% vs +434.0%; 2020–21 +325.6% vs +284.4%; 2022–24 +42.3% vs -1.4%; 2025–2026-10-07 +100.2% vs +114.4%.
- The baseline's ~73.5% max drawdown is severe. QQQ drawdown episodes reached -15.6% in 2010 and -16.1% in early 2016 without a -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% episode start.

## Candidate 1 — Fed-paused × below 200-DMA overlay: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA overlay result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- Enter sticky defense when QQQ is below 200-DMA and previous-session Fed state is TIGHTENING_PAUSED; exit when QQQ closes at/above 200-DMA.
- Result: $2,908,571 vs baseline $4,040,316 on that run's common data; CAGR 46.57% vs 49.49%; max DD unchanged at -73.53%.
- It triggered six brief episodes in 2016/2019, missed 2022 entirely, and did not change COVID/2025 exposure. It sacrificed about 28% of ending wealth without reducing max DD.
- This rejects the paused-only rule, not all Fed hypotheses.

## Fed state attribution: completed diagnostic

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution around baseline drawdowns](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- Input hash: `b3a52cf47af93a200abf0b79efe37007d8ec6c591aae48b1cd759df8fff9bbf5`.
- 2022 drawdown began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; first -4.5% shock was 2022-05-05. TIGHTENING_PAUSED began only 2023-10-26, after QQQ had reclaimed the 200-DMA.
- TIGHTENING_ACTIVE was also present in early 2016 and 2018, making an active-state overlay plausible for 2022 but vulnerable to false positives.

## Candidate 2 — Fed-active × below 200-DMA overlay: WORKING TRADE-OFF, NOT SELECTED

- Workflow: [37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946).
- Report: [Active-tightening overlay result](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md).
- Rule: enter sticky defense when QQQ is below the existing 200-DMA and previous-session Fed state is TIGHTENING_ACTIVE; exit when QQQ closes at/above the 200-DMA. Baseline shock/recovery defense remains active independently.
- Same-run results: baseline **$4,040,313**, candidate **$3,674,919**, buy-and-hold **$2,094,669**. Candidate gives up ~$365k (~9.0%) versus baseline, but improves max DD from -73.53% to -57.34% and worst rolling 252-session return from -72.64% to -47.11%.
- 2022 calendar loss improves from -69.83% to -43.68%; 2022–2024 period return improves from +42.3% to +82.6%, with local max DD improving from -72.6% to -53.4%.
- The candidate's clear weakness is 2018–2019 trend-chop: its repeated entries/exits cost terminal wealth. It did not change COVID or 2025 exposure because those periods were labeled EASING.
- This is a real trade-off, not a winner. The baseline remains the primary growth control; Candidate 2 remains a comparison candidate because it materially improves the measured 2022 loss and rolling-year worst return.

## Next actions

1. **Do not add another indicator or tune thresholds yet.** Diagnose the active overlay's 2018–2019 false-positive transitions and the 2022 defense interval from its event ledger; establish exactly which rebounds were missed and how much terminal wealth each episode cost.
2. Keep only two active candidates: unchanged baseline and Candidate 2. Compare their inherited equity and exposure through 2016, 2018–2019, 2022, COVID, and 2025; report terminal wealth and stress protection together.
3. The full-sample candidate was developed after inspecting those episodes; they are **not an untouched holdout**. Any rule changed from these findings requires a new future chronological holdout. Do not call it validated or live-approved.
4. After the false-positive diagnosis, test the already-frozen macro state as a separate hypothesis only if it addresses a documented failure not covered by the two current candidates. No broad indicator fishing, DMA-length sweep, re-entry-delay search, AI layer, or paper trading yet.
5. Keep actual TQQQ results separate from synthetic pre-2010 proxies; never use future outcome labels to determine whether signals trade.

## Historical study boundaries

- Pre-2010 (1970s, 1987, 2000–2002) is signal-only index analysis unless a leveraged proxy is explicitly synthetic. TQQQ did not exist.
- The old ~$3.3M anti-fakeout variant is a separate historical rule and no longer blocks progress.
- The separate synthetic ~$3.7M Fed/DMA study and extraordinary synthetic-wealth outputs are not evidence of actual-TQQQ results.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** current comparison anchor or candidate, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Candidate 2 is **WORKING TRADE-OFF, NOT SELECTED**. Numerical reproduction is supported; generalization across major downturn types remains unresolved.
