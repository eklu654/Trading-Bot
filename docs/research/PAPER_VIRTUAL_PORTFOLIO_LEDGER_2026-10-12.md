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
- Python compilation passed and all 14 state-machine tests passed, covering initial capital, idempotent fills, incremental partial fills, long-only enforcement, mark monotonicity, compounded sizing, F75/B0 eligibility, staged-intent lockout, unknown outcomes, client-ID reconciliation, terminal position reconciliation, and replay prevention.
- This is a local state-machine test only. It does not prove persistence, live broker fill retrieval, or order submission.


## Integration update — 2026-10-12 06:20 UTC

The original “Current boundary” section above describes the state-machine-only checkpoint and is superseded for repository integration status by the following verified facts:

- Main now contains `.github/workflows/alpaca-paper-order-executor.yml` and `.github/workflows/alpaca-paper-virtual-ledger.yml`. The executor is scheduled for 13:40 UTC weekdays and enables POST only for a scheduled event; the reconciliation workflow uses GET only.
- Executor run [38203442398](https://github.com/eklu654/Trading-Bot/actions/runs/38203442398) completed successfully but returned `SKIPPED_MARKET_CLOSED` for both portfolios and `NO_PENDING_INTENT`; it did not submit an order.
- Read-only reconciliation run [38203111870](https://github.com/eklu654/Trading-Bot/actions/runs/38203111870) completed successfully.
- Current durable states on this branch remain B0/F75 at $5,000.00 cash/equity, zero TQQQ shares, no pending intent, no processed fills, and mark date 2026-10-09. No broker fill has yet been reconciled.
- Code review checked a suspected false-positive in the reconciliation guard. `stage_intent()` adds the staged client order ID to `used_client_order_ids` before the state is persisted, so the known pending order is not rejected by the later bot-order ID guard. No code change was made for that suspicion.
- Main's paper-readiness record and current session audit: [readiness](https://github.com/eklu654/Trading-Bot/blob/main/docs/03-execution/alpaca-paper-readiness-2026-10-12.md) · [session audit](https://github.com/eklu654/Trading-Bot/blob/main/docs/03-execution/session-audit-2026-10-12-0611z.md).

Next evidence needed is the first scheduled open-market executor result, followed by fill-backed reconciliation and verification that both persisted ledger states reflect broker order/fill status and the completed-session mark. No live trading is authorized.


## Schedule correction — 2026-10-12 06:20 UTC

Correction to the integration summary immediately above: the executor cron was changed after the first inspection. Current main schedule is `40 14 * * 1-5` (14:40 UTC), which corresponds to 10:40 a.m. Eastern during daylight time and 09:40 a.m. Eastern during standard time. The post-change push run [38211932599](https://github.com/eklu654/Trading-Bot/actions/runs/38211932599) passed all executor steps on commit `26302e02af2051814b974c17078b8eb546dccde0`; because it was a push event, it was dry-run/reconciliation only and submitted no order. The 12 Actions runs associated with that commit, including the executor and full research-tests job, all completed successfully.
