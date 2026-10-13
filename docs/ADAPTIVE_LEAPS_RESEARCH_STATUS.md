# Adaptive LEAPS Research — Status and Next Actions

**Updated:** 2026-10-13  
**Scope:** Frozen adaptive long-call LEAPS baseline for SPY and QQQ; conditional short-call overlay remains a later, separate experiment.

## Verified repository state

- Source data is pinned to `anahatsingh-ui/options-dataset-hist` commit `37f6c456fe1a4775c875673fb8ef907d5cd2fd66`.
- Coverage research previously recorded: duplicate keys = 0; positive underlying joins = 100%; 270-DTE candidate availability SPY 99.98%, QQQ 99.84%. These are coverage findings, not strategy-performance findings.
- Frozen selection: target 270 DTE, target absolute delta 0.80; eligible DTE window 225–315; calls only; absolute delta 0.60–0.95; valid positive bid and mark; ask >= bid; volume or open interest positive.
- Replay code currently uses close-observation signals and next available observation execution; buys at ask and sells at bid; exits when observed DTE <= 30; logs missing/invalid entries and exits; supports a $5,000 cash-enforced mode.
- Replay workflow defines four outputs: SPY theoretical one-contract, SPY cash-constrained at $5,000, QQQ theoretical one-contract, and QQQ cash-constrained at $5,000. It uploads daily ledgers, transactions, summaries, and source hashes as `adaptive-leaps-chronological-replay`.
- The replay and unit-test workflow files exist on `main`. The replay workflow has a 45-minute job timeout; unit tests have a 5-minute timeout.

## Important distinction

The code and workflow definitions are present, but this audit did **not** independently verify a completed chronological replay run or inspect its generated artifacts. Therefore there is still no validated historical P/L conclusion and no paper-trading approval from this research.

## Next actions — in order

1. Inspect the latest Adaptive LEAPS Unit Tests and Data Coverage Audit workflow runs; capture run IDs, conclusions, and artifact links.
2. Inspect the latest Adaptive LEAPS Chronological Replay run. Confirm all four replay commands completed and the artifact upload succeeded.
3. Download and reconcile each `summary.json`, `daily_ledger.csv`, and `transactions.csv`:
   - observation dates and source period;
   - starting cash + transaction cash flows = final cash;
   - no same-observation fills;
   - buys use ask, sells use bid;
   - rejected orders are counted and explained;
   - terminal open positions have a valid bid mark, otherwise terminal equity stays unavailable;
   - the $5,000 constrained runs never spend more cash than available.
4. Report SPY vs QQQ separately. Include final equity, return, max drawdown, time invested, completed trades, rejected orders, and periods with missing marks. Do not conflate theoretical one-contract results with feasible $5,000 results.
5. Only after reconciliation passes, freeze the long-call baseline and add the conditional short-call overlay as a separately attributable experiment. Preserve the rebound rule: close the short call on unwind; do not automatically re-enter; require a fresh risk activation.
6. No paper trading until the historical outputs are reproducible and reviewed.

## Workflow references

- [Adaptive LEAPS Unit Tests](../.github/workflows/adaptive-leaps-unit-tests.yml)
- [Adaptive LEAPS Data Coverage Audit](../.github/workflows/adaptive-leaps-data-coverage.yml)
- [Adaptive LEAPS Chronological Replay](../.github/workflows/adaptive-leaps-replay.yml)
- [Lifecycle primitives](../research/adaptive_leaps_lifecycle.py)
- [Replay engine](../research/adaptive_leaps_replay.py)
- [Replay runner](../research/run_adaptive_leaps_replay.py)

## Audit note

This document records repository/code inspection only. It does not assert that a workflow run succeeded or that the strategy is profitable. Update this file with actual run IDs, artifact names, reconciliation results, and any defects found after reviewing the generated outputs.


### 2026-10-13 — Replay diagnostics added; execution still unverified

- Commit [78b1736993dcc00639e309f6d049d90567d85616](https://github.com/eklu654/Trading-Bot/commit/78b1736993dcc00639e309f6d049d90567d85616) extends the replay summary with observation date range, time invested by observation, completed exits, rejected orders, held observations lacking valid bid marks, observed max drawdown with a completeness flag, transaction-cash reconciliation, and a chronology check that every fill follows its signal observation.
- These diagnostics are intentionally evidence-quality fields, not a profitability verdict. Max drawdown is explicitly labeled incomplete if any ledger observation lacks equity.
- The runner was re-fetched from GitHub after commit to verify the new fields are present. The commit has no reported combined status checks; that is not a test pass. No replay run ID or generated replay artifact has yet been independently verified in this checkpoint.
- Next: verify the fast unit-test workflow actually ran after this runner change; then verify the chronological replay run and inspect all four outputs. If run listing is unavailable, use the repository Actions UI to capture the concrete run IDs rather than infer success from a push or commit.


- Follow-up commits [ff4a3a0](https://github.com/eklu654/Trading-Bot/commit/ff4a3a0dc06ae6ade86d1b37cb7e69ed76dbb0ae) and [3c707a8](https://github.com/eklu654/Trading-Bot/commit/3c707a88cbf1bc78c4c48042eae7c0165ff3ebcd) make the diagnostics helper importable without DuckDB installed and add a synthetic unit test for cash reconciliation, next-observation chronology, completed trades, invested observations, and drawdown completeness. The source files were re-fetched to confirm both changes are on main. CI execution and the historical replay are still unconfirmed; do not treat the new test as passing until an actual workflow result is inspected.


### Additional code-review limitation — expiration lifecycle

- The runner retains option observations only for DTE 0 through 315. If an exit repeatedly fails and the held contract reaches expiration without a valid bid exit, the current engine deliberately leaves the position unresolved and terminal equity unavailable; it does not simulate exercise, assignment, or expiration settlement.
- This is fail-closed rather than silently assigning zero value, but it means any replay with unresolved expiry cases is not a fully reconciled portfolio result. The artifact audit must count these cases, and explicit expiration/exercise treatment is a required follow-up before interpreting final equity.


### 2026-10-13 22:17Z — CI verification checkpoint

- The updated LEAPS unit tests passed on current follow-up commit `3c707a88cbf1bc78c4c48042eae7c0165ff3ebcd`: [run 38476641482](https://github.com/eklu654/Trading-Bot/actions/runs/38476641482). This verifies compilation and unit-level lifecycle/replay tests, including the newly added synthetic diagnostics checks.
- Chronological replay run [38476594687](https://github.com/eklu654/Trading-Bot/actions/runs/38476594687) was still `in_progress` when checked at 22:17Z; it had not uploaded artifacts, so no historical performance figures have been independently reconciled. A second replay [38476628056](https://github.com/eklu654/Trading-Bot/actions/runs/38476628056) was pending behind the replay concurrency group on the newer runner commit.
- This is a test pass, not a strategy result. Do not report profitability or approve paper trading until a replay run completes, the four summaries and ledgers are downloaded, and cash/chronology/mark completeness checks reconcile.


### 2026-10-13 22:19Z — First chronological replay completed; results are NOT interpretable as returns

- Replay workflow [run 38476594687](https://github.com/eklu654/Trading-Bot/actions/runs/38476594687) completed successfully and uploaded artifact [`adaptive-leaps-chronological-replay`](https://github.com/eklu654/Trading-Bot/actions/runs/38476594687) (artifact ID `11853862316`). I downloaded and inspected all four summaries, transaction CSVs, and daily ledgers.
- **All four runs end with an unresolved option position and `final_equity=null` / `final_mark_available=false`. No P/L or return conclusion is valid.** The output is a data-quality/lifecycle failure, not evidence for or against strategy profitability.
- SPY (2008-01-02 to 2025-12-12; 4,514 observations): one buy on 2008-01-03 for `SPY080930C00148000` at ask 10.70; no completed exit. The engine first rejects the exit at DTE 27 on 2008-09-03 because the bid is missing, then carries the expired contract unresolved through the end of 2025. Cash is $3,930, but equity is unavailable.
- QQQ (2011-03-23 to 2025-12-15; 3,700 observations): nine transactions, four completed exits, then a buy on 2013-12-23 of `QQQ140920C00077000` at ask 12.01. Exit attempts first fail at DTE 29 on 2014-08-22 due to missing bid; that expired position remains unresolved through the end of 2025. Cash is $6,025, but equity is unavailable.
- Reconciliation checks that did pass: transaction cash reconciles exactly; every fill occurs after its signal observation; source hashes were included. Diagnostics reported 4,345 rejected orders for SPY and 2,840 for QQQ, 4,369/4,514 SPY observations and 2,954/3,700 QQQ observations held without a valid bid mark, and incomplete max drawdown for every run.
- The four theoretical/cash-constrained runs produced identical transactions and cash. This does **not** demonstrate feasibility: neither constrained run produced a valid terminal equity, and the position never closed because the selected contract's exit bid was missing.
- **Blocking follow-up:** inspect source-level quote coverage for the two selected contracts around the DTE 30 exit window; establish a predeclared, no-look-ahead missing-exit/expiration policy; add diagnostics for unresolved expired contracts and last valid mark; then rerun all four cases. Do not use `final_cash` as final account value, infer returns from realized cash flows alone, or proceed to the short-call overlay/paper trading until terminal equity is reconciled.


- Repeatability check: newer runner commit `ff4a3a0dc06ae6ade86d1b37cb7e69ed76dbb0ae` completed replay [run 38476628056](https://github.com/eklu654/Trading-Bot/actions/runs/38476628056) with the same four summary outcomes: SPY cash $3,930 and QQQ cash $6,025, but terminal equity unavailable in all cases. Its artifact (`11853992456`) was independently downloaded; cash reconciliation and chronology pass, but unresolved expired positions and missing bid marks remain unchanged. This reproduces the defect rather than resolving it.


### 2026-10-13 22:22Z — Fail-closed terminal-equity gate added

- The repeated replay proved the failure mode is specifically a missing exit bid near the expiry buffer, followed by an expired position being retained indefinitely. For SPY the terminal contract is `SPY080930C00148000`; for QQQ it is `QQQ140920C00077000`. Neither terminal position has a valid mark.
- Updated `research/run_adaptive_leaps_replay.py` to label such runs `incomplete_terminal_mark` and report terminal contract/DTE, whether it is expired, days past expiration, last valid bid-mark date, days since that mark, and entry/exit rejection counts.
- Added synthetic coverage for an unresolved expired contract in commit [`575fce4538ad9b1221800f377bc5b57996cd13cb`](https://github.com/eklu654/Trading-Bot/commit/575fce4538ad9b1221800f377bc5b57996cd13cb); [unit run 38477235719](https://github.com/eklu654/Trading-Bot/actions/runs/38477235719) passed.
- Updated replay workflow in commit [`80c19d3bfd0df737ae676713bedbf7acb2a2379f`](https://github.com/eklu654/Trading-Bot/commit/80c19d3bfd0df737ae676713bedbf7acb2a2379f): it uploads the diagnostics artifact even when the terminal-equity gate fails, then fails the workflow unless all four cases have a reconciled final mark. The new run [38477257536](https://github.com/eklu654/Trading-Bot/actions/runs/38477257536) was queued at the time of this note; no result from the new gate is claimed yet.
- This makes the CI status honest, but does not solve the source quote/expiration lifecycle issue. Next research step is to examine why selected contracts lack valid exit bids and define an ex-ante, no-look-ahead exit/settlement policy before any strategy P/L comparison.


### 2026-10-13 22:24Z — Replay quality-gate run in progress; expiration-policy design review

- Queried the GitHub Actions API directly. Latest LEAPS replay quality-gate run [38477257536](https://github.com/eklu654/Trading-Bot/actions/runs/38477257536), commit `80c19d3bfd0df737ae676713bedbf7acb2a2379f`, was still `in_progress` at 22:24Z. Job `replay` was running; no artifacts were available at that check. Do not infer a result from the workflow's presence or age.
- Current runner/workflow review found a design dependency for fixing unresolved expiration: the replay workflow downloads only option-chain Parquet files, while the separate data-coverage workflow also downloads `underlying_prices.parquet`. The contract-integrity audit recognizes underlying date columns (`date`, `timestamp`, `trading_date`, `time`) and price columns (`underlying_price`, `close`, `close_price`, `price`, `adj_close`, `underlying_close`).
- The current replay does not join underlying spot prices and does not implement expiration settlement. Therefore it cannot responsibly infer exercise/expiration value from the option bid alone after the contract disappears from the daily chain. The existing fail-closed terminal-equity gate is correct as a quality gate, but it is not the final lifecycle solution.
- Next implementation decision: add a separately tested, explicit terminal policy. Prefer a conservative pre-expiration exit rule with a defined last-tradable observation and a clear unresolved outcome when quotes are absent; only add intrinsic-value settlement if the exact underlying price convention, expiration date/time convention, ITM/OTM handling, and cash/exercise feasibility are validated. Do not quietly mark an unquoted option at zero or use future observations to backfill a price.
- Immediate next action: inspect run 38477257536 to completion, verify the artifact upload even if the terminal-equity gate fails, then use the artifact's rejection/last-valid-bid diagnostics to design the policy. No strategy P/L conclusion is valid yet.


### 2026-10-13 22:26Z — Quality-gate replay artifact inspected (run 38477257536)

- Artifact `adaptive-leaps-chronological-replay`, ID `11854517409`, downloaded and inspected from [run 38477257536](https://github.com/eklu654/Trading-Bot/actions/runs/38477257536). Contains all four summaries, ledgers, transactions, and source hashes.
- All four cases remain `incomplete_terminal_mark`; all have `final_equity=null` and `final_mark_available=false`. This is still not a strategy return result.
- SPY: 4,514 observations (2008-01-02 through 2025-12-12); one buy, zero completed exits, final cash $3,930; terminal contract `SPY080930C00148000`; last valid bid mark 2008-08-11; terminal DTE -6,282. The held contract has 4,369 observations without a valid bid mark and 4,345 rejected-order observations.
- QQQ: 3,700 observations (2011-03-23 through 2025-12-15); nine transactions, four completed exits, final cash $6,025; terminal contract `QQQ140920C00077000`; last valid bid mark 2014-03-11; terminal DTE -4,104. The held contract has 2,954 observations without a valid bid mark and 2,840 rejected-order observations.
- For all four cases, transaction cash reconciles exactly and every fill follows its signal date. However, observed drawdown is explicitly incomplete because most held observations lack valid marks. The theoretical and $5,000 modes currently produce identical outputs for each symbol because the same single long position becomes stuck; no theoretical/cash-feasible performance comparison is possible.
- Key diagnosis: this is not merely a final-day valuation issue. The first selected contract loses a valid bid well before the frozen DTE-30 exit threshold (SPY last valid bid was at roughly 50 DTE; exit first rejected at DTE 27 per prior ledger inspection), and the engine then remains blocked by the unexitable position for years. The next experiment must audit bid availability and time-to-last-valid-bid for every candidate/held contract, then compare predeclared earlier exits and a strict stale/missing-quote policy without look-ahead. Do not tune the exit threshold on these two examples alone; use a broad contract cohort and report selection bias.
- Cash-flow and chronology diagnostics pass, but the replay quality gate is designed to fail until terminal equity is valid. Run status/artifact upload should be checked separately; the existence of this artifact does not mean the workflow passed.


### 2026-10-13 22:27Z — Quality gate outcome confirmed

- Replay run [38477257536](https://github.com/eklu654/Trading-Bot/actions/runs/38477257536) completed with conclusion `failure` at 22:25:10Z. This is the intended fail-closed result: all four terminal-equity checks failed because final equity is null and the terminal option has expired without a valid exit/mark. The replay commands themselves ran and the 13-file artifact was uploaded successfully before the gate failed.
- Artifact ZIP SHA-256: `e4ca6d3fecc5f9b47cab5491bb1fe2d7c48ea21ae71e4aa4e15d9942b7e88f1d`; artifact ID `11854517409`.
- Logs confirm all four failures explicitly, with SPY terminal DTE -6,282 and 4,345 exit rejections; QQQ terminal DTE -4,104 and 2,840 exit rejections. The gate now prevents this incomplete run from being misreported as a successful backtest.
- Research decision: do not merely force a terminal value to make CI green. Next implement an audit of quote-history continuity and missing-bid incidence for held contracts; then compare predeclared exit buffers using a representative cohort and report all unexitable positions as unresolved. Any policy using underlying spot/expiration intrinsic value must be a separately specified and tested settlement model, not a convenient patch to these results.


### 2026-10-13 22:34Z — Quote-continuity audit added; validation pending

- Added `research/audit_adaptive_leaps_quote_continuity.py` (initial commit `6346963222e275d9c3e2eeaf301d2fb638079346`) and wired it into the replay workflow in `e02f4adaba51bb7327a41b59fdc1f49b5bcb50d6`. It measures eligible-contract quote persistence, valid/invalid bid rows, the last valid bid date and DTE, calendar gaps between observed rows, and rows after the last valid bid. It flags the two terminal contracts from replay 38477257536.
- The audit explicitly does not treat missing rows as quotes, does not impute a zero mark, and is diagnostic only; it does not change entry/exit logic or the terminal-equity quality gate.
- Current main-branch validation run: [38478595334](https://github.com/eklu654/Trading-Bot/actions/runs/38478595334), triggered at 22:33:34Z. At the last check it was still in progress, so no claim yet that the audit query executes successfully or that its output exists.
- Created isolated branch `leaps/quote-continuity-audit-fix` from `e02f4adaba51bb7327a41b59fdc1f49b5bcb50d6` and hardened the audit aggregation in commit `a8f2700b024cf679ade23fca1fd92365cd0462ae`: removed a correlated aggregate subquery and made the optional flagged-contract indicator explicitly false when no IDs are supplied. This follow-up is not on main and has not been executed against the pinned Parquet data.
- Next: obtain run 38478595334's final conclusion and audit-step logs/artifacts. If the query errors, fix on the isolated branch, add a synthetic SQL fixture/test, and validate before merging. Do not change the frozen DTE-30 exit rule until cohort-level results are available.
