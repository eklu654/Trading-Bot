# B0/F75 Paper Execution Guardrails — 2026-10-12

## Purpose and boundary

Added a pure Python order-intent planner and regression tests to establish fixed-sleeve sizing and fail-closed invariants before any broker mutation is wired in. The planner makes no network calls and submits no orders.

## Frozen rules encoded

- B0: TQQQ long/flat, target weight 0% or 100%.
- F75: TQQQ long/flat, target weight 0%, 75%, or 100%, with B0 eligibility enforced by the caller using the frozen overlay.
- Each portfolio starts with its own $5,000 virtual allocation. Target notional must scale with the portfolio's evolving virtual equity, never a permanently fixed $5,000 notional and never Alpaca paper NLV. The current daily diagnostic uses shadow-ledger equity as a reference only; an order-writing executor must use its own fill-backed virtual-equity ledger.
- Only the exact https://paper-api.alpaca.markets endpoint is accepted.
- Account must be ACTIVE, unblocked, USD; market must be open; latest bar date must match the supplied completed-session date; no unresolved open orders.
- Short positions, non-positive/non-finite prices, invalid target weights, and stale/mismatched session data fail closed.
- Quantity is rounded down to 0.001 shares; sub-precision deltas fail closed. Intent IDs are deterministic for portfolio, symbol, session, target weight, and target quantity.
- Output mode is always PLAN_ONLY_NO_SUBMISSION.

## Not yet implemented / not claimed

This planner does not fetch market data, calculate the live baseline/F75 signal, query/reconcile broker positions or fills, persist a real order ledger, submit orders, or handle ambiguous broker outcomes. A caller must not treat a plan as permission to submit. Those integrations and fault-injection tests remain required before any automated order submission.

## Validation

- Initial workflow run [38201405724](https://github.com/eklu654/Trading-Bot/actions/runs/38201405724) passed the first 12 planner regression tests.
- Added a 13th test and a fail-closed guard for a rebalance delta below 0.001 shares, preventing a zero-quantity order intent.
- Latest planner-only run [38201530243](https://github.com/eklu654/Trading-Bot/actions/runs/38201530243) passed all 13 tests after the precision guard.
- Daily diagnostic run [38201802963](https://github.com/eklu654/Trading-Bot/actions/runs/38201802963) passed Python compilation, all 14 planner tests, and all 5 ledger/diagnostic tests for both portfolios. The sanitized outputs confirmed the signal/session, evolving shadow-equity reference, ACTIVE/USD status, zero positions/orders, and safe closed-market no-op.
- This validates read-only diagnostics and planning, not broker order submission, fill-backed equity accounting, or order-outcome recovery.
