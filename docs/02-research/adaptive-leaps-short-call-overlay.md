# Adaptive LEAPS + Short-Call Overlay Research

**Status:** Specification / data-feasibility gate; no strategy result or candidate promotion  
**Opened:** 2026-10-12  
**Scope:** Independent options strategy research. This track is separate from ETF-001, B0, F75, OPTIONS-001, and OPTIONS-002.  
**Underlyings:** QQQ and SPY, tested separately with identical rules where contract mechanics permit.  
**Starting-account reference:** $5,000, with feasibility reported separately from theoretical one-contract economics.

## 1. Research question

Can a long-dated call combined with a conditionally activated, repeatedly managed short-call overlay improve total ending equity versus simply holding the long call, while retaining enough upside participation and avoiding catastrophic option-position/account outcomes?

The hypothesis is not that premium is free protection. Short calls can cushion a decline, but cap gains during rebounds and can become expensive to close. Rolling is a close plus a new trade; it does not erase a loss or guarantee maximum profit.

## 2. Strategy anatomy and terminology

- **Long leg:** one long-dated call on QQQ or SPY, initially researched in the 270–540 calendar-day DTE region, subject to available historical contracts.
- **Overlay:** optionally sell one nearer-dated call while the long call is held. The overlay is inactive in the baseline state.
- If the short call has a different expiry from the long call, the position is generally a **diagonal call spread**, not a stock-covered call. It is not necessarily fully riskless or fully covered in broker/account terms.
- The long call's maximum loss is its premium. The short call's loss is theoretically unlimited in isolation; the long call may offset some but not necessarily all of its exposure at every time/strike combination.
- All results must include the combined position marked to market, not premium received as a standalone profit measure.

## 3. Frozen initial research variants

A. **LONG_CALL_HOLD:** buy the long-dated call and manage only using the common predeclared long-leg expiry/exit rule. No short calls.

B. **ALWAYS_SELL_SHORT_CALL:** sell a short-dated call on a fixed cadence, regardless of regime. This measures the opportunity cost of persistent upside caps.

C. **RISK_TRIGGERED_SHORT_CALL:** keep the long call uncapped in normal conditions; open a short call only after a causal risk detector activates.

D. **RISK_TRIGGERED_DELTA_ROLL:** as in C; when a short call meets the predeclared profit/roll condition, close it and sell a replacement call targeting a configured absolute delta. Re-evaluate on each observation date while the risk regime remains active.

E. **ROLL_WITH_REBOUND_EXIT:** as in D, but close the short call when a separate rebound-risk/unwind rule activates. Do not immediately re-open merely because the prior short was closed.

F. **LONG_LEG_RISK_EXIT:** as in E, with a separately specified rule to reduce or close the long call in extreme-risk conditions. Keep this separate from the short-call overlay to attribute value correctly.

No variant is presumed superior. The long-call baseline is essential because a strategy that collects premium but underperforms long-call hold may not be useful.

## 4. Initial parameter matrix (exploratory, not optimized/promoted)

### Long-call candidates
- DTE target: 270, 365, and 540 calendar days where chain coverage permits.
- Delta targets: 0.70, 0.80, and 0.90; choose the closest valid call by absolute delta distance at entry.
- One contract for theoretical mechanics; separately model whether premium fits the $5,000 account and what fraction of NLV it consumes.

### Short-call candidates
- DTE target: 21 and 35 days, selected from a predeclared eligible range of 14–45 DTE.
- Absolute delta target: 0.10, 0.16, and 0.25.
- Roll/profit capture triggers: evaluate closing at 50% and 75% of maximum short-call premium decay; also evaluate a fixed delta trigger as a separate policy. Do not conflate profit capture and delta targeting into one unexplained trigger.
- When rolling, close the old contract using an executable quote-side assumption, then open a distinct replacement contract selected from information available on that date. Record the net debit/credit and realized P/L separately.
- Only roll when the short-call risk overlay remains enabled, the replacement passes quote/liquidity checks, and the order is feasible. Otherwise close/hold per the frozen policy; never silently skip an adverse roll without logging it.

The matrix is intentionally bounded. First test the main mechanics and data quality; do not grid-search every combination against the full history.

## 5. Causal regime and position-management rules

The first implementation should compare:
1. an always-on short-call control;
2. a simple causal risk gate using only data available at the prior completed close;
3. an independently defined rebound/unwind rule.

No future close, future realized volatility, future option Greek, or future chain row may influence a current decision. Signals computed from close t are executable no earlier than the next observation/session unless the dataset supports a correctly timestamped later execution.

Do not choose a risk gate by maximizing full-sample return. Freeze the candidate gate on development data, then validate chronologically and preserve an untouched holdout. Record every activation, deactivation, opening, closing, roll, expiry, assignment proxy, and rejected trade with reason codes.

## 6. Data feasibility: coverage, integrity, and candidate availability verified

The public preservation mirror `anahatsingh-ui/options-dataset-hist` README and directory listings were checked on 2026-10-12. It reports EOD option-chain snapshots (4:00 PM ET) and yearly Parquet files:
- **SPY:** 2008–2025, 24,681,665 contract-day rows.
- **QQQ:** 2011–2025, 15,345,882 contract-day rows.
- Fields include contract_id, symbol, expiration, strike, type, bid/ask/mark, volume, open_interest, date, implied_volatility, delta, gamma, theta, vega, rho, and in-the-money status.
- The mirror describes the source as a byte-verified preservation copy of Philipp D. Dubach's original MIT-licensed dataset.

This confirms both underlyings exist in the source. The empirical coverage, quote-quality, contract-integrity, underlying-join, and candidate-availability audits are now complete for the pinned source revision. These checks establish research-data availability and basic row integrity only; they do **not** prove executable fills, assignment correctness, or strategy profitability.

A new data audit script and manual GitHub Actions workflow were added:
- `research/audit_adaptive_leaps_coverage.py`
- `.github/workflows/adaptive-leaps-data-coverage.yml`

The workflow downloads SPY chains for 2008–2025 and QQQ chains for 2011–2025, profiles contract-day coverage and quote quality, and uploads CSV/JSON reports as an artifact. **Execution verified 2026-10-12:** [run 38225648878](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878) completed successfully and uploaded [artifact 11736311901](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878/artifacts/11736311901). The report found 5,792,357 SPY and 3,089,957 QQQ contract-day observations at DTE >=270; 4,455,633 SPY (76.9%) and 2,275,977 QQQ (73.7%) also passed the report's valid-quote-plus-activity rule. These are contract-day counts, not proof of executable fills. Full results are in `docs/02-research/adaptive-leaps-data-coverage-results-2026-10-12.md`.

A follow-up analysis found uneven annual coverage and material spread variation in the 270–539 DTE / 0.60–0.84 absolute-delta call region. See `docs/02-research/adaptive-leaps-yearly-coverage-review-2026-10-12.md`. The contract-integrity audit completed successfully in [run 38226350847](https://github.com/eklu654/Trading-Bot/actions/runs/38226350847): zero duplicate candidate keys and 100% positive same-date underlying-close joins in every year of the tested candidate region. This is not proof of executable fills or correct corporate-action adjustments. The workflow is pinned to source commit `37f6c456fe1a4775c875673fb8ef907d5cd2fd66`; [run 38226516897](https://github.com/eklu654/Trading-Bot/actions/runs/38226516897) completed successfully and recorded SHA-256 hashes for all 35 source Parquet files in artifact [11736697765](https://github.com/eklu654/Trading-Bot/actions/runs/38226516897/artifacts/11736697765). The corrected candidate-availability audit [run 38226954965](https://github.com/eklu654/Trading-Bot/actions/runs/38226954965) uses option-chain observation dates as the denominator and found 270-DTE candidate availability of 99.98% for SPY and 99.84% for QQQ, versus materially lower coverage at 365/540 DTE. Its earlier denominator bug is documented and the initial report is superseded.

The source is EOD-only. The first replay therefore represents a once-daily decision/quote model, not intraday execution. Any trigger that depends on an intraday touch is out of scope unless supported by suitable intraday data.

## 7. Fill, valuation, and accounting requirements

- Preserve raw source bid, ask, mark, IV, Greeks, volume, open interest, underlying close, strike, expiry, and contract identifier.
- For buys, conservative fill starts at ask; for sells, at bid. Midpoint is sensitivity only, never the sole reported result.
- Closing a short call is a buy at ask in the conservative model; selling the replacement call receives bid. Long-call liquidation uses bid.
- Include commissions/fees and an explicit slippage sensitivity. Do not use the mark as if it were always executable.
- Mark all legs on each observation date; include cash, option market value, realized/unrealized P/L, and total equity.
- Do not double-count collected short-call premium as profit while the short liability remains open.
- Expiry, exercise, and assignment must be handled explicitly. If the EOD source cannot resolve exercise/assignment reliably, label that case as a limitation and use conservative deterministic handling.
- Report theoretical one-contract strategy economics separately from account-feasible returns. A $5,000 account may be unable to buy a high-delta LEAPS contract on either underlying; fractional option contracts are not allowed.
- The overlay is not automatically “covered” for broker margin/assignment purposes merely because a LEAPS call exists.

## 8. Required controls and metrics

For each underlying and variant report:
- starting/ending equity and net P/L;
- CAGR only when account-equity accounting and dates make it meaningful;
- maximum drawdown and recovery duration;
- worst day/trade and largest loss from a short-call roll;
- long-call premium at risk and long-leg time-to-expiry at each decision;
- gross short-call premium collected, buyback cost, net overlay P/L, fees/slippage;
- percentage of time the upside was capped and missed upside during sharp rebounds;
- number of rolls, average net credit/debit per roll, roll win/loss distribution;
- assignment/expiry events and any account-feasibility failures;
- conservative versus midpoint sensitivity;
- performance by volatility/trend regime and major stress periods;
- QQQ vs SPY comparison on the same dates, with no cross-underlying pooling that hides differences.

Required controls: long-call hold; always-sell overlay; no-roll short-call overlay; delta-roll overlay; risk-gate placebo or shuffled activation control where feasible. Report failed and rejected trades, not only completed positions.

## 9. Acceptance gates

Do not call the strategy validated unless:
1. symbol and DTE coverage are proven from source rows;
2. chain data passes documented quality checks;
3. entry/exit/roll decisions are causal and reproducible;
4. conservative bid/ask results are primary, with midpoint only as sensitivity;
5. all variants share the same date/underlying and long-call selection basis;
6. total equity includes open option liabilities and realistic closing costs;
7. account feasibility is separated from theoretical P/L;
8. results are split chronologically into development, validation, and untouched holdout;
9. adaptive results beat relevant controls after costs, without the result depending on a small number of hand-selected episodes;
10. no candidate is promoted solely on in-sample terminal wealth.

## 10. Next implementation steps

1. Coverage, contract-integrity, year-by-year, and corrected candidate-availability audits are complete. Use 270 DTE as the first plumbing case (near-complete candidate availability); keep 365 as secondary and 540 as incomplete-coverage sensitivity.
2. Source URLs are pinned and all 35 downloaded Parquet files are SHA-256 hashed in the workflow artifact.
3. Freeze an entry calendar and long-leg replacement/exit rule before P/L replay; the current spec defines target DTE/delta but not a unique entry schedule.
4. Implement deterministic one-long-call lifecycle first, with causal selection and conservative bid/ask valuation; then add the short-call overlay state machine.
5. Add unit tests for expiry boundaries, missing/crossed/zero quotes, stale/low-activity rows, contract selection ties, early close/expiry, short-call rebound exits, missing replacements, and account-feasibility rejection.
6. Preserve the current short-call rebound behavior as frozen: on rebound/unwind, close the short call rather than automatically selling another; only re-open on a fresh risk activation after reset.
7. Only after the runner is reproducible and runtime-bounded, expand the matrix and add walk-forward validation.

## Audit log

### 2026-10-12 — Initial specification created
- User requested a standalone LEAPS investigation, independent from B0/F75 and the main ETF strategy.
- Both QQQ and SPY are in scope.
- Core concept: long-dated call is normally uncapped; in deteriorating markets the bot sells shorter-dated calls, can repeatedly roll profitable shorts toward a target delta, and can roll out in time when instability persists.
- Research emphasis: test if dynamic short-call management adds net value after bid/ask costs while preserving rebounds. Rolling is not treated as free profit or automatic risk reduction.
- Initial spec commit: `e491fe4fd994cad85f94ccf2ac08c207f0443a81`.

### 2026-10-12 — Historical source discovery and coverage audit implementation
- Verified source README lists SPY 2008–2025 (24.68M rows) and QQQ 2011–2025 (15.35M rows), with EOD Greeks/quotes and underlying-price Parquet files.
- Added `research/audit_adaptive_leaps_coverage.py` (initial commit `22fa94ebfdaaa22cb6677e6e9aa11b9bcc1f3017`; quote-null counting fix `7a5a4333a5c42fcc18b81a7d953e69efb802d233`).
- Added manual-only workflow `.github/workflows/adaptive-leaps-data-coverage.yml` (commit `3a1a87f4e485e304912ca1b2fc1945a4bdb6c3ce`).
- Workflow execution is not yet confirmed. Do not infer long-DTE coverage or any strategy performance until its artifact is inspected.
- Next gate: obtain the coverage artifact, then decide whether to implement the replay engine or address data gaps.

### 2026-10-12 — Explicit short-call rebound behavior frozen
- If deterioration persists and the overlay remains enabled, the short call may be managed/rolled only under the predeclared profit, delta, and replacement-quality rules; a roll is a separate close plus open and must record net debit/credit.
- If the market improves and the rebound/unwind rule fires, close the existing short call using the conservative ask-side assumption. Do **not** automatically sell a replacement call just because the long LEAPS remains open or the prior risk regime was recently active.
- Re-entry requires a fresh, causal risk activation after the unwind/reset condition; no same-cycle immediate re-selling. If quotes, liquidity, or account feasibility fail, log the rejection and leave the overlay inactive rather than forcing a roll.
- This is a management-rule clarification only, not a claim that the strategy has been backtested or validated. The data-coverage workflow still needs to run and its artifact must be inspected before the replay engine is built.

### 2026-10-12 — Coverage auditor SQL repair
- Code review found a literal escaped newline embedded in the aggregate SQL around missing-quote counts; corrected it to a real SQL line break in `research/audit_adaptive_leaps_coverage.py` (commit `07728ca62c28a57dde09fcafb2cdd1fc3fcb72e9`).
- This is a syntax repair, not a verified coverage result. The manual workflow still must run successfully and its CSV/JSON artifact must be inspected before strategy replay work proceeds.


### 2026-10-12 — Lifecycle primitives and test gate added
- Added `research/adaptive_leaps_lifecycle.py` with immutable quote representation, 270-DTE candidate eligibility/selection, ask-side buys, bid-side sells, 30-DTE exit predicate, and a guard that disallows same-snapshot execution.
- Added `tests/test_adaptive_leaps_lifecycle.py` for invalid/crossed/zero quotes, activity gate, selection tie-breaks, buy/sell sides, expiry buffer, and causal execution-date boundary.
- Updated `.github/workflows/adaptive-leaps-data-coverage.yml` to compile the lifecycle module and run its focused unit tests. CI run [38227733194](https://github.com/eklu654/Trading-Bot/actions/runs/38227733194) was queued at the time of this note; do not call the test gate passed until the run is completed and its steps are inspected.
- This is a mechanics layer, **not yet a historical lifecycle replay**. No return, drawdown, CAGR, account feasibility, assignment behavior, or short-call overlay performance has been computed from it.
- The current primitive uses a frozen 270-DTE target, +/-45 calendar-day eligibility band, absolute delta 0.60–0.95, valid non-crossed quote, and volume/open-interest activity. Ranking: DTE distance, delta distance, relative spread, higher OI, higher volume, earlier expiration, lower strike, contract ID.
- Before any P/L replay, define an explicit entry calendar and missing-candidate policy; ensure all fills happen no earlier than the next available EOD observation after the signal. Add portfolio/account ledger and long-leg lifecycle integration only after this focused test gate passes.


### 2026-10-12 — Fast unit-test workflow isolated
- Added `.github/workflows/adaptive-leaps-unit-tests.yml` so lifecycle unit tests run independently of the lengthy historical Parquet downloads.
- Fast test run [38227835157](https://github.com/eklu654/Trading-Bot/actions/runs/38227835157) completed successfully. The module compiled and all **7 lifecycle unit tests passed** (0.001 seconds): quote/activity validity, invalid/crossed quotes, deterministic ranking, no-candidate behavior, ask/bid execution sides, expiry-buffer boundary, and next-observation causality.
- The data-coverage workflow also now runs the unit tests before its data downloads, so syntax/logic failures surface early on future runs.
