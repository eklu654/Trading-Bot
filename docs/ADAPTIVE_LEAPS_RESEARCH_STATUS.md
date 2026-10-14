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


### 2026-10-13 22:37Z — Quote-cohort review caught right-censoring bias; correction added

- Downloaded and inspected artifact [11855876774](https://github.com/eklu654/Trading-Bot/actions/runs/38478595334/artifacts/11855876774), SHA-256 `26f83d33d3d212adf9f2e50c5bcd782c7fd53faa87890d5a6f43c252ef91cf8c`. The source-level quote continuity audit ran successfully for both symbols and uploaded per-contract CSVs.
- Initial audit totals (SPY 651/8,930; QQQ 769/6,158 with last valid bid >30 DTE) were **biased by right-censoring**: contracts expiring after the end of source coverage were counted as if the dataset had observed their expiration. Do not cite these initial rates as evidence of early quote disappearance.
- Recomputed using only contracts whose expiration is on or before the source coverage end (SPY through 2025-12-12; QQQ through 2025-12-15): SPY has 8,231 expiration-observed contracts, of which 133 (1.62%) have last valid bid more than 30 DTE before expiration; QQQ has 5,535 expiration-observed contracts, of which 335 (6.05%) do. Right-censored contracts excluded: 699 SPY and 623 QQQ. These are source-cohort diagnostics, not estimates of live fillability or strategy outcomes.
- Terminal-contract findings remain direct: SPY `SPY080930C00148000` last valid bid 2008-08-11 at 50 DTE, with 35 later source rows lacking a valid bid; QQQ `QQQ140920C00077000` last valid bid 2014-03-11 at 193 DTE, with one later invalid-bid row before its source history ends. Both expire within the source coverage, so right-censoring does not explain either terminal case.
- Fixed on isolated PR branch [#28](https://github.com/eklu654/Trading-Bot/pull/28): quote audit now records source coverage end and flags whether expiration is fully observed; headline rates count only fully observed expirations. Added a synthetic Parquet-backed test with one expired/mature contract and one right-censored contract.
- Main replay run [38478595334](https://github.com/eklu654/Trading-Bot/actions/runs/38478595334) failed the terminal-equity quality gate as intended, but the replay artifact and both quote-continuity summaries were uploaded successfully. The audit step itself completed for SPY and QQQ.
- Next: wait for PR #28's focused unit test result; if it passes, review the corrected audit output and merge only after the test verifies that right-censored contracts are excluded. Then run the corrected audit against pinned source before changing the frozen exit policy.


### 2026-10-13 22:40Z — Corrected quote audit rerun verified; data discontinuity is the next blocker

- PR [#28](https://github.com/eklu654/Trading-Bot/pull/28) merged as `e8b06bca104ab253780c551dcff1490861a7c062`. Focused LEAPS tests passed: [run 38479001187](https://github.com/eklu654/Trading-Bot/actions/runs/38479001187), 19 tests in 0.221 seconds; the broader research tests also passed on [run 38479001186](https://github.com/eklu654/Trading-Bot/actions/runs/38479001186).
- Corrected replay/audit run [38479111640](https://github.com/eklu654/Trading-Bot/actions/runs/38479111640) uploaded artifact [11856937081](https://github.com/eklu654/Trading-Bot/actions/runs/38479111640/artifacts/11856937081), SHA-256 `543cb884656a328e6dc1ba07e8fef89a2e102ce4994f1906d32b0f11e45bd946`. Both audit summaries now explicitly identify source coverage end and exclude right-censored contracts from mature-expiration rates.
- Corrected cohort totals: SPY 8,930 eligible contract IDs; 8,231 expirations observed by source end (2025-12-12); 699 right-censored; 133/8,231 (1.62%) mature contracts have last valid bid >30 DTE. QQQ 6,158 eligible IDs; 5,535 expirations observed by source end (2025-12-15); 623 right-censored; 335/5,535 (6.05%) mature contracts have last valid bid >30 DTE. These are historical source-continuity statistics, not live fillability or P/L.
- Terminal contracts remain unresolved and fully within source coverage: SPY `SPY080930C00148000` last valid bid 2008-08-11 at 50 DTE with 35 later source rows lacking a valid bid; QQQ `QQQ140920C00077000` last valid bid 2014-03-11 at 193 DTE with one later invalid row and no subsequent contract rows. All four replay cases remain `incomplete_terminal_mark`, final equity null; quality-gate failure is expected and correct.
- Independent analysis of the per-contract CSVs found concentrated expiration-year anomalies: SPY 2008: 45/103 contracts late (>30 DTE); SPY 2009: 88/187; QQQ 2014: 80/200 (all 80 last valid bid 2014-03-11 and last source row 2014-03-12); QQQ 2024: 253/750 (all 253 last valid bid 2023-12-26 and last source row 2024-01-09). The pinned source README says it provides one row per option contract per trading day at 4 PM ET ([README at pinned commit](https://github.com/anahatsingh-ui/options-dataset-hist/blob/37f6c456fe1a4775c875673fb8ef907d5cd2fd66/README.md)). These date-clustered disappearances therefore require source-methodology/completeness investigation before being interpreted as real market quote unavailability.
- Next gate: build a reproducible expiration-year/date-cluster report and cross-check these cohorts against source trading-date coverage and, where available, the same-date underlying series. Do not tune exit DTE or introduce stale-price/exercise assumptions until the data discontinuities are classified. Do not treat final cash as final equity.


### 2026-10-13 22:44Z — Expiration-year discontinuity report generated and verified

- PR [#29](https://github.com/eklu654/Trading-Bot/pull/29) merged as `47c3cf74f42a1fed41e2b8d0e3ad062a1db31525`. Focused LEAPS tests passed on [run 38479437893](https://github.com/eklu654/Trading-Bot/actions/runs/38479437893), 19 tests; broader repository research tests passed on [run 38479437885](https://github.com/eklu654/Trading-Bot/actions/runs/38479437885).
- The updated main-branch replay/audit [run 38479521315](https://github.com/eklu654/Trading-Bot/actions/runs/38479521315) completed and uploaded artifact [11856087691](https://github.com/eklu654/Trading-Bot/actions/runs/38479521315/artifacts/11856087691), SHA-256 `254f6730f7f1acb99c4d670afc1e25fac9b56e64e21149456d25f5fba79bd638`. Both replay commands and both quote audits succeeded; the final terminal-equity gate failed as expected because all four cases still have unresolved expired positions.
- Artifact now contains per-contract CSV, expiration-year CSV, and summary JSON for SPY and QQQ. Corrected mature-cohort rates remain SPY 133/8,231 (1.62%) and QQQ 335/5,535 (6.05%) with right-censored expirations excluded.
- Reproducible expiration-year report confirms concentration: SPY 2008: 45/103 mature contracts (43.69%); SPY 2009: 88/187 (47.06%); QQQ 2014: 80/200 (40.00%), with 100% of that year's late-bid contracts sharing last valid bid 2014-03-11 and last source row 2014-03-12; QQQ 2024: 253/750 (33.73%), with 100% sharing last valid bid 2023-12-26 and last source row 2024-01-09. These date clusters reinforce that source-history completeness is the immediate research blocker.
- No exit-rule change was made. Do not treat the above source gaps as proof of actual untradeability or use a stale mark/zero/expiry settlement as a convenience to force P/L. Next step is to cross-check these specific contract-history cutoffs against the source's underlying trading-date series and dataset methodology; only then decide whether the affected periods can be repaired, excluded under a predeclared data-quality rule, or require a different source.


### 2026-10-13 — Underlying-session cross-check added; CI validation pending

- New isolated branch `leaps/underlying-date-discontinuity-audit` adds `research/audit_adaptive_leaps_source_discontinuity.py`. For the two replay-blocking contracts (`SPY080930C00148000`, `QQQ140920C00077000`), it compares the last contract row and last valid bid against the underlying-price trading-session calendar and the dates on which the symbol's option-chain files still contain rows.
- The replay workflow now downloads the pinned source's underlying-price Parquet files, compiles the diagnostic, runs it for SPY and QQQ, and includes the JSON/CSV output in the existing replay artifact. This diagnostic is non-gating: it cannot make missing quotes executable or turn an unresolved replay into a valid P/L result.
- Added a synthetic Parquet unit test asserting that five underlying sessions after a contract's last row are reported when symbol-level option rows continue on those dates. Unit workflow paths/compile coverage were updated.
- Changes are isolated on a PR branch to avoid triggering broad main-branch workflow fan-out. The next gate is actual PR CI and then the replay artifact: record the exact underlying-session counts and whether the option source continues on those dates. No new source-gap result, strategy return, or paper-trading approval is claimed until the run completes and outputs are inspected.
- Research interpretation remains conservative: an underlying trading session with no row for a specific option contract is evidence of a contract-history gap relative to this source's stated row convention, but it does not establish that the option had a positive or executable bid. No exit threshold or expiration policy was changed.


### CI failure and correction — 2026-10-13 22:54Z

- PR #30 CI was inspected directly, not assumed successful. Initial runs: [LEAPS unit tests run 38480676716](https://github.com/eklu654/Trading-Bot/actions/runs/38480676716) failed 1/20 tests; [repository research tests run 38480676732](https://github.com/eklu654/Trading-Bot/actions/runs/38480676732) failed 1 test and passed 170.
- Root cause was output normalization, not the underlying-session counts: DuckDB returned Pandas `Timestamp` values, and JSON emitted `2020-01-03T00:00:00`, while the test and report contract expected ISO calendar dates (`2020-01-03`). The underlying-session synthetic result itself correctly found 5 sessions after the contract cutoff.
- Fixed JSON date normalization in `research/audit_adaptive_leaps_source_discontinuity.py` in commit `f44d704c9fa8f7cada7235716109acdc694a2d18`. Await the new commit's CI before calling the fix verified. Do not merge PR #30 while checks are failing.
- Remaining known caution: CI also surfaces a pre-existing Pandas FutureWarning in `research/backtest_etf001.py:175`; it was not the failure cause and is out of scope for this LEAPS patch.


### Latest verification checkpoint — 2026-10-13 23:23Z

- Confirmed PR #30 head is `40e146ec2b32b6f37a3434c13562d471a2bde6df`, PR state is open, and GitHub reports it mergeable with no branch conflict.
- Confirmed the focused LEAPS unit workflow `38482852634` completed successfully.
- Confirmed the broad repository `research-tests` workflow `38482852636` completed successfully. The date-normalization fix has therefore cleared both the focused LEAPS suite and the repository suite.
- No full chronological replay was triggered by these PR checks: the replay workflow currently runs on manual dispatch or pushes to main when selected paths change. This PR has not been merged, and no new source-discontinuity artifact has been inspected yet.
- **Next gate:** trigger the replay workflow after review/merge, then inspect the uploaded source-discontinuity CSV/JSON, the four replay summaries, and the terminal-equity quality gate. Do not merge solely on green unit tests if policy requires the new source audit to be observed first; do not state the audit's real-data finding until the artifact exists.
- Existing known blocker remains unchanged: the prior full replay failed terminal-equity reconciliation in all four cases because expired positions remained unresolved. The source-date diagnostic is investigation, not a fix to that accounting/contract lifecycle issue.


### PR #30 merged and replay gate — 2026-10-13 23:27Z

- PR [#30](https://github.com/eklu654/Trading-Bot/pull/30) merged successfully by squash at `599c61cbc2b05fdbc372718b17aca7ffc753d281`; pre-merge LEAPS unit and broad repository CI both passed on reviewed head `7d110bb01334264c67af64fb14ae61707c38e3c8`.
- Verified on `main` that `.github/workflows/adaptive-leaps-replay.yml` includes the pinned SPY/QQQ underlying-price downloads, compiles `research/audit_adaptive_leaps_source_discontinuity.py`, and runs the SPY/QQQ diagnostics. The new diagnostic file is present on main.
- Merge changes the replay workflow path, so the workflow's main-branch path filter should enqueue a replay automatically. The GitHub connector's commit-run listing is PR-only and returned no runs for the merge commit; this is not evidence that no push run exists. A direct Actions API listing must confirm the concrete run ID and status.
- Research gate remains: inspect the uploaded `adaptive-leaps-chronological-replay` artifact, source discontinuity CSV/JSON, and all four summaries/ledgers. The audit is `continue-on-error` diagnostic by design; its output must be reviewed even if terminal-equity gate fails. Existing unresolved expiration/terminal-equity handling remains a separate issue; no return claims until all four cases reconcile.


### Workflow trigger audit — 2026-10-13 23:34Z

- Follow-up review found the replay workflow's `push.paths` filter listed the quote-continuity audit but omitted `research/audit_adaptive_leaps_source_discontinuity.py`. The source audit is invoked by the workflow, but a future edit to that script alone would not trigger a replay.
- Added the missing source-audit path to the workflow filter on branch `leaps/replay-workflow-path-filter` (commit `c6d7777486f98539e1f20e2667b409e1dc61b93f`). This is a trigger-maintenance fix only; no strategy logic or historical results changed.
- Post-merge replay run/artifact status is still not confirmed by the available GitHub connector calls. The prior conclusion that a run was automatically enqueued was an expectation from path-filter behavior, not a verified run ID. Do not report that replay ran until a concrete Actions run and artifact are inspected.


### PR #31 merged; trigger fix validated — 2026-10-14 00:00Z

- PR [#31](https://github.com/eklu654/Trading-Bot/pull/31) merged by squash at `1f4702accc3172304fad5c68628ce4dc2cc4a31b`.
- Repository research test run `38485097629` (workflow `research-tests`, run number 1959) completed successfully on PR head `504134509f94207c8793a4da6bfeaa7ed7be1b65`.
- Confirmed on `main` that the replay workflow push path filter now includes both `research/audit_adaptive_leaps_quote_continuity.py` and `research/audit_adaptive_leaps_source_discontinuity.py`. PR #31 changed only the replay workflow trigger list and this audit document.
- Checked the merge commit's workflow-run listing; it returned no runs. This connector result is inconclusive (not a repository-wide Actions listing) and does not establish that a post-merge replay ran or did not run. The concrete post-merge replay run ID and artifact remain unverified.
- Next step is still to obtain a concrete run ID for `Adaptive LEAPS Chronological Replay`, inspect `adaptive-leaps-chronological-replay` artifact contents and source-discontinuity CSV/JSON, then reconcile all four replay summaries. Existing unresolved expiration/terminal-equity handling remains a hard stop for profitability conclusions and paper trading.


### Follow-up continuation checkpoint — 2026-10-13

- Re-read the current main workflow and source-discontinuity diagnostic. The workflow invokes SPY and QQQ checks against the pinned underlying Parquet files and uploads the full replay artifact even when diagnostic/replay steps fail.
- Reviewed the diagnostic SQL: it compares the flagged contract's last row and last valid bid against underlying trading dates through expiration, and separately counts dates with/without symbol-level option rows. It explicitly does not claim missing quotes were executable.
- Re-attempted to establish the post-merge replay run/artifact from available connector calls. The connector's permitted public-fetch endpoint does not expose the Actions run listing needed here; no verified run ID or artifact contents were obtained in this checkpoint. Do not interpret this as evidence that the workflow did not run.
- No historical return or terminal-equity figures were changed or newly validated. Outstanding gates remain: concrete replay run + artifact inspection, all four summary/ledger reconciliations, and correct expired-position terminal handling.


### 2026-10-14 04:50Z — Replay receipt PR merged; concrete post-merge run verified

- PR [#32](https://github.com/eklu654/Trading-Bot/pull/32) merged by squash as `f32d2d00fd394e0b5a117a23128b33a7988ce8ae`. Its research-tests run [38502124462](https://github.com/eklu654/Trading-Bot/actions/runs/38502124462) completed successfully on reviewed PR head `1dc73a1da73fdbfb93de2fd1e9d789b0449a0b4b`.
- The merged replay workflow now grants `contents: write` and writes `docs/LEAPS_REPLAY_LATEST_RUN.md` at the end of each replay job, including failures. The receipt path is not in the replay workflow's push filter, preventing recursive replay triggers.
- Direct Actions API run listing now works with `per_page=100` and filtering locally by workflow name/path. Confirmed the merge triggered actual chronological replay run [38513353493](https://github.com/eklu654/Trading-Bot/actions/runs/38513353493), event `push`, head SHA `f32d2d00fd394e0b5a117a23128b33a7988ce8ae`, created at 2026-10-14 04:49:06Z. At this checkpoint it is `in_progress`; no artifact or result is claimed yet.
- Previous latest replay [38492986874](https://github.com/eklu654/Trading-Bot/actions/runs/38492986874) completed with `failure`, consistent with the known terminal-equity quality gate. Need inspect its jobs/artifact if useful, then prioritize new run 38513353493.
- Next: poll the concrete run ID, confirm replay commands and artifact upload, download artifact, inspect both source-discontinuity reports and all four summaries/ledgers, and append exact reconciliation results here. Existing rule stands: unresolved expiry/terminal marks mean no valid P/L claim and no paper-trading approval.


### 2026-10-14 04:53Z — Replay run 38513353493 inspected; receipt push race found

- Post-merge replay [38513353493](https://github.com/eklu654/Trading-Bot/actions/runs/38513353493) completed with `failure` at the terminal-equity quality gate; the 23-file artifact uploaded successfully as artifact [11870348302](https://github.com/eklu654/Trading-Bot/actions/runs/38513353493/artifacts/11870348302), SHA-256 `7679dffd79782804c510b0e44a3ff3d4283e3098150182cc02dd2a722cb446a7`.
- Independently checked all four summaries and ledgers. SPY: 4,514 observations (2008-01-02–2025-12-12), one buy, zero completed exits, cash $3,930, terminal equity unavailable, 4,345 exit rejections. QQQ: 3,700 observations (2011-03-23–2025-12-15), nine transactions/four completed exits, cash $6,025, terminal equity unavailable, 2,840 exit rejections. Both theoretical and $5,000 cash-constrained outputs are identical in each symbol; the one-contract baseline never differentiates their sizing.
- In all four outputs, transaction cash reconciles and fills occur after signal observations. All four remain `incomplete_terminal_mark`; SPY's last valid bid is 2008-08-11 (50 DTE) and QQQ's is 2014-03-11 (193 DTE). Source-discontinuity diagnostic confirms symbol-level option rows continue after both last-valid-bid dates; for QQQ, 133 underlying sessions occur after the contract's last row. These findings support a source/contract-history completeness problem, not a defensible mark or proven executable exit.
- The receipt step wrote its local file but `git push origin HEAD:main` failed non-fast-forward because main advanced during replay. The run and artifact are still identified above. PR [#33](https://github.com/eklu654/Trading-Bot/pull/33) adds `git fetch origin main` and `git rebase origin/main` before pushing the receipt; this is workflow bookkeeping only. CI is pending at this note's timestamp.
- Next gate: validate/merge PR #33, confirm a subsequent replay writes `docs/LEAPS_REPLAY_LATEST_RUN.md` successfully, and continue investigating data completeness/expiration handling. No historical return claim or paper-trading approval.


### 2026-10-14 04:56Z — Receipt race fixed and verified on a new replay

- PR [#33](https://github.com/eklu654/Trading-Bot/pull/33) merged as `b64c8f7cd7d51071b1ad024fe4b88517bb0acc6b`. Research-tests run [38513692735](https://github.com/eklu654/Trading-Bot/actions/runs/38513692735) passed on the final reviewed PR head `9c0a2bcf511d311fe3c55fa7d9cbd6aa667fde96`.
- Follow-up chronological replay [38513781718](https://github.com/eklu654/Trading-Bot/actions/runs/38513781718) completed with `failure` at the expected terminal-equity gate, but the receipt step completed successfully. The workflow-created [`docs/LEAPS_REPLAY_LATEST_RUN.md`](LEAPS_REPLAY_LATEST_RUN.md) now records run ID `38513781718`, run number 17, commit `b64c8f7cd7d51071b1ad024fe4b88517bb0acc6b`, and the direct Actions URL. This verifies the non-fast-forward fix.
- Artifact [11869994334](https://github.com/eklu654/Trading-Bot/actions/runs/38513781718/artifacts/11869994334) uploaded successfully (23 files; SHA-256 `024f88dab9abb85e65b31c20dda845986ec3a2dc3355d1417a4602998c97927d`). The source-hash manifest matches the previous replay's 37 lines exactly, so the pinned Parquet inputs are unchanged.
- The replay's strategy result remains invalid: all four summaries still report unresolved terminal marks; no final equity or valid return is available. The receipt solves run discovery, not the option-data/expiration-lifecycle problem.
- Next research step should be a separately labeled cross-source check of the two flagged contract histories against the preserved `data-v1` option-chain copy from `lambdaclass/options_portfolio_backtester`. That copy has pinned SHA-256 hashes, but its notice says the original upstream disappeared and its sourcing was undocumented; therefore it is an alternate preserved copy, not independent exchange-data validation. Do not switch the frozen baseline or infer missing quotes are executable without that check.


### 2026-10-14 04:59Z — Alternate preserved dataset confirms the same contract-history cutoffs

- PR [#34](https://github.com/eklu654/Trading-Bot/pull/34) merged as `8f177b1f430ac52689f03899b7a8cb402921670e`; focused LEAPS tests [38514116088](https://github.com/eklu654/Trading-Bot/actions/runs/38514116088) and broad repository tests [38514116092](https://github.com/eklu654/Trading-Bot/actions/runs/38514116092) passed.
- The new pinned alternate-source audit [run 38514197653](https://github.com/eklu654/Trading-Bot/actions/runs/38514197653) completed successfully and uploaded artifact [11870104431](https://github.com/eklu654/Trading-Bot/actions/runs/38514197653/artifacts/11870104431), SHA-256 `f1b67b74b77f6dd67ef79eb67154e5aff1dc3303826f7bab726d3726193a2e3f`. Both SPY/QQQ Parquet downloads matched the expected SHA-256 hashes in the pinned `data-v1` release.
- SPY `SPY080930C00148000`: 189 rows, last row on expiration 2008-09-30, but last positive bid on 2008-08-11 (50 DTE), bid $0.02 / ask $0.05, then 35 rows without a positive bid. QQQ `QQQ140920C00077000`: 78 rows, last row 2014-03-12, last positive bid 2014-03-11 (193 DTE), bid $6.70 / ask $7.67, then no later contract rows.
- These row counts, dates, and last-bid prices match the primary replay source exactly. This shows the cutoff is reproduced in the alternate preserved copy; it does **not** independently verify that the quotes were absent in the actual market, because the release notice says the original upstream disappeared and its sourcing was undocumented.
- Research conclusion unchanged: source continuity is not resolved. Next useful validation is an independently sourced historical chain (e.g. an account-accessible provider for QQQ 2014; SPY 2008 needs coverage beginning before the cutoff). Do not impute a stale mark, use intrinsic value as a convenient patch, or tune exit DTE against this source defect. The replay remains invalid and not approved for paper trading.


### 2026-10-14 05:09Z — Row-level source comparison completed; both preserved copies are identical for flagged contracts

- PR [#36](https://github.com/eklu654/Trading-Bot/pull/36) added QQQ's 2013 file because the first row-level attempt compared only the 2014 file and consequently showed 30 alternate-only dates. PR [#37](https://github.com/eklu654/Trading-Bot/pull/37) quoted the multi-file glob so Bash would not split it into multiple CLI arguments. Both changes passed repository CI before merge.
- Corrected audit [run 38514997928](https://github.com/eklu654/Trading-Bot/actions/runs/38514997928) completed successfully; artifact [11871486428](https://github.com/eklu654/Trading-Bot/actions/runs/38514997928/artifacts/11871486428), SHA-256 `cf4666764b59f5998dedf6e62427bcf871ee28e3510235aec8aaf68e8257c93a`.
- Full row-by-row comparison across the primary pinned yearly files and the alternate `data-v1` files now shows exact core quote-history matches for both flagged contracts:
  - SPY: 189/189 dates shared, zero date gaps, zero bid-validity disagreements, zero bid/ask value differences. Last positive bid remains 2008-08-11 at $0.02 bid / $0.05 ask; 35 later contract rows have no positive bid.
  - QQQ: 78/78 dates shared after including 2013 and 2014, zero date gaps, zero bid-validity disagreements, zero bid/ask value differences. Last positive bid remains 2014-03-11 at $6.70 bid / $7.67 ask; the last contract row remains 2014-03-12.
- Therefore, the two preserved datasets are not independent confirmations; for these contracts they reproduce the same quote history exactly. The result rules out a mismatch between these two copies but does not establish whether their common upstream missed quotes that existed in the market.
- The data blocker is now narrowed: further useful resolution requires a genuinely independent vendor/source or documented exchange data. OptionsDX publicly lists QQQ coverage for 2014 and SPY only from 2010 onward, so it may independently validate QQQ but cannot by itself validate the 2008 SPY contract. Full historical downloads require selecting/obtaining the relevant product data; no external account or paid data was accessed here.
- No strategy result is approved: all four LEAPS replay cases still lack reconciled terminal equity. Do not substitute stale marks, intrinsic value, or a DTE rule tweak for missing quote evidence.


### 2026-10-14 05:10Z — Expiration accounting decision: do not use expiry payoff to hide a failed scheduled exit

- Reviewed the replay loop and lifecycle code. The frozen rule schedules a sale at the next option-chain observation once DTE is at or below 30. If that quote is absent/invalid, the position remains open and exit attempts are rejected; the engine deliberately leaves terminal equity unavailable rather than silently using zero or a stale bid.
- Official product guidance: ETF options are American-style and exercise results in delivery of the underlying ETF on T+1 ([OCC ETF option specifications](https://www.theocc.com/clearance-and-settlement/clearing/etf-options)); one standard contract generally controls 100 shares ([OCC equity option specifications](https://www.theocc.com/clearance-and-settlement/clearing/equity-options-product-specifications)). Exercise-by-exception is an administrative clearing procedure, and brokers may apply their own cutoffs or override exercise decisions ([Options Industry Council exercise FAQ](https://www.optionseducation.org/referencelibrary/faq/options-exercise)).
- Consequently, marking an expired call at `max(underlying close - strike, 0) × 100` is only a contractual expiration payoff under a defined settlement/position-liquidation assumption. It is not evidence that the strategy's scheduled DTE-30 sale could have been executed. The QQQ strike obligation may also exceed the $5,000 account's available cash; actual exercise/forced liquidation cannot be assumed without an explicit account policy.
- Decision: keep the current quality gate and frozen baseline unchanged. Do **not** patch terminal equity with intrinsic value or automatic exercise just to make the run pass. Resolve the missing pre-expiry exit quotes with independent historical data, or separately predeclare and test an expiry-fallback policy as a different strategy variant. Until then, the baseline has no valid terminal return and is not eligible for paper trading.
- Repository-wide research-tests run [38515124150](https://github.com/eklu654/Trading-Bot/actions/runs/38515124150) passed after the documentation update.


### 2026-10-14 05:13Z — Reduce unrelated TQQQ matrix fan-out from LEAPS feature branches

- PR [#38](https://github.com/eklu654/Trading-Bot/pull/38) merged as `07d735ba5ca2e057ce7ba5ac3e4b622c16ed7ad7` after repository CI [38515402664](https://github.com/eklu654/Trading-Bot/actions/runs/38515402664) passed.
- The `Actual TQQQ partial DMA matrix` workflow previously filtered by research-file paths but had no `push.branches` restriction, so every LEAPS feature-branch edit to `research/*.py` launched an unrelated matrix run. Automatic push runs are now restricted to `main`; the existing path filter and explicit manual `workflow_dispatch` remain intact.
- This is CI hygiene only and does not change ETF results or LEAPS logic.


### 2026-10-14 06:08Z — Rechecked workflow state and screened a genuinely separate historical-data provider

- The documentation update's broad CI run [38515491403](https://github.com/eklu654/Trading-Bot/actions/runs/38515491403) has now completed **successfully**. No LEAPS-related CI failure is currently indicated in the newest run listing.
- The latest chronological replay remains [run 38513781718](https://github.com/eklu654/Trading-Bot/actions/runs/38513781718), conclusion **failure**, artifact [11869994334](https://github.com/eklu654/Trading-Bot/actions/runs/38513781718/artifacts/11869994334). It predates the later audit/documentation-only commits and still has no valid terminal equity; those later commits did not change the replay engine or input data, so there is no evidence they would fix the result.
- Screened HistoricalData.net as a potential genuinely separate provider. Its public documentation describes EOD US option chains from February 2002, including bid/ask fields, and a full archive listed at $590 one-time; however, it explicitly warns that the archive-wide start date does not establish SPY or QQQ contract-specific coverage. Its public coverage endpoint only checks the latest options session, not historical contract/date coverage. Public API checks confirmed a current SPY options session, but cannot verify the target 2008 SPY or 2014 QQQ contract histories. References: [archive and pricing](https://historicaldata.net/options.html), [SPY coverage scope](https://historicaldata.net/options/SPY.html), [API coverage limitations](https://historicaldata.net/api.html).
- Purchase decision: **do not buy the $590 archive yet**. First request written confirmation from the provider for both exact contract symbols/date windows and whether daily bid/ask rows are retained for expired contracts with zero/blank bids. This is a narrow coverage question; a broad archive purchase is not justified until the provider confirms it can answer it.
- No new source has been downloaded or represented as independent evidence. The two pinned copies remain byte/row consistent for the flagged contracts, and this independent-provider path is only a candidate pending confirmation.
- Research remains frozen: do not adjust DTE, invent quotes, apply intrinsic value as a missing-exit substitute, or claim a valid return until terminal positions reconcile from supported market data and an explicit expiry policy.


### 2026-10-14 06:11Z — Prepared a bounded independent-data coverage request

- Added [docs/LEAPS_INDEPENDENT_DATA_COVERAGE_REQUEST.md](LEAPS_INDEPENDENT_DATA_COVERAGE_REQUEST.md) with exact SPY/QQQ contract identifiers, required date windows, questions about blank/zero bids versus absent rows, quote timestamps/sizes, source provenance, licensing, and a pre-purchase acceptance checklist.
- The request is deliberately scoped to two contracts; it does not authorize a purchase. HistoricalData.net remains only a candidate until it confirms both exact histories and can establish that its records are independent of the pinned data-v1 mirror.
- This converts the vague next step into a concrete, auditable coverage request. No email was sent and no paid data was accessed.


### 2026-10-14 06:14Z — Prioritize an OPRA-stated source for the narrow contract check

- Further public-source screening found HistoricalOptionData.com / DeltaNeutral LLC, whose documentation says its EOD option records come from OPRA/NBBO and include bid/ask, quote date, expiration, strike, and option symbol. Its product pages list an SPY-specific archive beginning in 2005 at $455 and a 2002-present full-market Level 1 archive at $1,150. These are advertised product prices, not a quote for the minimum records needed.
- This is a stronger candidate for a narrowly scoped inquiry than purchasing HistoricalData.net's $590 full archive immediately, but the exact SPY 2008 and QQQ 2014 contract rows and their missing/zero-bid handling remain unconfirmed. The vendor's public claims are not treated as validation evidence. See the updated request at [docs/LEAPS_INDEPENDENT_DATA_COVERAGE_REQUEST.md](LEAPS_INDEPENDENT_DATA_COVERAGE_REQUEST.md).
- HistoricalData.net's published methodology says the historical options archive combines archived records with a separate daily capture begun 2026-08-06; its public independent quote reconciliation covers recent sessions and selected 2022 samples, not these target 2008/2014 rows. Thus its archive is a candidate source but not yet proven independent for the specific old records.
- Decision unchanged: no purchase and no strategy change until written exact-contract coverage and a small sample are available. If the vendor cannot supply the relevant rows or identify source provenance, do not spend on it for this audit.


### 2026-10-14 06:12Z — Fix the broader main-push workflow fan-out

- PR [#39](https://github.com/eklu654/Trading-Bot/pull/39) merged as `007e46ef2f46259d285e966538b3fcb27096316e` after repository test run [38520664339](https://github.com/eklu654/Trading-Bot/actions/runs/38520664339) passed.
- Root cause confirmed: 10 long-running TQQQ/failed-bounce workflows had only `push.branches: [main]` and no `paths` filter. A LEAPS documentation-only commit therefore launched all 10 jobs. Each now has exact entrypoint/shared-helper and dependency-file path filters; explicit `workflow_dispatch` remains. The broad `research-tests` workflow remains unchanged.
- This is broader than PR #38's branch-only fix. It prevents documentation-only updates and unrelated LEAPS code from starting those particular jobs, while changes to each workflow's listed research inputs still trigger it. No trading logic or result calculations changed.
- The batch started by the prior docs-only push was not a LEAPS replay; it was unrelated ETF/TQQQ work. No conclusion from those runs is used in the LEAPS strategy assessment.


### 2026-10-14 06:14Z — Narrowed the independent-data inquiry to a low-cost symbol-month quote

- HistoricalOptionData.com documents an ONESYMBOL order assistant priced at $4.95 × (symbol-months)^0.846, with partial months rounded up. A rough full-lifecycle request would cover 9 SPY months (Jan–Sep 2008) plus 11 QQQ months (Nov 2013–Sep 2014), or 20 symbol-months; the published formula implies about **$62.41** before any special-order fees or coverage/pricing adjustments. This is only an estimate, not a quote or evidence the exact rows exist.
- This is materially more proportionate than buying the vendor's advertised $455 SPY archive or $1,150 full-market archive. The coverage request document now includes the estimate, exact contracts, full-lifecycle windows, and an acceptance checklist. No order has been submitted.
- The workflow fan-out fix is merged. The PR's test run [38520664339](https://github.com/eklu654/Trading-Bot/actions/runs/38520664339) passed. The immediate merge-triggered test run was superseded/cancelled by the following documentation commit, and the latest main test run [38520775104](https://github.com/eklu654/Trading-Bot/actions/runs/38520775104) was still running at this note. No TQQQ/failed-bounce jobs were triggered by the workflow-fix merge or subsequent documentation push, confirming the path filters are doing their intended job so far.


### 2026-10-14 06:14Z — Remove duplicate heavyweight attribution from the broad test workflow

- PR [#40](https://github.com/eklu654/Trading-Bot/pull/40) merged as `701d729ea975aaaff97475f46266aa0ec8084d5e` after CI [38520926283](https://github.com/eklu654/Trading-Bot/actions/runs/38520926283) passed.
- The broad workflow now runs pytest only. The full `tqqq_three_layer_event_attribution.py` analysis remains in its dedicated workflow, which is path-filtered to the entrypoint, cost-robustness script, shared execution helper, and dependency files. This avoids duplicating that analysis on every documentation push without dropping the dedicated run when its inputs change.
- The latest main documentation validation before this PR, [38520871811](https://github.com/eklu654/Trading-Bot/actions/runs/38520871811), passed. After PR #39's scoped-trigger fix, no TQQQ/failed-bounce workflows appeared for subsequent documentation-only pushes; the broad test run is the only expected validation job for the docs changes.
- The LEAPS data request is still only a drafted inquiry. No vendor was contacted, no data was purchased, and the replay's terminal-equity blocker remains unresolved.


### 2026-10-14 06:26Z — Screened a no-cost historical options source; not accepted as independent validation

- Screened OnclickMedia as a potential free spot-check. Its public pages describe an EOD options archive and REST API, but the backtester API's stated options-data range begins 2013-01-02, so it cannot establish the missing 2008 SPY contract history. Its About page says the options archive aggregates Yahoo Finance, community channels, and other free providers and warns of gaps/inconsistencies; it does not identify contract-level source provenance.
- Result: do not count OnclickMedia as a proven independent source for either flagged contract. It might provide a low-cost exploratory cross-check for QQQ in 2014, but a match or mismatch alone would not resolve source independence or quote executability. No external API query, data download, account creation, purchase, or contact was made.
- This leaves the previously documented ONESYMBOL quote inquiry as the best proportionate next validation path: request written confirmation for exact SPY 2008 and QQQ 2014 contract-month coverage, provenance, and treatment of absent/blank/zero-bid rows before authorizing any spend. The current estimate (~$62.41 for 20 symbol-months) remains an estimate, not a quote.
- Replay and accounting gates remain unchanged. No terminal equity, profitability, or paper-trading conclusion is inferred from this source screen.


### 2026-10-14 06:30Z — Explicitly measured quote availability in the frozen DTE-30 exit window

- PR [#41](https://github.com/eklu654/Trading-Bot/pull/41) merged as `acb339cd34b3b7516a187a3aec3c61877d5f7bfa`. Both the focused LEAPS unit tests [38522462349](https://github.com/eklu654/Trading-Bot/actions/runs/38522462349) and full research test suite [38522462332](https://github.com/eklu654/Trading-Bot/actions/runs/38522462332) passed.
- Updated audit [run 38522551689](https://github.com/eklu654/Trading-Bot/actions/runs/38522551689) passed; artifact [11874985365](https://github.com/eklu654/Trading-Bot/actions/runs/38522551689/artifacts/11874985365), SHA-256 `04f283ba6b2bccb3b2b7889d7b653ebaa4045243abb7a7a86531e084198c026d`.
- SPY `SPY080930C00148000`: nominal expiration 2008-09-30; calendar DTE-30 threshold 2008-08-31. The preserved source contains 21 contract observations from the threshold through expiration, but **zero positive-bid rows and zero valid sell quotes** in that entire window. Its last positive bid is $0.02 on 2008-08-11.
- QQQ `QQQ140920C00077000`: nominal expiration 2014-09-20; DTE-30 threshold 2014-08-21. The preserved source's last contract row is 2014-03-12, **192 calendar days before expiration** and 162 days before the DTE-30 threshold. There are zero observations in the scheduled exit window.
- This separates the failure modes: SPY has rows but no sellable quote by the frozen exit window; QQQ's preserved history ends well before the exit window. These findings are still only about the two matching preserved copies, not an independent exchange record or proof of actual market liquidity.
- No replay logic, DTE rule, or accounting fallback changed. The latest LEAPS replay still cannot support a valid terminal return until an independent data source resolves these exact quote gaps or a separate predeclared policy is tested.


### 2026-10-14 06:34Z — Fixed remaining broad matrix triggers and made active LEAPS replay discoverable

- PR [#42](https://github.com/eklu654/Trading-Bot/pull/42) merged as `98cf56141bc641c5d312e79473b003f73210f90f` after research-tests [38522774735](https://github.com/eklu654/Trading-Bot/actions/runs/38522774735) passed. The two remaining TQQQ partial-DMA workflows had broad `research/*.py` globs that still launched on the LEAPS audit script; their automatic triggers now name only their entrypoints and shared helpers. Their own workflow files were removed from their path filters so trigger-only edits do not launch another matrix. Manual dispatch remains available.
- After PR #42 merged, only `research-tests` ran for the workflow-only change; neither TQQQ partial-DMA matrix was triggered. This closes the two remaining broad-glob cases observed in the run listing.
- PR [#43](https://github.com/eklu654/Trading-Bot/pull/43) merged as `56888f964cb9d96f83edf26730d7a9131c264663` after research-tests [38522895854](https://github.com/eklu654/Trading-Bot/actions/runs/38522895854) passed. The LEAPS replay workflow now publishes `docs/LEAPS_REPLAY_LATEST_RUN.md` at start via the GitHub Contents API, then updates the final status after the quality gate. SHA-aware retries handle concurrent documentation writes; receipt writes are limited to main, and start-receipt failure does not block the replay.
- Verification: new replay run [38522970928](https://github.com/eklu654/Trading-Bot/actions/runs/38522970928), run number 18, wrote its ID/URL and `Status: in_progress` to the receipt while the run was still active. This resolves the previous discoverability gap; the receipt is no longer final-step-only.
- Run 18 is still in progress. Its terminal accounting must be inspected when it finishes; changing the receipt mechanism does not change the unresolved missing-quote problem or authorize any strategy performance conclusion.


### 2026-10-14 06:36Z — Replay run 18 completed; terminal equity remains unresolved

- Run [38522970928](https://github.com/eklu654/Trading-Bot/actions/runs/38522970928), run number 18, completed with **failure at the terminal-equity quality gate**. Artifact [11875056032](https://github.com/eklu654/Trading-Bot/actions/runs/38522970928/artifacts/11875056032), SHA-256 `5fcce4e99b8b9455756e9bfbb7bfd0c238bf41bc788c2e4275bb303bb4eff5a6`.
- All four replay processes and source diagnostics completed. All four strategy summaries remain `incomplete_terminal_mark`; the quality gate correctly rejected them. Transaction cash reconciliation difference is $0 and all recorded fills occur after their signal observations, but neither fact establishes terminal equity.
- SPY theoretical and $5,000 cash-constrained cases are identical: cash $3,930; final equity unavailable; one entry at $10.70 ask ($1,070) on 2008-01-03; zero completed trades; 4,345 rejected exit attempts. Terminal contract `SPY080930C00148000` expired 2008-09-30, but the replay carries it through the last dataset observation 2025-12-12 (6,282 calendar days past expiration). Last valid bid mark: 2008-08-11. There are 4,369 held observations without a valid bid mark. The observed -21.38% drawdown is incomplete and must not be treated as the true maximum drawdown.
- QQQ theoretical and $5,000 cash-constrained cases are identical: cash $6,025; final equity unavailable; four completed trades; 2,840 rejected exit attempts. The unresolved terminal contract `QQQ140920C00077000` was bought on 2013-12-23 at $12.01 ask ($1,201) and expired 2014-09-20, but remains open in the replay through 2025-12-15 (4,104 calendar days past expiration). Last valid bid mark: 2014-03-11; 4,297 calendar days since that mark; 2,954 held observations without a valid bid mark. The observed -13.2505% drawdown is likewise incomplete.
- Cash-constrained and theoretical results being identical here is not evidence of feasibility or performance; both have zero rejected entries, while the terminal positions remain unvalued. Do not report $3,930 or $6,025 as final account equity.
- The updated start/final receipt mechanism worked end-to-end: `docs/LEAPS_REPLAY_LATEST_RUN.md` showed run 18 while it was active, then updated to `Final job status at receipt step: failure` after the gate failed.
- PR [#44](https://github.com/eklu654/Trading-Bot/pull/44) merged as `499114e9570864ed2ed6b1c2deff53ec5c14bf0e` after research-tests [38523116687](https://github.com/eklu654/Trading-Bot/actions/runs/38523116687) passed. Full tests now trigger on workflow/source/test/data/dependency/config changes, not Markdown-only notes or receipt writes. This prevents receipt updates from launching redundant full test runs.


### 2026-10-14 06:39Z — Broader quote-continuity diagnostics distinguish zero-bid rows from omitted contract rows

- Run 18's continuity artifacts show the SPY flagged contract has 189 rows through expiration, 145 valid-bid rows, and 44 invalid/missing-bid rows. After its last positive bid on 2008-08-11, the source has 35 contract rows through 2008-09-30, but no valid bid. At the source-symbol level, all 35 underlying sessions have other SPY option rows; this is not a broad SPY-chain outage.
- The QQQ flagged contract has 78 rows, 77 valid-bid rows, and one invalid/missing-bid row; its last row is 2014-03-12. After that, 133 underlying sessions run through the last trading session before its 2014-09-20 expiration, and the source contains other QQQ option rows on every one of those sessions. The specific contract row is absent throughout that period.
- Cohort-level context: SPY has 8,930 eligible contracts, 8,231 fully observed to expiration, and 133 fully observed contracts whose last valid bid is more than 30 calendar days before expiration. In the 2008 SPY cohort, 45 of 103 eligible contracts fall into that late-last-bid group. QQQ has 6,158 eligible contracts, 5,535 fully observed, and 335 fully observed contracts with last valid bid more than 30 days before expiration. These counts are diagnostics, not proof that every zero bid is erroneous; zero bid can reflect genuine lack of executable demand.
- Interpretation: the SPY case is a sustained zero/invalid-bid problem after 50 DTE; the QQQ case is contract-specific row disappearance 193 DTE after the last valid bid, despite continued QQQ chain coverage. Independent vendor rows are still needed to distinguish real illiquidity from source omission.
- PR [#45](https://github.com/eklu654/Trading-Bot/pull/45) merged as `52f0d9ef971ae226ffcebef1741d671cc3cc8431` after research-tests [38523385078](https://github.com/eklu654/Trading-Bot/actions/runs/38523385078) passed. Regression tests now guard the scoped matrix triggers, docs-only test filtering, and replay-receipt non-recursion.


### 2026-10-14 06:44Z — QQQ 2014 cutoff is a cohort-wide pattern; intrinsic-basis audit queued

- Further analysis of run 18's full QQQ contract continuity CSV found **80 contracts expiring in 2014** with the same last positive bid date (2014-03-11) and same final contract row date (2014-03-12). Their expirations span 2014-06-21, 2014-06-30, 2014-09-20, 2014-09-30, 2014-12-20, and 2014-12-31. Every one has exactly one row after its last positive bid. This is a systematic cohort cutoff, not a single-contract anomaly.
- Public historical QQQ data reports an unadjusted close of $90.22 on 2014-03-11 ([Yahoo Finance history](https://finance.yahoo.com/quote/QQQ/history/?filter=history&frequency=1d&includeAdjustedClose=true&interval=1d&period1=946684800&period2=1679059200)). The preserved QQQ 77 call row on that date has bid $6.70 / ask $7.67; if both series are on the same unadjusted basis, intrinsic is $13.22 and even the ask is below intrinsic. The public dataset documentation describes the underlying file as OHLCV but does not specify its raw/adjusted basis, so this is a price-basis warning pending direct inspection—not yet a confirmed quote defect.
- PR [#46](https://github.com/eklu654/Trading-Bot/pull/46) merged as `3ea1fe7037cd8d28ac97d639b6aad71a9430732a` after focused and broad tests [38523872038](https://github.com/eklu654/Trading-Bot/actions/runs/38523872038) and [38523872217](https://github.com/eklu654/Trading-Bot/actions/runs/38523872217) passed. New audit [run 38523952499](https://github.com/eklu654/Trading-Bot/actions/runs/38523952499) is queued to inspect the actual pinned underlying price fields and compare them with the preserved option quote fields. This diagnostic cannot impute prices or approve terminal equity.


### 2026-10-14 06:45Z — Underlying price-basis diagnostic completed; QQQ quote integrity is now a separate blocker

- Intrinsic-bound audit [run 38523952499](https://github.com/eklu654/Trading-Bot/actions/runs/38523952499) passed and produced artifact [11874402653](https://github.com/eklu654/Trading-Bot/actions/runs/38523952499/artifacts/11874402653), SHA-256 `6cc0584996c11a035fed6309bce6cbe71d8bcbcfa356db4090de3d23feea748e`. Both pinned underlying files contain separate `close` and `adjusted_close` fields.
- QQQ entry quote (2013-12-23): $77 call bid $11.52 / ask $12.01; raw close $87.41 implies $10.41 intrinsic, so both quotes clear the lower bound. On 2014-03-11, the same contract's bid/ask are $6.70 / $7.67 while raw close is $90.22, implying $13.22 intrinsic: **both bid and ask are below intrinsic**. Against adjusted close $82.135, intrinsic is $5.135 and the quotes clear the bound. The two price fields therefore give conflicting validity results.
- SPY's flagged contract does not violate the lower bound on either checked date using raw close: it is out of the money at entry (close $144.86 vs strike $148) and at its last positive bid (close $130.71).
- Interpretation: this does not prove whether the QQQ option quote is wrong or premium adjustment methodology differs; the public dataset documentation does not specify the option-premium adjustment basis. But a standard listed option's executable ask cannot be accepted below raw-spot intrinsic. Until a vendor or data-methodology source establishes the correct basis, the QQQ history must be treated as **price-integrity unresolved**, in addition to the March 2014 contract-row cutoff. Do not use adjusted close to legitimize the option quote, and do not use either value as a replay fallback.
- The independent data request should now explicitly ask the provider to confirm raw, as-traded bid/ask and strike conventions for `QQQ140920C00077000` on 2013-12-23 and 2014-03-11, including the matching unadjusted underlying close. The frozen baseline and all terminal-equity gates remain unchanged.


### 2026-10-14 06:48Z — Cohort-wide intrinsic-bound audit added

- PR [#47](https://github.com/eklu654/Trading-Bot/pull/47) merged as `871d326e6776aad55dc0bb1ec1bdc5f9cf6ba9b8` after focused tests [38524274255](https://github.com/eklu654/Trading-Bot/actions/runs/38524274255) and full research-tests [38524274195](https://github.com/eklu654/Trading-Bot/actions/runs/38524274195) passed.
- The diagnostic now counts bid/ask-below-intrinsic warnings across all options expiring in the same calendar year on the flagged quote dates, separately for each available underlying price field. It reports counts and samples but does not gate, alter, or impute any quote.
- New audit [run 38524356807](https://github.com/eklu654/Trading-Bot/actions/runs/38524356807) is queued. Its cohort counts will determine whether the QQQ price-basis warning is isolated or affects a broader slice of the preserved option dataset.


### 2026-10-14 06:49Z — Cohort intrinsic-bound results show broad QQQ price-integrity warnings

- Cohort audit [run 38524356807](https://github.com/eklu654/Trading-Bot/actions/runs/38524356807) passed; artifact [11875462386](https://github.com/eklu654/Trading-Bot/actions/runs/38524356807/artifacts/11875462386), SHA-256 `1f8d9659c47116352513969202ec088b5fbc38216cbe2e7de0a7ed6aaa492a31`.
- On 2014-03-11, the QQQ 2014-expiration cohort has 2,772 quote rows (all with positive asks; 2,482 with positive bids). Against raw `close`, **472 asks (17.0%) and 891 bids (35.9% of positive bids) are below intrinsic**. Against `adjusted_close`, the counts are 851 asks and 861 bids. The sample includes near-expiry calls: strike 74 ask $8.40 vs $16.22 raw intrinsic; strike 75 ask $7.90 vs $15.22; strike 76 ask $7.40 vs $14.22. Those quotes are roughly half their raw intrinsic values.
- Control: on 2008-08-11, the SPY 2008-expiration cohort has 1,054 quote rows (815 positive bids). Against raw `close`, there are zero asks below intrinsic and 108 positive bids below intrinsic. Against `adjusted_close`, there are 386 asks and 367 bids below intrinsic. This supports using raw `close` as the relevant candidate for unadjusted listed-option prices, but it does not establish the option source's premium basis.
- Conclusion: QQQ is not merely missing later contract rows; a material share of its 2014 quote rows are inconsistent with raw-spot intrinsic bounds. The preserved dataset cannot be treated as executable as-traded QQQ bid/ask history until the provider's premium adjustment methodology is established or an independent source disproves these records. The frozen replay remains unapproved.


### 2026-10-14 06:51Z — Added ratio-distribution diagnostics to test for systematic quote scaling

- PR [#48](https://github.com/eklu654/Trading-Bot/pull/48) merged as `98fb48a99f283674f7adb93f18bf2989f30629e9` after focused and broad tests [38524593368](https://github.com/eklu654/Trading-Bot/actions/runs/38524593368) and [38524593474](https://github.com/eklu654/Trading-Bot/actions/runs/38524593474) passed.
- The non-gating cohort audit now reports p10/p25/p50/p75/p90 ask-to-intrinsic ratios for in-the-money quotes, split by calls/puts and raw/adjusted underlying fields. This is intended to distinguish isolated stale quotes from systematic scale/basis issues.
- Updated audit [run 38524678107](https://github.com/eklu654/Trading-Bot/actions/runs/38524678107) is running; inspect its artifact before drawing any conclusion about a factor-of-two error.
