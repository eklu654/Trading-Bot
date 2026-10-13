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
