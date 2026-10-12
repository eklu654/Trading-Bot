# Paper-trading launch readiness audit — 2026-10-12 07:00 UTC

## Objective
Prepare B0 (control) and F75 (frozen 75%/100% overlay) for a first **paper-only** scheduled run on Monday, 2026-10-12. No live-trading permissions or endpoint are authorized.

## Schedule change made
- Updated `.github/workflows/alpaca-paper-order-executor.yml` to weekday cron slots at 13:40 and 14:40 UTC.
- Updated `.github/workflows/alpaca-paper-daily-decision.yml` to the same slots for read-only diagnostics.
- Houston is on Central Daylight Time (UTC-5) on this date: 13:40 UTC = 08:40 CT, ten minutes after the 08:30 CT regular-session open; 14:40 UTC = 09:40 CT.
- During standard time, 13:40 UTC is 07:40 CT and should be safely skipped by Alpaca's market-clock check; 14:40 UTC = 08:40 CT. During daylight time, the later slot is a redundant retry.
- Redundant schedule safety depends on durable intent, client-order-ID reconciliation, open-order checks, and broker-position vs virtual-ledger checks. If these checks disagree, execution must fail closed.
- Only `schedule` events set `ENABLE_PAPER_ORDER_SUBMISSION=true`. Push and manual events are not intended to submit new orders.

## Verified before market open
- The prior workflow definition had only 14:40 UTC, which meant 09:40 CT in daylight time—not near the 08:30 CT open. This has been corrected.
- Prior commit `26302e02af2051814b974c17078b8eb546dccde0` passed push-triggered executor run [38211932599](https://github.com/eklu654/Trading-Bot/actions/runs/38211932599); that was a dry-run path and **not** proof of order submission.
- Latest schedule edits are in commits `b39909730ee05f42f5ed15a79901bdc36e4f2a3c` (executor) and `1335c25e691fe05a4c7cbdf94cf61919c09240e1` (diagnostic). Executor push run [38215198510](https://github.com/eklu654/Trading-Bot/actions/runs/38215198510) passed; both B0/F75 actual prepare paths reported `SKIPPED_MARKET_CLOSED` because this was a premarket push event, and no order was submitted. Read-only diagnostic push run [38215205070](https://github.com/eklu654/Trading-Bot/actions/runs/38215205070) passed for both portfolios and likewise safely skipped because market was closed.
- Last persisted ledger snapshot had B0 and F75 each at $5,000 virtual cash/equity, zero shares, no pending intents, zero processed fills, and mark date 2026-10-09. Distinct broker-account fingerprints were present.
- The GET-only persistent ledger reconciliation workflow has now completed its first successful run: [38215313892](https://github.com/eklu654/Trading-Bot/actions/runs/38215313892). Both B0 and F75 returned `NO_CHANGE`, zero new fills, $5,000.00 virtual equity, and mark date 2026-10-09. This validates account/position/fill/bar reads and the workflow commit path for the empty baseline; it does **not** yet validate reconciliation of a real submitted order/fill.

## Market-open verification checklist
1. Confirm push-triggered dry-run and read-only diagnostic workflows pass after the schedule edit.
2. At 08:40 CT, inspect the scheduled executor run; confirm it reports each portfolio's status and any skip/block reason.
3. If orders are staged/submitted, verify broker order IDs/statuses and actual fill activities. A workflow success alone is not proof of a fill.
4. Confirm the 22:45 UTC (17:45 CT) read-only reconciliation runs after the market closes, applies unique fills idempotently, reconciles broker position quantities, and persists both ledgers.
5. If any check is blocked, order status is ambiguous, market data is stale, or ledger and broker state differ, leave the affected portfolio blocked; do not manually retry POSTs or bypass guards.

## Important limitations
- GitHub Actions cron timing is best-effort, not a guaranteed exact-time scheduler.
- We cannot truthfully claim full readiness until the first scheduled run and subsequent fill-backed reconciliation have succeeded.
- This is paper trading only. No live endpoint is used.

## Links
- [Executor workflow](https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/alpaca-paper-order-executor.yml)
- [Read-only diagnostic workflow](https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/alpaca-paper-daily-decision.yml)
- [Virtual ledger reconciliation workflow](https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/alpaca-paper-virtual-ledger.yml)
- [Readiness log](https://github.com/eklu654/Trading-Bot/blob/main/docs/03-execution/alpaca-paper-readiness-2026-10-12.md)

## Final pre-open code-path review — 2026-10-12 07:01 UTC
- Reviewed the executor's prepare/arm/submit state machine and unit tests before the first scheduled attempt.
- Duplicate/retry protections are implemented: concurrency group serializes executor runs; durable intent is committed before broker mutation; `SUBMITTING` is persisted before POST; subsequent runs first query Alpaca by exact client order ID and reconcile an existing order without POST; missing order lookup results in no retry without the same-run ephemeral permit; unknown POST outcomes remain blocked for reconciliation.
- Existing test suite includes checks that submission without a permit does not POST, a permitted submission posts once and persists the broker order ID, and unknown POST outcomes are recorded without retry. The last verified executor run passed 17 guardrail tests.
- Fail-closed checks include active/unblocked distinct USD paper accounts, fresh prior-session signal with manifest/hash consistency, market-open clock, only expected TQQQ long position, position-to-ledger agreement, no unrelated open orders, no untracked bot-tagged recent orders, latest trade no older than 180 seconds, and maximum 0.25% reference-price drift before submission.
- No additional pre-open code change is justified based on this review. Remaining unknown is operational, not a missing preflight step: first real scheduled paper submission/fill and subsequent fill-backed ledger reconciliation have not yet been observed. The 09:40 CT redundant slot must be checked for correct reconciliation/no duplicate POST after the 08:40 CT slot.
