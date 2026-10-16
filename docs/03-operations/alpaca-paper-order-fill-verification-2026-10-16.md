# Alpaca Paper Account Order and Fill Verification — 2026-10-16

## Scope

Read-only verification after the ChatGPT Alpaca Paper Trading connection was authorized. No order was placed, replaced, or canceled during this audit. Live-account authorization was not used.

## Account identity

The connected Alpaca Paper Trading app exposes two distinct account links, labeled B0 and F75. GitHub's executor identity fingerprints also remain distinct:

- B0: `50f604720af647b59e9afb107c66b68d00e076500b983dd7c89d194cda31d710`
- F75: `3e98eec4d11f1f4c92f39527241893ec5e83c0387bf78ad51d6b6e3578d37d91`

These are non-secret fingerprints, not API credentials.

## Broker order and fill evidence

Read-only Alpaca queries returned one recent TQQQ market buy for each account. Both orders are terminal `filled`, with filled quantity matching order quantity and multiple fill activity records that cumulatively reconcile to the order.

| Field | B0 | F75 |
|---|---|---|
| Broker order ID | `89c20a9a-cb6e-44d4-9947-d093ea60d49a` | `8aa513ac-26b4-428c-8abe-0004fef29db1` |
| Client order ID | `tb-2fae5a6bfc0d842f4961791cc3c95abb` | `tb-e9eab95d982d902a2f17e2d7a2f08fc7` |
| Submitted | 2026-10-13 13:31:52 UTC | 2026-10-13 13:31:54 UTC |
| Filled | 2026-10-13 13:33:43 UTC | 2026-10-13 13:33:30 UTC |
| Quantity | 64.170 TQQQ | 64.228 TQQQ |
| Filled average price | $77.697533 | $77.532562 |
| Final status | `filled` | `filled` |
| Open orders at reconciliation | 0 | 0 |

The fills activity records sum to 64.170 shares for B0 and 64.228 shares for F75. GitHub's isolated `paper-execution-ledger` branch stores the same broker/client order IDs, quantities, symbol, signal session `2026-10-12`, and processed fill activity IDs.

## Workflow evidence

- [Order executor run 38822643862](https://github.com/eklu654/Trading-Bot/actions/runs/38822643862) completed successfully on 2026-10-15. This specific run reported `NO_PENDING_INTENT` for both accounts and explicitly stated no POST was attempted. It did not itself submit the orders described above.
- [Read-only reconciliation run 38831245015](https://github.com/eklu654/Trading-Bot/actions/runs/38831245015) completed successfully on 2026-10-16. Both portfolios reported `SYNCED`, account status `ACTIVE`, one open position, zero open orders, and `READ_ONLY_RECONCILIATION_NO_ORDERS`. Its state commit was `82d555d` on branch `paper-execution-ledger`.
- State files: `data/paper_execution/b0_state.json` and `data/paper_execution/f75_state.json` on branch `paper-execution-ledger`.

## Current status and limitations

**Verified:** ChatGPT Alpaca Paper Trading read access works; both account links are distinct; each account has a filled TQQQ order with fill activity; the executor's existing ledger records matching broker/client IDs and fill activity identifiers; the scheduled GET-only reconciliation reports both accounts synced.

**Not yet proven:** that the newest executor code can submit a new order in a controlled test, that a retry/re-run safely reconciles the same client order ID without duplication under ambiguous network failure, or that the emergency-exit path can place and reconcile a sell order. Do not infer those capabilities solely from a successful historical buy or a green workflow run.

No live orders were used. No strategy rules, API secrets, GitHub secrets, or paper positions were changed by this audit.
