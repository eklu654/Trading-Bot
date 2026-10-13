# Paper-trading readiness gate — 2026-10-13

## Decision
**NOT READY to claim autonomous execution or emergency exits are operational.** Do not report a successful trade unless a broker order ID and reconciled broker status/fill are evidenced in the executor audit and durable state.

## Verified as of 2026-10-13 10:29 UTC
- Main executor workflow is scheduled every five minutes at `*/5 13-20 * * 1-5` UTC. Alpaca's broker clock gates order preparation/submission outside the actual session.
- The executor code is paper-endpoint-only and contains two-phase intent persistence, client-order-ID reconciliation, and no automatic retry for ambiguous POST outcomes.
- The scheduled workflow has **not yet produced verified live-session order evidence**. Run [38383606683](https://github.com/eklu654/Trading-Bot/actions/runs/38383606683) was a push-triggered dry run: tests passed, both distinct paper account identities were verified, but the broker clock reported `SKIPPED_MARKET_CLOSED` for both portfolios. No order was submitted.
- The earlier push-triggered run [38383403303](https://github.com/eklu654/Trading-Bot/actions/runs/38383403303) failed preflight because the signal ledger was stale relative to portfolio marks.
- The F75 shadow scheduler run [38383529041](https://github.com/eklu654/Trading-Bot/actions/runs/38383529041) completed successfully and appended the 2026-10-12 completed session. The manifest now reports `last_observation=2026-10-12`, 3 rows total, and 2 return-bearing sessions; the ledger hash and manifest agree.
- Both B0 and F75 durable states currently show $5,000 equity/cash, TQQQ quantity 0, no pending intent, and `mark_date=2026-10-12`, matching the latest completed signal session. Their persisted account fingerprints differ, and the account-verification step succeeded.
- The QQQ monitor remains explicitly read-only: `.github/workflows/qqq-intraday-monitor.yml` runs `research/qqq_intraday_monitor.py`, which reports `orders_submitted=false` even on threshold breach. It cannot currently exit positions.

## Remaining blockers before declaring ready
1. **Live-session executor proof:** inspect the first scheduled run after the actual market opens. Verify B0/F75 broker account, positions, open/recent orders, fresh TQQQ trade, target sizing, and exact report outcome. If an order is submitted, verify its broker order ID and subsequent status/fill and confirm the durable state matches the broker. If no order is needed or preflight blocks, preserve that explicit reason. A green workflow alone is insufficient.
2. **Emergency-exit implementation:** convert the QQQ -4.5% monitor from read-only reporting to a guarded, durable paper-only exit-intent path for both distinct accounts. Keep it independent of the daily target-signal cadence and avoid duplicate exits.
3. **Recovery semantics:** implement the +10% recovery only after anchoring it to the documented strategy's running low after the shock; persist that low across workflow restarts and specify how re-entry is delayed to a safe, confirmed execution window. Do not infer the anchor from a single poll.
4. **Safety tests:** cover trigger boundaries, stale/missing QQQ data, stale TQQQ quotes, duplicate/concurrent runs, partial fills, rejected orders, unknown POST outcomes, restart recovery, and account separation. Test monitor-to-executor integration, not just isolated threshold math.
5. **Operational cadence:** verify the five-minute schedules are running during the real session, review run duration/queue delays, and ensure emergency-exit processing is not blocked behind slow research workflows or the daily target workflow.

## Safety / scope
Paper API endpoint only. Never log raw credentials or account IDs. Never blindly retry an ambiguous POST. Do not declare ready until live-session broker reconciliation is evidenced and the emergency-exit path is implemented and tested. This note records readiness evidence and remaining gaps; it does not claim a successful trade.

## Artifact-level review — 2026-10-13 10:48 UTC
- Downloaded and inspected artifact `alpaca-paper-order-executor-audit` (run 38383606683; artifact ID 11804348174; SHA-256 digest reported by GitHub: `6a06771694355daebfc8c3f0a6e2dad079f933b3567a19ab3b8887dcb113de4e`).
- B0 and F75 prepare reports both say `SKIPPED_MARKET_CLOSED`, with signal session `2026-10-12` and target weights B0=1, F75=1.
- Both arm reports say `NO_ARM_REQUEST`; both order reports say `NO_PENDING_INTENT` and `No POST attempted.` This confirms no order was sent by that diagnostic run.
- Run job steps all passed, including compilation/tests, account verification, prepare, arm, submission/reconciliation wrapper, and audit upload. This is a successful diagnostic workflow but not a trade test.
- At review time the latest available executor run was still the push-triggered closed-market diagnostic. No live-session order acceptance/fill has yet been observed in the reviewed run list.
- Operationally, GitHub cron uses UTC. The current `13-20 UTC` window spans the US session in daylight time, but its first attempts begin before the 09:30 ET open and the last hour is truncated at 20:00 UTC. Alpaca's broker clock is the authoritative gate; expect closed-market skips before 09:30 ET.
