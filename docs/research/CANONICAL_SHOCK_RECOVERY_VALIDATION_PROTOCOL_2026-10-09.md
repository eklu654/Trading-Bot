# Canonical Shock/Recovery — Validation Protocol and Decision Gates

**Date:** 2026-10-09 UTC  
**Status:** PRE-REGISTERED RETROSPECTIVE VALIDATION PLAN; no candidate selected  
**Capital:** $5,000  
**Canonical input reference:** same-input reconciliation run [37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700), SHA-256 `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.  
**Purpose:** turn the verified baseline and two narrow overlay candidates into a disciplined comparison without pretending that previously inspected data is an untouched holdout.

## 1. Current research question

Can a modest, causal structural defense improve the canonical QQQ shock/recovery strategy's severe drawdown and prolonged-bear behavior without materially sacrificing terminal wealth or the sharp-crash recovery participation that makes the baseline attractive?

This protocol does not assume an overlay is necessary or that the active-Fed overlay is correct. The baseline remains the control and can win.

## 2. Frozen candidates

All candidates use actual TQQQ only over aligned available data, $5,000 initial equity, QQQ adjusted close for signals, TQQQ open/adjusted-close-consistent returns, close[t] decisions executed at open[t+1], and identical data rows.

| ID | Rule | Status |
|---|---|---|
| B0 | Canonical shock/recovery only: QQQ adjusted-close daily return <= -4.5% activates 0% TQQQ at next open; remain defensive until QQQ close is >=10% above post-shock running low; re-enter next open; otherwise 100% TQQQ. | Frozen control |
| F50 | B0 plus 50% TQQQ exposure while QQQ is below its existing 200-session SMA and the previous-session Fed lifecycle state is TIGHTENING_ACTIVE; overlay ends when QQQ closes at/above the 200-DMA. B0 shock defense overrides to 0%. | Development candidate |
| F75 | Same as F50 but 75% TQQQ exposure in the overlay state. | Development candidate |
| F00/F25 | Same state rule with 0%/25% TQQQ exposure. | Sensitivity controls only |

No rule changes, new indicators, new DMA lengths, alternate thresholds, AI, inverse ETFs, or additional macro filters are allowed in this comparison round. If a defect is found, document it, fix it, and rerun every candidate on the same corrected input; do not patch only the losing candidate.

## 3. Data and causality requirements

1. Freeze the common QQQ/TQQQ data file and any Fed-state input once per run; write SHA-256 hashes, row count, first/last date, column list, and missing/duplicate-date checks into the artifact manifest.
2. All candidates must use the same common session index and same adjusted-price convention.
3. Signal at close[t], execute at open[t+1]. Overnight return belongs to the position held before the open trade; intraday return belongs to the post-trade position. No close[t] signal may earn a return that occurred before its execution.
4. Fed state must be lagged to information available by the decision time. Record the exact state source, effective dates, and lag. Never backfill a state using a later-known policy decision.
5. No future outcome labels may determine whether a signal is allowed to trade. Labels that require future observations may be used only for post-hoc diagnostics and must be kept out of position construction.
6. Assert identical date indexes, signal arrays, and execution assumptions for B0/F50/F75; fail loudly if hashes, lengths, dates, or state timing differ.

## 4. Retrospective chronological diagnostics (not untouched holdouts)

The full modern history has already been inspected and candidates were compared over it. Therefore, every historical slice below is a **retrospective stability diagnostic**, not an independent confirmatory holdout and not proof of generalization.

Report each candidate and B0 on:
- 2010-02-11–2014-12-31: early available market regime;
- 2015-01-01–2019-12-31: corrections, volatility, and trend-cross whipsaws;
- 2020-01-01–2021-12-31: acute crash and fast recovery;
- 2022-01-01–2024-12-31: tightening-driven bear and subsequent recovery;
- 2025-01-01–last common observation: recent regime, explicitly shorter and incomplete.

For each segment, independently compound returns from a 1.0 normalized start as well as report the continuous inherited-account curve separately. State clearly which is which. Include event-based windows for COVID, 2018 Q4/2019 recovery, 2022, and the baseline's false-positive exits in June/September 2020 and April 2025.

Do not use the best segment to select the winner. A later rule change invalidates the present comparison and creates a new development candidate.

## 5. Required scorecard

For each strategy and segment, report:
- terminal equity from $5,000 on the continuous path;
- CAGR with exact date convention;
- maximum drawdown and peak/trough/recovery dates;
- worst rolling 252-session return and its dates;
- calendar-year returns, especially 2020, 2022, 2025, and latest partial year;
- exposure-weighted sessions and time in cash;
- number of transitions and turnover proxy;
- event-level exit/re-entry timestamps and next-open execution;
- costs at 0, 10, 25, and 50 basis points per full exposure change, applied consistently;
- paired differences versus B0 in ending wealth, max drawdown, and worst rolling-year return;
- results for every predeclared candidate, including negative results.

Cost results are sensitivities, not claims of real spreads/slippage. Funding, taxes, market impact, borrow, and broker fill assumptions must be called out if not modeled.

## 6. Candidate decision gates (predeclared)

An overlay can advance to further research only if all data/causality assertions pass and:
1. its terminal wealth is at least 95% of B0 after the 25 bp exposure-change cost sensitivity;
2. its maximum drawdown improves by at least 5 absolute percentage points versus B0;
3. its worst rolling 252-session return improves by at least 5 absolute percentage points versus B0;
4. it does not materially worsen the COVID crash/rebound outcome or the 2018 recovery whipsaw without a clearly quantified trade-off;
5. its apparent benefit is not attributable solely to one isolated episode, as shown by leave-one-overlay-episode-out contribution diagnostics;
6. no segment's return/equity calculation, signal timing, or accounting convention differs from B0.

These are screening gates, not statistical proof. The criteria are intentionally multi-objective: a candidate that increases terminal wealth but fails the downside gates is not automatically selected; one that reduces drawdown but destroys too much wealth is not selected either. If no candidate passes, retain B0 and report that the current candidates failed.

## 7. What constitutes actual out-of-sample evidence

Because the available modern history has already been examined, the historical folds cannot be relabeled as untouched holdouts. They are useful for locating regime dependence and accounting errors only.

A genuine prospective test requires freezing code, rules, dependencies, and data timestamp before observing the next period, then recording decisions and fills without changing the rules. Paper trading is not authorized by this document; it is a later decision gate after historical accounting, realistic execution modeling, and strategy selection are complete. If the strategy is changed after observing prospective results, the modified version starts a new forward test.

## 8. Known limitations and unresolved items

- The 2010–2026 actual-TQQQ sample does not include earlier market regimes.
- The S&P 500 signal-only study for the 1970s and 1987 and QQQ signal-only study for 2000–2002 are context, not actual TQQQ returns.
- The active-tightening/200-DMA overlay helped in 2022 but caused whipsaw/opportunity cost around 2018–2019 and did not stay defensive throughout the dot-com bear.
- Adjusted-price histories can be revised by vendors. Reproducibility depends on preserving exact input artifacts and hashes, not redownloading later.
- Full-sample ending balances and parameter-family results are vulnerable to selection bias even when the accounting is correct.
- Historical results do not establish future returns or suitability for live trading.

## 9. Required audit trail for every next experiment

Each run must preserve:
1. commit SHA and workflow run URL;
2. exact command, dependency versions, start/end date, and input hashes;
3. frozen candidate rule IDs and parameters;
4. row/date validation, assertions, and test output;
5. summary metrics, period scorecard, daily equity/exposure, event ledger, and cost sensitivity artifacts;
6. a short interpretation separating observed facts, hypotheses, limitations, and the next action.

## 10. Current disposition

- B0: **WORKING CONTROL**, numerically reproduced on a frozen common input; not proven robust for all regimes.
- F50: **WORKING DEVELOPMENT CANDIDATE**, promising in-sample wealth/drawdown trade-off; not selected.
- F75: **WORKING DEVELOPMENT CANDIDATE**, more growth-oriented in-sample trade-off; not selected.
- Existing macro classifier overlay: **REJECTED for this objective** based on its actual-TQQQ test.
- AI, paper trading, and broad indicator searches: **NOT AUTHORIZED IN THIS RESEARCH PHASE**.

Next action: build one compact reproducibility workflow that reruns B0/F50/F75 on a single frozen input and emits the complete scorecard and assertions defined above. Do not tune rules during that implementation.
