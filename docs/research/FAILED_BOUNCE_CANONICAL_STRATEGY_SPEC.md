# Canonical QQQ Shock / Recovery Defense — Frozen Strategy Specification

Status: **working canonical candidate.** User has directed that the approximately $4.04M result be used as the working reference so research can continue. This is not a guarantee and does not mean every price/accounting audit is complete.

## 1. Objective

Continue from the QQQ shock/recovery defense that repeatedly produced approximately $4,040,313–$4,040,316 from $5,000, versus approximately $2,094,669 for TQQQ buy-and-hold over the recorded live-TQQQ period. Find weaknesses and test whether a predeclared structural rule can better handle prolonged bear markets without sacrificing V-shaped recoveries.

Do not silently substitute older DMA, three-layer, inverse-ETF, or AI strategies for this baseline. Do not tune parameters to a crisis and then report that same crisis as independent proof.

## 2. Frozen canonical rule

- Signal instrument: QQQ adjusted close.
- Traded instrument: TQQQ.
- Initial capital: $5,000.
- Recorded requested period: 2010-01-01 through 2026-10-08; each run must print actual first/last aligned observations.
- Shock trigger: QQQ adjusted-close daily return <= -4.5%.
- After the trigger, track the lowest QQQ adjusted close from the shock onward.
- Recovery trigger: first close at least 10% above that running low.
- Defensive state: zero TQQQ exposure after the shock signal close; remain defensive until the recovery decision close.
- Execution convention: a signal formed at close[t] executes at open[t+1]. Exit at the next session open after the shock close; re-enter at the next session open after the recovery-decision close.
- Otherwise hold 100% TQQQ. No inverse ETF, cash-yield assumption, AI selector, DMA layer, or Fed filter in the canonical baseline.
- Events are detected on the common aligned QQQ/TQQQ trading-date index.
- Event detector is re-armed after recovery. A second shock during an active defensive episode does not create an overlapping event.

## 3. Reference result and confidence

Recorded results repeatedly show strategy ending balance near $4.04M, buy-and-hold near $2.095M, and nine events. Proceed with $4.04M as the working reference per user instruction. Keep the distinction between reproducing a historical run and proving every data/execution assumption. The earlier QQQ/TQQQ row-index-offset suspicion was disproved: both scripts intersect/reindex the dates before event generation.

## 4. Recorded event ledger — signal close dates

| # | QQQ shock close | Running-low close | Recovery-decision close |
|---:|---|---|---|
| 1 | 2011-08-04 | 2011-08-19 | 2011-08-31 |
| 2 | 2018-10-24 | 2018-12-24 | 2019-01-07 |
| 3 | 2020-02-27 | 2020-03-16 | 2020-03-26 |
| 4 | 2020-06-11 | 2020-06-11 | 2020-07-06 |
| 5 | 2020-09-03 | 2020-09-23 | 2020-10-12 |
| 6 | 2022-05-05 | 2022-06-16 | 2022-07-19 |
| 7 | 2022-09-13 | 2022-11-03 | 2022-11-11 |
| 8 | 2025-04-03 | 2025-04-08 | 2025-04-09 |
| 9 | 2026-06-05 | 2026-07-29 | 2026-08-13 |

These are signal dates, not execution dates. Actual exposure changes occur at the next TQQQ session open. Recompute the ledger if adjusted-price history is revised.

## 5. Core question and known vulnerabilities

Can a predeclared structural risk rule recognize slow, sustained bear regimes—especially aggressive Fed tightening/inflation regimes—while preserving exposure during fast recoveries?

The canonical baseline is reactive to a one-day QQQ decline of at least 4.5%. It can miss a gradual decline that never produces that daily shock. It can also remain out after the low while waiting for a 10% recovery. It is not inherently a macro/Fed detector. These are hypotheses to test, not assumptions that the strategy already handles.

## 6. Predeclared stress taxonomy

### A. Acute V-shaped crash/rebound

Primary modern case: February–March 2020 COVID selloff and rebound. Measure exit timing, missed upside while defensive, re-entry timing, and terminal wealth versus buy-and-hold. Select additional shocks using an objective rule defined before examining strategy results, not by cherry-picking.

### B. Prolonged bear / valuation unwind

2000–2002 is an essential stress case, but TQQQ did not exist then. Do not report actual TQQQ performance for that period. QQQ can provide the observed signal. Any synthetic 3x daily leveraged QQQ proxy must model daily reset, financing, expense drag, distributions/splits, and documented costs, then be validated against live TQQQ before using pre-2010 results.

### C. Fed-induced tightening / prolonged grind down

Use dated FOMC target-rate decisions and objectively defined tightening cycles, declared before outcome analysis. Compare the baseline with a small frozen set of structural candidates such as medium-term trend/momentum and a Fed-tightening state. Treat the Fed feature as a hypothesis, not a presumed winner. Do not create a bespoke rule for 2022 and then use 2022 as its only proof.

### D. False positives and recovery preservation

Include sideways/choppy periods and quick recoveries where defensive rules can sacrifice compounding. Measure drawdown avoided and rebound gains missed. All candidates use the same TQQQ buy-and-hold control and date range.

## 7. Chronological evaluation protocol

1. Freeze the baseline and parameters.
2. Use only information available by each close; execute at the next open.
3. Report terminal wealth and CAGR, maximum drawdown, average exposure, number of exits/re-entries, turnover/cost sensitivity, and worst rolling 12-month return.
4. Report predeclared regime blocks and event attribution. Do not sum overlapping counterfactual contributions.
5. Develop candidates on earlier data; choose parameters only in development; freeze them before later chronological holdouts.
6. Treat 2022 as one observation, not sufficient evidence for a general Fed rule. Seek independent tightening episodes and clearly label pre-TQQQ proxy results.
7. Compare every candidate with the unchanged ~$4.04M baseline and buy-and-hold. Reject overlays that help one selected crisis but materially harm V-shaped recoveries or long-run terminal wealth.
8. Include realistic costs and slippage; do not present a frictionless signal as fully implementable.

## 8. Required output for every experiment

- Rule/version and exact parameters.
- Data source, price fields, requested period, actual aligned endpoints, and input hashes.
- Starting/ending balance and CAGR using actual first/last dates with the convention stated.
- Maximum drawdown, worst rolling 12-month return, average exposure.
- Exits, re-entries, turnover, and cost assumption.
- Stress-period results, including rebound upside captured/missed.
- Baseline and buy-and-hold side-by-side.
- Code commit, workflow run, artifact, and test status.

## 9. Methodology cautions

- Independent market-data downloads can differ slightly. Use identical frozen files for daily-curve comparisons.
- Standardize CAGR annualization; prior scripts used different date windows.
- The first observation's overnight return is not observed; execution code initializes first-session exposure at zero. Keep this convention consistent and explicit.
- Event counterfactual dollar differences interact through compounding; do not sum them as independent contributions.
- Charge execution costs exactly once at the actual exposure-change open.
- Any pre-TQQQ leveraged series is synthetic, never realized fund performance.
- A frozen snapshot is only frozen if exact files and hashes are preserved.

## 10. Immediate next experiments

1. Continue using the ~$4.04M rule as the reference baseline.
2. Produce a stress-period scorecard for COVID V-shaped recovery, the 2022 tightening bear, 2018 Q4, and additional objectively selected shocks.
3. Identify prolonged declines the baseline misses because no one-day QQQ return reaches -4.5%.
4. Test a small, predeclared set of structural overlays first as diagnostics, then in chronological holdouts. A Fed feature must use public policy data available at decision time.
5. Add 2000–2002 only after the synthetic 3x daily model is validated against live TQQQ history.
6. Record every material decision, result, rejected hypothesis, and next action in this specification/checkpoint and a versioned experiment ledger.

## Audit log

- 2026-10-08/09: Canonical rule reconstructed from research/failed_bounce_robustness.py and research/audit_failed_bounce_canonical_independent.py; repeated result near $4.04M, control near $2.095M, nine recorded events.
- 2026-10-09: Retracted the false QQQ/TQQQ row-index concern after confirming both scripts align dates.
- 2026-10-09: Added aligned input and daily-equity exports; corrected workflow artifact paths. Frozen-input daily-curve reconciliation remains pending.
- User decision: proceed using ~$4.04M as the working result and resume robustness/refinement research rather than blocking all progress on remaining audit work.