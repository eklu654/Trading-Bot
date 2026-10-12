# Alpaca Paper Portfolio Readiness — 2026-10-12

## Verified broker preflight
- Credential check [38199438537](https://github.com/eklu654/Trading-Bot/actions/runs/38199438537) passed for B0 and F75; both accounts were ACTIVE/USD and unblocked.
- Read-only preflight [38199816562](https://github.com/eklu654/Trading-Bot/actions/runs/38199816562) reported zero positions and zero open orders for both accounts.
- Daily signal-to-account diagnostic [38201802963](https://github.com/eklu654/Trading-Bot/actions/runs/38201802963) passed for both portfolios. Its tests passed (14 planner tests plus 5 signal-ledger tests per job); the latest signal session was 2026-10-09, B0/F75 close targets were both 100%, the shadow-equity reference was $4,973.08 per portfolio, and both paper accounts reported ACTIVE/USD, zero TQQQ positions, zero open positions, zero open orders, and zero recent orders. Alpaca's clock was closed, so both jobs safely skipped. No order was submitted.

## Added controls
- The pure paper order planner uses deterministic client IDs, the exact paper endpoint, fixed strategy target-weight constraints, and fail-closed checks. Planner validation: [38201530243](https://github.com/eklu654/Trading-Bot/actions/runs/38201530243).
- The read-only daily diagnostic is in `.github/workflows/alpaca-paper-daily-decision.yml`, scheduled for 14:40 UTC weekdays. It verifies the shadow ledger hash/date/signal, account eligibility, broker positions/open orders/recent orders, broker clock, and fresh TQQQ trade data when the market is open.
- A fill-backed virtual ledger state machine starts each portfolio at $5,000 cash and zero shares, applies unique fill activities idempotently, supports incremental partial fills, marks equity from cash plus shares, and blocks new intents while an order outcome is unknown. Its 14 tests passed in [38201992005](https://github.com/eklu654/Trading-Bot/actions/runs/38201992005).
- Separate state branch `paper-execution-ledger` is initialized with B0/F75 virtual states. The new `.github/workflows/alpaca-paper-virtual-ledger.yml` will reconcile fill activities and positions and mark the virtual portfolio using Alpaca's raw daily bar, then commit state to that branch only if both portfolio checks pass. It is GET-only and never submits, replaces, or cancels orders.

## Current boundary / remaining before paper orders
- The virtual-ledger state machine and read-only diagnostic are validated locally; the new persistent broker reconciliation workflow still needs its first successful run. If the market-data or fill-activity endpoints are unavailable, it fails closed and does not update state.
- The daily diagnostic's shadow-equity reference is for comparison only. Future order sizing must use the persistent fill-backed virtual-equity ledger, not Alpaca's default paper NLV or the shadow simulation alone.
- Before any order-writing workflow is enabled: verify persisted ledger reconciliation, integrate the signal target with fill-backed equity, persist an order intent before POST, use client-order-ID reconciliation after timeouts, reconcile fill activities and broker position, and test rejection/partial-fill/restart/unknown-outcome paths.
- B0 is the control; F75 is the frozen 75%/100% experimental overlay. The 252-return-bearing-session threshold is an efficacy-review gate, not a prerequisite for diagnostic tracking.
- No live trading is authorized. No order has been submitted by these workflows.

## Two-phase paper executor — 2026-10-12

- Added `.github/workflows/alpaca-paper-order-executor.yml`, scheduled for 14:40 UTC weekdays. Only the scheduled event sets the order-submission enable flag; push and manual runs are dry-run/reconciliation only.
- Before any POST, the workflow persists a staged client-order-ID intent to `paper-execution-ledger`, then persists a `SUBMITTING` state and creates an ephemeral same-run permit. A later workflow run without that permit only queries the broker by client order ID; it never retries an ambiguous submission.
- All order writes are hard-pinned to `https://paper-api.alpaca.markets`. It requires the latest completed shadow signal, state mark date aligned to signal date, fresh IEX trade, ACTIVE/unblocked USD account, no unrelated positions/open orders, and broker quantity reconciled to fill-backed state.
- Order reports are sanitized and uploaded as artifacts. The executor never uses Alpaca paper NLV for strategy sizing; it uses fill-backed virtual equity.
- This workflow has not yet been validated by a scheduled market-open run. The next scheduled run may submit paper orders only if every gate passes; push/manual runs cannot submit. No live endpoint is used.
