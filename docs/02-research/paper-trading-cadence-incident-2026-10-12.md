# Paper-trading cadence incident and correction — 2026-10-12

## User-visible symptom
B0 and F75 appeared static at $5,000 cash/equity with zero TQQQ shares. The durable ledger on branch `paper-execution-ledger` also had `last_fill_sync_at: null` and a mark date of `2026-10-09`.

## Verified cause
- The paper order executor was configured for only two scheduled attempts per weekday (`13:40` and `14:40` UTC), not every five minutes.
- The separate five-minute workflow, `.github/workflows/qqq-intraday-monitor.yml`, was explicitly **read-only**. Its run #38204861873 passed tests but reported `MARKET_CLOSED` at 2026-10-12 04:42:21 UTC and `orders_submitted: false`; it was not a trading executor.
- Executor run #38203442398 completed its safety checks but its prepare reports said `SKIPPED_MARKET_CLOSED`, signal session `2026-10-09`, then `NO_ARM_REQUEST` and `NO_PENDING_INTENT`. Its environment showed `ENABLE_PAPER_ORDER_SUBMISSION: false`, so this was a non-scheduled dry-run and did not attempt a broker order. It must not be interpreted as evidence that a scheduled market-hours attempt occurred.
- The available run records do not prove whether either old scheduled slot executed on Oct 12. We therefore cannot attribute the lack of movement solely to a market-data issue or assert that today's scheduled run failed; the verified configuration mismatch is enough to explain why the expected five-minute decision cadence was absent.

## Fix committed
- Changed `.github/workflows/alpaca-paper-order-executor.yml` to schedule every five minutes from 13:00 through 20:55 UTC on weekdays (`*/5 13-20 * * 1-5`).
- The existing broker clock, latest-trade freshness check, fill-backed position reconciliation, durable client-order IDs, and one-run submission permit remain in force. Closed-market and stale-data checks continue to fail closed.
- The strategy signal still comes from the latest completed daily shadow-ledger row. Five-minute runs repeatedly evaluate whether the portfolio needs to move to that target; they do not create new intraday strategy signals. The QQQ -4.5% workflow remains a read-only monitor and does not independently submit trades.
- Push/manual runs remain dry-run only; only scheduled runs can submit to the Alpaca paper endpoint. No order was manually forced.

## Validation / follow-up
- Workflow edit commit: `e8a76499b04da5538eb40852380c074622cb1f50`.
- Next verification must inspect a post-fix **schedule-triggered** run and its sanitized `alpaca-paper-order-executor-audit` artifact. Confirm fresh account/position/order reconciliation, the prepare status for each portfolio, and any actual broker order/fill. A green workflow alone is insufficient.
- If prepare reports remain blocked because `mark_date` or signal session is stale, repair the daily shadow-ledger/mark refresh path rather than bypassing the guard.
