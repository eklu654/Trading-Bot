# Fill-Backed Paper Virtual Portfolio Ledger — Design and Test Log

## Scope

This is a pure state machine for the next paper-trading stage. It does not call Alpaca, write files, or submit orders. It is designed to be persisted durably before any future broker mutation.

## Invariants encoded

- Each B0/F75 virtual portfolio initializes at $5,000 cash and zero TQQQ shares.
- Cash and holdings update from unique Alpaca fill-activity IDs, so replaying a fill is idempotent and partial fills can be applied incrementally.
- Only long TQQQ exposure is permitted; short-producing sells, invalid prices/quantities, unexpected symbols, and negative virtual cash fail closed.
- Equity is cash plus shares times the latest mark. Marks are monotonic by session; same-session rewrites are rejected.
- Targets use evolving fill-backed virtual equity, not a fixed $5,000 notional and not Alpaca's default account NLV.
- F75 requires B0 eligibility and cannot exceed B0 exposure.
- Before a future order POST, the intent must be staged and its deterministic client ID persisted. Any unknown outcome leaves the intent unresolved and blocks new orders; absence from a single reconciliation query is not permission to retry.
- Terminal order completion requires broker quantity to reconcile with the fill ledger. Used client IDs are never reused.

## Current boundary

This module is not connected to broker endpoints or a durable state branch yet. Passing tests will validate local state transitions only. It is not order-execution authorization.


## Validation result

- Workflow [38201992005](https://github.com/eklu654/Trading-Bot/actions/runs/38201992005) completed successfully.
- Python compilation passed and all 17 state-machine tests passed, covering initial capital, idempotent fills, incremental partial fills, long-only enforcement, mark monotonicity, compounded sizing, F75/B0 eligibility, staged-intent lockout, unknown outcomes, client-ID reconciliation, terminal position reconciliation, and replay prevention.
- This is a local state-machine test only. It does not prove persistence, live broker fill retrieval, or order submission.


## Submission-state refinement — 2026-10-12

- Added explicit `SUBMITTING` arming before a future POST, plus a safe abort transition for cases where preflight fails before POST begins.
- Added same-signal-session replay prevention and strict paper-only staged-intent validation.
- Latest run [38202697317](https://github.com/eklu654/Trading-Bot/actions/runs/38202697317) passed all 16 tests.


## Executor integration checkpoint

- The paper order executor is now present on main, with 5 payload tests. Push/manual events are dry-run only; only scheduled events receive the submission-enable flag.
- Latest closed-market validation: [38203111900](https://github.com/eklu654/Trading-Bot/actions/runs/38203111900) passed 17 virtual-ledger tests and 5 order-payload tests. It correctly staged no intent while the market was closed.
- The persistent broker ledger workflow [38203111870](https://github.com/eklu654/Trading-Bot/actions/runs/38203111870) passed and made no state changes because no fills or new completed session mark were available.
- Scheduled market-open order submission is still unverified; no paper order has been submitted.
