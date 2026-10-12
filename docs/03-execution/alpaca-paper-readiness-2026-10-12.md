# Alpaca Paper Portfolio Readiness — 2026-10-12

## Verified broker preflight
- Credential check [38199438537](https://github.com/eklu654/Trading-Bot/actions/runs/38199438537) passed for B0 and F75; both accounts were ACTIVE/USD and unblocked.
- Read-only preflight [38199816562](https://github.com/eklu654/Trading-Bot/actions/runs/38199816562) reported zero positions and zero open orders for both accounts.
- Daily signal-to-account diagnostic [38201802963](https://github.com/eklu654/Trading-Bot/actions/runs/38201802963) passed for both portfolios. Its tests passed (14 planner tests plus 5 signal-ledger tests per job); the latest signal session was 2026-10-09, B0/F75 close targets were both 100%, the shadow-equity reference was $4,973.08 per portfolio, and both paper accounts reported ACTIVE/USD, zero TQQQ positions, zero open positions, zero open orders, and zero recent orders. Alpaca's clock was closed, so both jobs safely skipped. No order was submitted.

## Added controls
- The pure paper order planner uses deterministic client IDs, the exact paper endpoint, fixed strategy target-weight constraints, and fail-closed checks. Fill-backed buy sizing leaves a 0.5% cash reserve to absorb ordinary market-order slippage without driving virtual cash negative. Planner validation: [38201530243](https://github.com/eklu654/Trading-Bot/actions/runs/38201530243).
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

- Added `.github/workflows/alpaca-paper-order-executor.yml`, scheduled for 13:40 UTC weekdays (9:40 a.m. US/Eastern). Only the scheduled event sets the order-submission enable flag; push and manual runs are dry-run/reconciliation only.
- Before any POST, the workflow persists a staged client-order-ID intent to `paper-execution-ledger`, then persists a `SUBMITTING` state and creates an ephemeral same-run permit. A later workflow run without that permit only queries the broker by client order ID; it never retries an ambiguous submission.
- All order writes are hard-pinned to `https://paper-api.alpaca.markets`. It requires the latest completed shadow signal, state mark date aligned to signal date, fresh IEX trade, ACTIVE/unblocked USD account, no unrelated positions/open orders, and broker quantity reconciled to fill-backed state.
- Order reports are sanitized and uploaded as artifacts. The executor never uses Alpaca paper NLV for strategy sizing; it uses fill-backed virtual equity.
- This workflow has not yet been validated by a scheduled market-open run. The next scheduled run may submit paper orders only if every gate passes; push/manual runs cannot submit. No live endpoint is used.


## 2026-10-12 executor hardening follow-up
- Added a 0.5% buy-side virtual-cash reserve, explicit reference-price storage, and a terminal-order rejection reconciliation path.
- Added a second open-order lookup immediately before POST so an order that appears after the first client-ID lookup is reconciled rather than duplicated.
- The current executor push-trigger is dry-run only. Scheduled runs alone can create the ephemeral submission permit and POST to the paper endpoint.

- Added an account-identity gate before order planning: B0 and F75 credentials must resolve to distinct paper account IDs, and a SHA-256 fingerprint (never the raw ID) is persisted in each virtual ledger. Every executor run and subsequent ledger sync checks that the credential still resolves to the same account.


## Latest closed-market executor validation — 2026-10-12
- Run [38203442398](https://github.com/eklu654/Trading-Bot/actions/runs/38203442398) passed the executor workflow and its tests: 17 virtual-ledger tests plus 14 executor tests.
- The workflow verified B0/F75 credentials resolve to distinct ACTIVE, unblocked USD paper accounts and persisted only hashed account fingerprints. It then correctly returned `SKIPPED_MARKET_CLOSED` for both portfolios, with no staged intent, no POST, and no order.
- Persistent states remain $5,000 cash, zero shares, $5,000 virtual equity, mark date 2026-10-09, no pending intent.
- The next scheduled opportunity is 2026-10-12 at 13:40 UTC. It can submit only to Alpaca's paper endpoint, and only if the latest completed signal/session, account identity, broker position, open-order, and fresh-trade gates all pass. Scheduled market-open submission has not yet been observed.

## QQQ intraday monitoring — read-only interim control (2026-10-12)
- Added `.github/workflows/qqq-intraday-monitor.yml`, scheduled to poll every five minutes during 13:00–20:59 UTC weekdays. Alpaca's market clock gates actual quote checks; GitHub Actions scheduling is best-effort and can be delayed.
- The monitor compares the latest QQQ IEX trade with the most recent completed daily close and reports when the move is at or below -4.5%. It rejects stale trades and fails closed when a completed prior close cannot be identified.
- This is **monitoring only**: it never creates orders, changes B0/F75 targets, or triggers the paper executor. Results are retained as 30-day Actions artifacts.
- This is not a continuous stream and cannot guarantee capture of every brief intraday breach. A persistent Alpaca market-data stream/service with reconnect handling is the next step for lower-latency detection. Any trading reaction must separately specify whether the -4.5% rule is an intraday trigger or a completed-daily-close signal.

## QQQ intraday threshold monitor — implementation checkpoint
- Added `research/qqq_intraday_monitor.py`, 8 unit tests, and `.github/workflows/qqq-intraday-monitor.yml`.
- It polls every five minutes during 13:00–20:59 UTC weekdays, checks Alpaca's market clock, reads the latest QQQ IEX trade, and compares it to the most recent completed daily close. A breach is reported at or below -4.5%. It is read-only and cannot submit orders.
- First CI run [38204835453](https://github.com/eklu654/Trading-Bot/actions/runs/38204835453) caught a daily-bar timezone/session-date bug in tests; fixed by using the daily bar's own session date rather than converting midnight UTC to the prior New York date.
- Corrected validation is running as [38204861873](https://github.com/eklu654/Trading-Bot/actions/runs/38204861873). Do not call this monitor validated until this run completes successfully.
- Important limitation: GitHub Actions cron is best-effort, not a live stream. A short-lived breach can occur and reverse between polls, and scheduled runs can be delayed. This is an interim warning/measurement layer, not an automated defensive order trigger. A persistent stream consumer is needed for low-latency continuous monitoring.

## Monitor validation result
- Corrected run [38204861873](https://github.com/eklu654/Trading-Bot/actions/runs/38204861873) succeeded: all 8 monitor unit tests passed. Its live workflow invocation returned `MARKET_CLOSED`, so it did not yet exercise a live intraday trade/bar response. The next open-market polling run is the first opportunity to validate the real Alpaca data response path.
