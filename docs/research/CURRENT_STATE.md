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

Do not change the baseline when testing candidates. Every candidate must use the same dates, fields, execution, initial capital, and costs.

## Verification status and headline

- **Same-input daily-curve reconciliation passed:** [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Shared and independently coded engines agreed exactly on daily returns, daily equity, and all nine event transitions.
- Frozen input SHA-256: `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.
- Exact same-input result: strategy **$4,040,313.79**, CAGR 49.49%, max drawdown -73.53%; TQQQ buy-and-hold **$2,094,668.95**, CAGR 43.70%, max drawdown -81.66%.
- Latest independent robustness run [37884245678](https://github.com/eklu654/Trading-Bot/actions/runs/37884245678) reported $4,040,311.91 vs $2,094,668.80 from a separately downloaded dataset. Treat the small difference as separate-input variation; the same-input run is the strict reconciliation.
- **Status: WORKING historical candidate, not live-approved.** The ~73.5% max drawdown is severe; slow-bear robustness is unresolved.

## Completed diagnostics

1. [First stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md) — period returns, drawdowns, event-level counterfactual contributions, and cost sensitivity.
2. [Stress windows and slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md) — inherited account returns during acute/slow-bear windows and mechanical QQQ drawdown episodes.
3. [Same-input reconciliation](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700) — exact shared-vs-independent daily curve match on 4,189 rows.

### Findings from the stress audit

Period returns are calculated independently within each period; period drawdown resets at the period start:

| Period | Baseline return | TQQQ buy-and-hold | Baseline max DD | Buy-and-hold max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +865.3% | -43.1% | -43.9% |
| 2015–2019 | +569.6% | +434.0% | -44.5% | -58.1% |
| 2020–2021 | +325.6% | +284.4% | -47.0% | -69.9% |
| 2022–2024 | +42.3% | -1.4% | -72.6% | -81.0% |
| 2025–2026-10-07 | +100.2% | +114.4% | -56.1% | -56.8% |

The baseline beat the control in the first four windows but lagged in 2025-current. Event counterfactuals show large benefits in 2018 Q4, the initial COVID crash, and 2022, but large opportunity costs in June 2020 and April 2025.

Mechanical slow-bear screen uses QQQ adjusted close, a rolling 252-session high, episode entry at -5%, rearm at 95% of the reference peak, and reports troughs of at least -15%. It found:
- 2010 episode: -15.6%, no -4.5% daily shock.
- Early 2016 episode: -16.1%, no -4.5% daily shock.
- 2018 episode: -22.8%, shock 4 sessions after episode start.
- COVID: -28.6%, shock 3 sessions after episode start.
- 2022: -35.1%, first shock 77 sessions after episode start.
- 2025: -22.8%, first shock 25 sessions after episode start.

Thus, the most important known weakness is structural: a single-day-shock trigger can miss slow declines or trigger late. The 2022 inherited account still lost 69.8% in the calendar year, though less than the buy-and-hold account's 79.1% loss. This is a diagnostic, not proof that a moving-average or Fed overlay will help.

## Historical study boundaries

- Pre-2010 periods (1970s, 1987, 2000–2002) are signal-only index diagnostics unless a leveraged proxy is explicitly labeled synthetic with assumptions disclosed. TQQQ did not exist then.
- Future outcome labels may be used for diagnostics only, never to decide whether a signal trades.
- The prior structural matrix's future-label/censored-event gate has been removed; optimized matrix rows remain exploratory/in-sample.
- The old ~$3.3M anti-fakeout strategy is a distinct historical variant and is no longer a blocker or active baseline.
- The separate synthetic ~$3.7M Fed/DMA study and extraordinary synthetic-wealth outputs are not evidence of actual-TQQQ results.

## Next actions

1. **Candidate overlay A:** evaluate the existing 200-DMA relationship combined with the live-safe Fed lifecycle state (including TIGHTENING_PAUSED) as a narrow slow-bear candidate. Freeze the exact causal rule before running; never use the eventual final hike date as a real-time feature.
2. Compare the overlay against baseline on the same frozen input. Report whole-period ending balance, CAGR, max DD, rolling 12-month worst return, exposure, and exact incremental results for COVID, 2018, 2022, June/September 2020, and April 2025.
3. If and only if overlay A shows evidence of incremental value, test the existing frozen macro deterioration/crisis state as a separate candidate. Combine only if individual features show value.
4. Keep a chronological holdout untouched. If rules are revised after seeing it, the period becomes development data and a new future holdout is required.
5. No broad indicator fishing, fresh DMA-length sweep, re-entry-delay search, AI selector, or paper trading yet. The aim is higher ending wealth; drawdown diagnoses failure modes, not the sole optimization target.
6. Update this file after each meaningful step with exact rule ID, commit SHA, workflow run, input hash, results, status label, and next action.

## Latest CI sweep

At commit `207213dea6e4dde44a89f68daa044e7f213fe202`, the following completed successfully: robustness, independent audit, structural matrix, long-history drawdown audit, feature audit, actual three-layer validation, partial-DMA matrix, event attribution, research tests, and same-input reconciliation. The documentation commits for this checkpoint are `e2780545292964b96ab6005b3b4e2fc238e15e3c` (first scorecard), `e25e6237cea668a39ca4de7a480a1d73d131b328` (stress windows/slow-bear audit), and this update.

## Result labels

- **SUPPORTED:** replicated on identified data/execution with no known material methodological defect.
- **WORKING:** comparison anchor, not yet established as robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed predeclared criterion invalidates the claimed result.
- **UNRESOLVED:** evidence is insufficient.

Current baseline status: **WORKING**. Same-input numerical reconciliation is supported; generalization across slow/prolonged bears and live execution remains unresolved.
