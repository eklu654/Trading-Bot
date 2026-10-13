# Market-Open Readiness Gate — 2026-10-13

## Verdict

**NOT READY for unattended order execution. Paper-only diagnostic preflight is verified; successful order submission and fill reconciliation are not. Do not promote to unattended operation or live trading.**

This is an operational safety gate, not a strategy-performance claim. It preserves the distinction between proving credentials work and proving the complete order lifecycle works.

## Latest evidence carried forward

- Diagnostic executor run `38383606683`: tests/account verification passed, but the market was closed and both portfolios skipped. It proves no order placement.
- Earlier scheduled run `38316969245`: `NO_ARM_REQUEST`, `NO_PENDING_INTENT`.
- B0 and F75 paper credentials were verified as distinct active Alpaca paper accounts; preflight showed no account/trading block and no positions/open orders at the time checked.
- Emergency monitor is currently read-only: it can detect a QQQ -4.5% trigger, but no broker exit submission is verified.
- Contract: [B0/F75 Paper Execution Contract](../research/B0_F75_PAPER_EXECUTION_CONTRACT_2026-10-12.md).

## Blocking gates (must all pass)

1. **Broker order lifecycle:** in Alpaca paper only, submit a deliberately small/controlled test order through the same production executor path; capture broker order ID and prove terminal status plus fills/position reconciliation. Do not infer success from HTTP acceptance alone.
2. **Emergency exit:** monitor trigger must create a durable idempotent exit intent, submit/cancel/replace as appropriate, and reconcile broker order state and actual fills. Verify it cannot create duplicate sells or reverse into a short position.
3. **Fresh signal and timing:** only use a completed-session signal and current eligible prices; reject stale or missing inputs. Close-derived signals execute no earlier than the next eligible session.
4. **Account/sleeve enforcement:** enforce paper endpoint, correct B0/F75 credentials, active/unblocked status, and the $5,000 virtual sleeve. Never size from Alpaca's displayed default NLV.
5. **Durability and restart:** persist signal date/hash, target, current broker state, intent, client order ID, broker order ID, fills, and reconciliation result. Restart must reconcile before planning or retrying.
6. **Failure injection:** demonstrate safe handling of API timeout/ambiguous response, rejected order, partial fill, stale data, unexpected position, existing open order, concurrent scheduler/monitor, and process restart.
7. **Recovery behavior:** test the QQQ -4.5% shock trigger and +10% recovery rule through restart and repeated events. Re-entry must not erase a pending exit or bypass reconciliation.
8. **Market-hours acceptance:** observe at least one eligible market-hours cycle in paper mode, including order lifecycle and subsequent account/position reconciliation. Preserve run URLs and sanitized artifacts.

## Acceptance criteria

- No duplicate order after retry, timeout, restart, or concurrent invocation.
- Every broker position and open order is explained by the durable ledger; discrepancies fail closed.
- Exit trigger → durable intent → broker order → fill/reconciliation → state update is evidenced end-to-end.
- Both B0 and F75 are tested independently, with F75 remaining subordinate to B0 eligibility.
- Any failed or unverified gate leaves the executor in no-new-orders mode and alerts visibly.
- Evidence includes workflow run IDs, sanitized logs/artifacts, and test outcomes; never record credentials or tokens.

## Source/log inspection — 2026-10-13

Inspected `research/alpaca_paper_order_executor.py`, its unit tests, virtual ledger, and run `38383606683` job log. The executor already has a paper-only POST path, durable staged/SUBMITTING states, deterministic client order IDs, account identity checks, broker reconciliation, and an unknown-outcome no-retry path. The workflow run passed 17 virtual-ledger tests and 14 executor tests. This is meaningful implementation progress, but the tested order submission was not exercised against the broker.

The same run's environment explicitly set `ENABLE_PAPER_ORDER_SUBMISSION=false`. The prepare step reported `SKIPPED_MARKET_CLOSED` for both portfolios; the arm/submit path then reported `NO_ARM_REQUEST` / `NO_PENDING_INTENT`, with **no POST attempted**. Therefore the run cannot establish broker acceptance, fills, or position reconciliation. Existing unit tests mock the POST and broker responses; they do not replace an end-to-end paper order lifecycle.

## Audit update

2026-10-13: Confirmed the order-submit implementation exists but is deliberately disabled in the current workflow environment. Emergency exit remains read-only. The immediate implementation gap is not simply “add a POST”: it is to validate the guarded schedule-only enablement, complete a market-hours paper order lifecycle safely, and implement a durable emergency-exit intent/submit/reconcile path with restart and fault tests. **No claim of readiness is made.**


## Follow-up source review — 2026-10-13

A read-only source review was committed at [paper-executor-review-2026-10-13.md](paper-executor-review-2026-10-13.md), commit `4d630ff1a212f0cfe7077c4392384f25de68bc4d`. It confirms paper-only endpoint pinning, durable staged/SUBMITTING state, client-order-ID lookup before retry, stale-price checks, and fill-backed ledger guards. It also confirms the executor CLI has no dedicated emergency-exit mode; workflow YAML/monitor integration, cross-process concurrency, complete fill reconciliation, and real market-hours broker lifecycle remain unverified. No broker order was sent in this review.
