# B0/F75 Paper Execution Guardrails — 2026-10-12

## Purpose and boundary

Added a pure Python order-intent planner and regression tests to establish fixed-sleeve sizing and fail-closed invariants before any broker mutation is wired in. The planner makes no network calls and submits no orders.

## Frozen rules encoded

- B0: TQQQ long/flat, target weight 0% or 100%.
- F75: TQQQ long/flat, target weight 0%, 75%, or 100%, with B0 eligibility enforced by the caller using the frozen overlay.
- Each portfolio uses its own $5,000 virtual allocation, not Alpaca paper NLV.
- Only the exact https://paper-api.alpaca.markets endpoint is accepted.
- Account must be ACTIVE, unblocked, USD; market must be open; latest bar date must match the supplied completed-session date; no unresolved open orders.
- Short positions, non-positive/non-finite prices, invalid target weights, and stale/mismatched session data fail closed.
- Quantity is rounded down to 0.001 shares; intent IDs are deterministic for portfolio, symbol, session, target weight, and target quantity.
- Output mode is always PLAN_ONLY_NO_SUBMISSION.

## Not yet implemented / not claimed

This planner does not fetch market data, calculate the live baseline/F75 signal, query/reconcile broker positions or fills, persist a real order ledger, submit orders, or handle ambiguous broker outcomes. A caller must not treat a plan as permission to submit. Those integrations and fault-injection tests remain required before any automated order submission.

## Validation

The workflow run linked from the commit history is the authority for test results. Record its actual conclusion and test count here after Actions finishes.
