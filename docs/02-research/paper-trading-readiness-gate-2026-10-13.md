# Paper-trading readiness gate — 2026-10-13

## Decision
**NOT READY to claim autonomous order execution or emergency exits are operational.** Do not report a successful trade unless the broker order ID and subsequent broker reconciliation/fill are evidenced in the executor audit artifact and durable portfolio state.

## Verified repository state at review time
- Main executor workflow is scheduled every five minutes at `*/5 13-20 * * 1-5` UTC: `.github/workflows/alpaca-paper-order-executor.yml`.
- The executor has a paper-only POST implementation, but code presence is not evidence that a POST succeeded.
- `.github/workflows/qqq-intraday-monitor.yml` calls `research/qqq_intraday_monitor.py`, whose module/docstring and report explicitly state it is read-only and never submits orders.
- Both paper states on `paper-execution-ledger` report initial equity/cash $5,000, quantity 0, no pending intent, and `last_fill_sync_at: null`. Their mark date is 2026-10-12.
- The shadow manifest on `research/qqq-slow-bear-audit` reports last observation 2026-10-09, frozen cutoff 2026-10-07, and only two ledger rows. The ledger's latest signal row is 2026-10-09, with B0 and F75 target weights both 1.
- The executor's `prepare` path refuses to plan a new order if the portfolio state's `mark_date` does not equal the latest signal session. Here, state mark date (2026-10-12) and ledger signal session (2026-10-09) differ. This is a concrete blocker to the next scheduled order attempt, unless the upstream ledger/state is reconciled first.

## Required before declaring ready
1. Refresh/rebuild the shadow ledger and manifest from validated market data through the last completed session; verify the manifest hash, row count, and source hash.
2. Reconcile B0/F75 state marks to that exact signal session and fetch current broker positions, open/recent orders, and fills. Do not overwrite fill-backed quantities with shadow exposures.
3. Convert the QQQ -4.5% monitor from read-only reporting to a tested, durable, paper-only exit-intent path. Define the recovery anchor explicitly before implementing the +10% recovery/re-entry rule.
4. Add tests for threshold breach, stale data, duplicate exit prevention, partial fills, order rejection, unknown POST outcome, recovery/re-entry, and both account identities.
5. Verify a scheduled run against both paper accounts and inspect `alpaca-paper-order-executor-audit`. Require an accepted broker order ID and reconciled fill (or a clearly reported no-order reason); a green workflow alone is insufficient.

## Safety / scope
Paper API endpoint only. Never log raw credentials or account IDs. Do not automatically retry an ambiguous POST. Keep an emergency-exit path independent of the daily target-signal cadence. This note records a readiness gap, not a claim that a fix or trade has occurred.
