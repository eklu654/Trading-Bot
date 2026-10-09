# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery TQQQ strategy can withstand both acute V-shaped crashes and gradual/prolonged bear markets.  
**Starting capital:** $5,000.

## User's current direction

Start from the current, reproducible ~$4.04M candidate and let evidence determine its strengths, weaknesses, and whether any overlay is warranted. Do not block progress on reconstructing the separate historical ~$3.3M anti-fakeout strategy. Preserve historical findings as context; do not substitute rules without evidence.

## Frozen working baseline

**Rule ID:** `qqq_shock45_recovery10_actual_tqqq_v1`

- Signal: QQQ adjusted-close daily return <= -4.5%.
- Defense: target 0% TQQQ exposure from the next open after the trigger close.
- Recovery: track the post-trigger adjusted-close low; re-enter after a close is >= 10% above that low, executing at the next open.
- Otherwise hold 100% TQQQ.
- Accounting: overnight return belongs to the position held before open execution; intraday return belongs to the position after open execution.
- No DMA, Fed, MACD, golden-cross, macro, inverse ETF, or AI filter is part of the baseline.
- Initial balance $5,000; actual-TQQQ history used here is 2010-02-11 through 2026-10-07.

Every candidate must use the same dates, fields, execution, initial capital, and costs as the baseline. Never change the baseline to improve a candidate's score.

## Baseline verification and stress diagnostics

- **Same-input daily-curve reconciliation passed:** [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Shared and independently coded engines agreed exactly on daily returns, daily equity, and all nine event transitions.
- Frozen input SHA-256: `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.
- Same-input result: baseline **$4,040,313.79**, CAGR 49.49%, max drawdown -73.53%; TQQQ buy-and-hold **$2,094,668.95**, CAGR 43.70%, max drawdown -81.66%.
- [First stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md) records period returns, event counterfactuals, and cost sensitivity.
- [Stress windows and slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md) records inherited account returns and a mechanical drawdown screen.

Period returns are independently compounded within each named period; period drawdowns are local to that window:

| Period | Baseline return | TQQQ buy-and-hold | Baseline max DD | Buy-and-hold max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +865.3% | -43.1% | -43.9% |
| 2015–2019 | +569.6% | +434.0% | -44.5% | -58.1% |
| 2020–2021 | +325.6% | +284.4% | -47.0% | -69.9% |
| 2022–2024 | +42.3% | -1.4% | -72.6% | -81.0% |
| 2025–2026-10-07 | +100.2% | +114.4% | -56.1% | -56.8% |

Slow-bear screen findings:
- 2010 episode: QQQ -15.6%, no -4.5% daily shock.
- Early 2016 episode: QQQ -16.1%, no -4.5% daily shock.
- 2018 episode: QQQ -22.8%, first shock 4 sessions after the -5% episode start.
- COVID: QQQ -28.6%, first shock 3 sessions after the -5% episode start.
- 2022: QQQ -35.1%, first shock 77 sessions after the -5% episode start.
- 2025: QQQ -22.8%, first shock 25 sessions after the -5% episode start.

The rule's main structural weakness is now explicit: a single-day-shock trigger can miss slow declines or trigger late. In 2022, the inherited strategy account still lost 69.8% over the calendar year, although TQQQ buy-and-hold lost 79.1%.

## First overlay result — rejected

The first predeclared candidate was baseline + a sticky defensive overlay entered when QQQ was below the existing 200-DMA and the previous session's Fed state was TIGHTENING_PAUSED; exit was QQQ close back at/above the 200-DMA.

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208)
- Detailed report: [Fed-paused/200-DMA overlay result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md)
- Candidate ending balance: **$2,908,571**, versus baseline **$4,040,316** on the candidate run's common data.
- CAGR: 46.57% vs 49.49%.
- Maximum drawdown: -73.53% for both.
- The overlay activated six times, all during brief 2016 and 2019 corrections. It did not activate in the 2022 tightening bear and did not change COVID or 2025 exposure.

**Decision: REJECT this exact overlay.** It reduced ending wealth by about 28% and did not improve maximum drawdown. This rejects the paused-only × below-200-DMA rule as an overlay on this baseline, not all Fed-based research.

## Next action

Before testing another candidate, perform a diagnostic-only Fed lifecycle attribution on the frozen baseline input:
1. Record lagged daily Fed states (TIGHTENING_ACTIVE, TIGHTENING_PAUSED, EASING, NEUTRAL) during each mechanically identified drawdown episode and around the baseline's nine shock/recovery events.
2. Show when state transitions occurred relative to each episode start, QQQ 200-DMA crossings, and first -4.5% shock.
3. Answer whether the existing Fed state has any causal ability to warn earlier in 2022 or the 2010/2016 slow corrections, or whether it only generates false positives during benign pauses.
4. Do not backtest a new Fed overlay until this diagnostic supports a specific causal hypothesis. If no useful signal is present, move to the already-defined macro state as a separate hypothesis; do not add indicators indiscriminately.

## Historical study boundaries

- Pre-2010 periods (1970s, 1987, 2000–2002) are signal-only index diagnostics unless a leveraged proxy is explicitly labeled synthetic. TQQQ did not exist then.
- Future outcome labels may be used for diagnostics only, never to decide whether a signal trades.
- The prior structural matrix's future-label/censored-event gate has been removed; optimized matrix rows remain exploratory/in-sample.
- The old ~$3.3M anti-fakeout strategy is a distinct historical variant and is no longer a blocker or active baseline.
- The separate synthetic ~$3.7M Fed/DMA study and extraordinary synthetic-wealth outputs are not evidence of actual-TQQQ results.

## Result labels

- **SUPPORTED:** replicated on identified data/execution with no known material methodological defect.
- **WORKING:** comparison anchor, not yet established as robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed predeclared criterion invalidates the claimed result.
- **UNRESOLVED:** evidence is insufficient.

Current baseline status: **WORKING**. Same-input numerical reconciliation is supported; generalization across slow/prolonged bears and live execution remains unresolved.

## Key recent commits

- First stress scorecard: `e2780545292964b96ab6005b3b4e2fc238e15e3c`
- Stress windows/slow-bear audit: `e25e6237cea668a39ca4de7a480a1d73d131b328`
- Fed-paused/200-DMA candidate code: `9cdd2066014f5bd8f97883803963c83ad413d189`
- Candidate workflow: `67bc0c8f4c5921416f41721d388b0d58466b0737`
- Overlay result report: `0afd787b546f5a63ca06278ad32cbd09926af0a9`
