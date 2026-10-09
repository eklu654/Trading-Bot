# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery TQQQ strategy can withstand both acute V-shaped crashes and gradual/prolonged bear markets.  
**Starting capital:** $5,000.  
**Authority:** This file and the dated research reports are the working project checkpoint. Keep old results, but clearly label their validity.

## User's current direction

Start from the current, reproducible ~$4.04M candidate and let the evidence determine its strengths, weaknesses, and whether any overlay is warranted. Do not spend more time blocking progress on recovering the separate remembered ~$3.3M anti-fakeout strategy. Historical work can inform hypotheses, but must not displace the current baseline without evidence.

## Frozen working baseline

**Rule ID:** `qqq_shock45_recovery10_actual_tqqq_v1`

- Starting equity: $5,000.
- Signal instrument: QQQ adjusted close.
- Trigger: QQQ daily adjusted-close return <= -4.5%.
- Defense: target 0% TQQQ exposure from the next open after the trigger close.
- Recovery: track the post-trigger adjusted-close low; re-enter after a close is >= 10% above that low, with execution at the next open.
- Otherwise: 100% TQQQ exposure.
- Execution accounting: overnight return belongs to the position held before the open; intraday return belongs to the position after open execution.
- No DMA, Fed, MACD, golden-cross, macro, inverse ETF, or AI filter is part of this baseline.

Do not alter this rule when creating comparison candidates. Every candidate must be run against this baseline on the same dates, data fields, execution convention, starting capital, and cost assumptions.

## Baseline verification and latest results

- Same-input daily-curve reconciliation passed: [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Both engines agreed exactly on daily equity/returns and the nine event transitions on the frozen common inputs.
- Latest robustness run: [37884245678](https://github.com/eklu654/Trading-Bot/actions/runs/37884245678), ending balance **$4,040,311.91**; TQQQ buy-and-hold **$2,094,668.80**; CAGR **49.49% vs 43.70%**; max drawdown **-73.53% vs -81.66%**. This run downloads its own market data, so use the same-input run—not cross-run decimal equality—for exact reconciliation.
- First stress scorecard: [CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md), committed at `e2780545292964b96ab6005b3b4e2fc238e15e3c`.
- Latest research sweep at commit `207213dea6e4dde44a89f68daa044e7f213fe202`: robustness, independent audit, structural matrix, long-history drawdown audit, feature audit, actual three-layer validation, partial-DMA matrix, event attribution, and research-tests all completed successfully. Individual run links are in the stress scorecard.
- The canonical candidate is a **working historical baseline**, not an approved live strategy. The approximately 73.5% maximum drawdown is severe and must be treated as a central risk finding.

## First stress findings

Returns below are measured independently inside each named period; period equity is reset to 1 at the period start. Period drawdown is likewise local to that period.

| Period | Baseline return | TQQQ buy-and-hold return | Baseline max DD | Buy-and-hold max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +865.3% | -43.1% | -43.9% |
| 2015–2019 | +569.6% | +434.0% | -44.5% | -58.1% |
| 2020–2021 (COVID crash/recovery) | +325.6% | +284.4% | -47.0% | -69.9% |
| 2022–2024 (tightening bear/recovery) | +42.3% | -1.4% | -72.6% | -81.0% |
| 2025–2026-10-07 | +100.2% | +114.4% | -56.1% | -56.8% |

The rule outperformed the control in the first four windows but lagged in 2025–current. Its nine event counterfactuals include both substantial benefits (notably 2018 Q4, COVID's initial crash, and 2022) and costly false-positive exits (notably June 2020 and April 2025). These findings justify diagnostics; they do not prove that any new filter will help.

## Historical study boundaries

- Actual TQQQ validation is limited to the period in which TQQQ exists and the aligned input data are available.
- Pre-2010 studies such as the 1970s, 1987, and 2000–2002 are signal-only index diagnostics unless a daily-reset leveraged proxy is explicitly labeled synthetic with assumptions disclosed.
- Future outcome labels (e.g., whether a recovery later failed within 252 sessions) may be used for diagnostics only; they must never determine whether a live signal is taken.
- The former structural-matrix code had a future-label/censored-event selection defect; that gate has been removed. Treat optimized matrix rows as exploratory/in-sample, not validated.
- The old ~$3.3M anti-fakeout strategy is a distinct, unrecovered historical variant. It is no longer a blocker or the active baseline.
- The separate synthetic ~$3.7M Fed/DMA study and extreme synthetic-wealth outputs are not evidence of actual-TQQQ results. Corrected actual-TQQQ three-layer validation remained far below buy-and-hold.

## Mandatory next steps

1. **Finish baseline diagnostics without changing its rules.** Build a continuous event timeline and per-period ledger for COVID (2020-02 through 2020-07), 2022, 2018 Q4, June/September 2020 false-positive exits, and April 2025. Report start/end equity, inherited-vs-reset accounting, peak/trough and recovery dates, maximum drawdown, time defensive, exit/re-entry delays, and rebound return missed.
2. **Audit slow-bear exposure.** Mechanically identify prolonged QQQ drawdowns where no -4.5% daily shock occurs near the beginning. Measure how long the baseline stays 100% exposed and the losses accrued before any trigger. Do not choose periods by looking at TQQQ strategy outcomes.
3. **Only then test overlays.** First test the existing 200-DMA × live-safe Fed lifecycle feature as a separate frozen candidate; test existing macro state separately. Combine only if an individual overlay demonstrates incremental value. No broad indicator fishing, fresh DMA-length sweeps, re-entry-delay search, or AI layer yet.
4. **Protect the growth objective.** Compare ending wealth first, with drawdown/stress behavior used to identify unacceptable failure modes. Do not optimize for drawdown alone.
5. **Use chronological holdouts.** Freeze the candidate rule before viewing the final holdout. Any rule changed after holdout inspection converts that period to development data and requires a new untouched holdout.
6. **Record every meaningful action.** Update this file and the dated report with commit SHA, run ID, input hashes/date range, rule ID, exact results, validity label, and next action.

## Result labels

- **SUPPORTED:** replicated on identified data/execution with no known material methodological defect.
- **WORKING:** usable as the current comparison anchor but not yet established as robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed predeclared criterion invalidates the claimed result.
- **UNRESOLVED:** evidence is insufficient.

Current baseline status: **WORKING**. Same-input numerical reconciliation is supported; generalization across slow/prolonged bears and live execution remains unresolved.
