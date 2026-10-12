# Alpaca Paper Portfolio Readiness — 2026-10-12

## Verified
- Credential check run [38199438537](https://github.com/eklu654/Trading-Bot/actions/runs/38199438537) passed for both B0 and F75.
- Both paper accounts returned `ACTIVE`, USD currency, credentials present, and neither account nor trading was blocked.
- Credential verification made only a GET request to `/v2/account`; it submitted no orders.

## New read-only preflight
- Added `.github/workflows/alpaca-paper-portfolio-preflight.yml`.
- For each account, it checks account eligibility, current positions, open orders, and Alpaca's broker clock/session state.
- It reports only sanitized status/count metadata, not account numbers, credentials, balances, or raw API responses.
- It uses GET requests only and has no order-submission endpoint or write operation.
- Scheduled for weekdays at 22:15 UTC; also runs when this workflow file changes on `main`, and supports manual dispatch.

## Remaining before strategy orders
1. Run the preflight and verify current positions/open orders and session metadata.
2. Implement strategy-to-target-position mapping with a fixed $5,000 virtual allocation per portfolio; never size from the paper account's default total balance.
3. Add deterministic idempotent client order IDs, startup reconciliation, order/fill state tracking, stale-data fail-closed behavior, and explicit kill switch.
4. Validate order sizing and signal timing before enabling any paper order submission. The existing F75 prospective ledger remains `SHADOW_ONLY_NO_ORDERS`; it is not itself an order engine.

## Strategy status
- B0 remains the control; F75 remains frozen experimental overlay.
- Diagnostic B0/F75 equity tracking continues immediately and independently of the 252-return-bearing-session efficacy threshold.
- Do not fabricate observations or use historical signal values as a current-session signal.
