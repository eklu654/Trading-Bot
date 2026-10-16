# Paper Automation Schedule Cadence Audit — 2026-10-16

## Finding

The workflows are configured with five-minute cron expressions, but the available GitHub Actions history does **not** demonstrate five-minute execution cadence. Treat the cadence as unverified and currently unreliable for time-sensitive emergency protection.

## Observed Actions history

Read-only Actions API inspection found these recent scheduled runs:

| Workflow | Run | Created (UTC) | Result |
|---|---:|---|---|
| QQQ Intraday -4.5% Monitor + Paper Defense Latch | [38822279465](https://github.com/eklu654/Trading-Bot/actions/runs/38822279465) | 2026-10-15 23:13:36Z | success |
| Alpaca Paper Order Executor | [38822643862](https://github.com/eklu654/Trading-Bot/actions/runs/38822643862) | 2026-10-15 23:17:05Z | success |
| QQQ Intraday -4.5% Monitor + Paper Defense Latch | [38802556778](https://github.com/eklu654/Trading-Bot/actions/runs/38802556778) | 2026-10-15 20:30:51Z | success |
| Alpaca Paper Order Executor | [38802975499](https://github.com/eklu654/Trading-Bot/actions/runs/38802975499) | 2026-10-15 20:33:55Z | success |
| QQQ Intraday -4.5% Monitor + Paper Defense Latch | [38778425279](https://github.com/eklu654/Trading-Bot/actions/runs/38778425279) | 2026-10-15 17:34:08Z | success |
| Alpaca Paper Order Executor | [38779676063](https://github.com/eklu654/Trading-Bot/actions/runs/38779676063) | 2026-10-15 17:43:17Z | failure |

The observed QQQ monitor starts are separated by roughly 2h43m and 2h57m, not five minutes. The executor starts show similar multi-hour gaps. Workflow run numbers were 15–17 for the monitor, indicating this is not merely a display of many hidden recent executions. GitHub's Actions history/API is not a formal scheduler SLA, but this evidence is insufficient to claim the desired cadence is running.

## What those runs actually prove

- The latest listed monitor run passed its code/tests, but its runtime report was `MARKET_CLOSED` with `orders_submitted=false`. It did not make a fresh market-hours threshold observation.
- The latest listed executor run passed its job, but both prepare reports were `SKIPPED_MARKET_CLOSED` with signal session `2026-10-12`; both submit reports were `NO_PENDING_INTENT` and said no POST was attempted.
- The later F75 v2 ledger append on 2026-10-16 repaired the signal date to 2026-10-15, and the push-triggered executor diagnostics passed. Those diagnostics are not evidence of the next scheduled market-hours execution.
- The schedule-only order gate is still present, so push/manual executor runs do not submit orders.

## Risk and decision

A workflow cron expression is not equivalent to a reliable always-on polling service. If the QQQ monitor is not invoked near its configured cadence, the -4.5% threshold can be observed late or missed between polls; if the executor is not invoked, a persisted latch may not become a sell intent promptly. Even with a healthy five-minute cadence, this is periodic polling, not tick-by-tick protection.

Do not describe the paper executor as proven ready for unattended emergency exits based only on successful compile/tests or market-closed runs. Before relying on it:
1. Inspect GitHub Actions schedule/event configuration and the full run history to determine why the configured cadence is not reflected in observed starts.
2. Verify actual market-hours schedule execution and report freshness over multiple consecutive intervals.
3. If GitHub-hosted cron cannot meet the required latency, move the monitor/executor scheduler to a dependable always-on process or service with health checks, while keeping paper-only credentials and one-run mutation permits.
4. Complete the supervised paper sell/fill/position/ledger/duplicate-prevention integration test.

## Safety statement

This audit was read-only. No workflow, code, strategy, ledger, account configuration, or broker order was changed.


## Additional live-session feed finding and observability correction

Inspection of market-hours run [38778425279](https://github.com/eklu654/Trading-Bot/actions/runs/38778425279) found that the monitor returned `STALE_TRADE_FAIL_CLOSED` at 2026-10-15 17:34:16Z: the latest QQQ IEX trade was timestamped 16:55:32Z, about **2,323 seconds (38.7 minutes) old** while the broker clock was open. The monitor workflow nevertheless completed successfully and the latch persistence script returned `NO_FRESH_SIGNAL`. The executor run [38779676063](https://github.com/eklu654/Trading-Bot/actions/runs/38779676063), roughly nine minutes later, failed both portfolio preparations with `QQQ defense preflight trade is stale or invalid`. No new order was submitted by that failed run.

This means the issue is not only cadence: the configured IEX latest-trade source was stale during a market-hours observation. The fail-closed behavior prevented unverified planning, but also meant no new breach could be established from that observation.

To make this visible rather than green-but-stale, commit [82be8a70991414b17fe1a5ee45fdac3ce0cd07bf](https://github.com/eklu654/Trading-Bot/commit/82be8a70991414b17fe1a5ee45fdac3ce0cd07bf) adds a workflow guard after report generation: a `STALE_TRADE_FAIL_CLOSED` report now fails the monitor workflow visibly before latch persistence. The artifact upload remains `if: always()`, preserving the stale report for diagnosis. This is an observability improvement only; it does not repair the data feed or create an emergency sell.

**Next blocker to resolve:** establish why the IEX latest-trade endpoint was nearly 39 minutes stale for QQQ while the market clock was open. Validate repeated timestamps against an independent permitted real-time feed/quote source and confirm subscription/feed semantics before changing the trigger price source. Do not relax the 180-second freshness guard merely to make the workflow green. Until fresh market-hours observations and reliable schedule cadence are demonstrated, do not rely on this as unattended emergency protection.


### Feed entitlement check

A follow-up read-only query of historical QQQ trades on the IEX feed for 2026-10-15 16:50–17:35Z returned IEX prints only through 16:55:32Z, consistent with the stale timestamp in the workflow log. A request for recent SIP data was rejected with HTTP 403: `subscription does not permit querying recent SIP data`. Therefore, switching the workflow to SIP is not currently a verified available fix under this account's market-data entitlement. Do not simply change `feed=iex` to `feed=sip`; first obtain an authorized, real-time source or a supported quote source and test its freshness end-to-end.


## Continuation checkpoint — 2026-10-16 08:55Z

- Latest Actions history checked again: the newest monitor run remains push-triggered run [38871234196](https://github.com/eklu654/Trading-Bot/actions/runs/38871234196), successful after the stale-report visibility guard. There is still no newer scheduled market-hours run in the inspected history, so fresh-feed and schedule-cadence recovery are not yet demonstrated.
- Repository already contains a persistent WebSocket candidate: `research/qqq_stream_monitor.py`, tests in `research/test_qqq_stream_monitor.py`, and `Dockerfile.qqq-stream-monitor`. Its tests cover threshold/staleness/idempotency, but design notes say it has not been deployed or validated against a live stream.
- Follow-up commit [69f832c12bc4925c72f06e9cdba78c9968494d69](https://github.com/eklu654/Trading-Bot/commit/69f832c12bc4925c72f06e9cdba78c9968494d69) records this candidate's readiness boundary and a per-session event-journal limitation: only one threshold and one recovery event are stored per session, so a second breach after recovery is deduplicated. This is acceptable only as a one-way daily observational latch; do not treat it as a re-armable downstream trigger.
- No order-writing tool was called. No broker, strategy, or account state was modified.

### Immediate queue

1. Validate the IEX WebSocket in read-only mode during actual market hours and record timestamps/ages across repeated trades.
2. Investigate the schedule history/configuration mismatch; do not infer cadence from cron text.
3. If the stream proves fresh, deploy it as a monitored read-only service with durable SQLite storage and restart/health alerts.
4. Only after signal freshness and service uptime are demonstrated, plan a separately reviewed paper-only order/fill/position/ledger integration test.


### Concurrency is another cadence constraint

Both workflows use the same GitHub Actions concurrency group, `paper-broker-mutations`, with `cancel-in-progress: false`; the monitor job timeout is 3 minutes and executor timeout is 6 minutes, while both cron expressions request five-minute intervals. Sharing the group is intentional to protect shared ledger writes, but it serializes monitor and executor work. GitHub concurrency is not a durable FIFO queue for every scheduled tick: when work overlaps or the runner queue backs up, do not assume every five-minute occurrence will eventually execute in order. This is a plausible contributing risk, not a proven root cause for the observed multi-hour gaps. Confirm with per-run queue/start timestamps and cancellation/suppression evidence before changing the mutual-exclusion design; do not remove the shared guard without replacing ledger-write coordination.


## Continuation checkpoint — 2026-10-16 09:10Z: Actions API cadence cross-check

Read-only query of the repository's most recent 100 Actions runs returned 11,015 total runs but only a small number of runs for these two workflows. The observed scheduled runs remain:

| Workflow | Run | Created (UTC) | Event/result |
|---|---:|---|---|
| QQQ monitor | [38822279465](https://github.com/eklu654/Trading-Bot/actions/runs/38822279465) | 2026-10-15 23:13:36Z | schedule / success |
| Executor | [38822643862](https://github.com/eklu654/Trading-Bot/actions/runs/38822643862) | 2026-10-15 23:17:05Z | schedule / success |
| QQQ monitor | [38802556778](https://github.com/eklu654/Trading-Bot/actions/runs/38802556778) | 2026-10-15 20:30:51Z | schedule / success |
| Executor | [38802975499](https://github.com/eklu654/Trading-Bot/actions/runs/38802975499) | 2026-10-15 20:33:55Z | schedule / success |
| QQQ monitor | [38778425279](https://github.com/eklu654/Trading-Bot/actions/runs/38778425279) | 2026-10-15 17:34:08Z | schedule / success |
| Executor | [38779676063](https://github.com/eklu654/Trading-Bot/actions/runs/38779676063) | 2026-10-15 17:43:17Z | schedule / failure |

The workflow-specific run numbers and repository-wide recent history do not show the dozens of scheduled invocations expected during the approximately 6.5-hour regular market session. The 2026-10-16 08:04Z successful run [38871234196](https://github.com/eklu654/Trading-Bot/actions/runs/38871234196) is explicitly a `push` event, not schedule evidence. This cross-check strengthens the conclusion that five-minute cadence is not being demonstrated; it does not establish why. The available fetch wrapper rejected workflow-specific run-list endpoints, so queue-time/cancellation/suppression details could not be exhaustively recovered from that endpoint.

### Cron-window and concurrency interpretation

Both schedules are UTC-based and request five-minute invocations across 13:00–21:59Z weekdays. In mid-October, the regular US equity session is approximately 13:30–20:00Z. The broker-clock gate is therefore necessary because the configured cron window intentionally includes pre-open and post-close intervals. The monitor's minute offsets are 1,6,11,... and executor offsets 2,7,12,...; if both schedules fired normally, they should be staggered rather than intentionally simultaneous.

The jobs normally complete in roughly 11–20 seconds in the observed runs, while their timeouts are 3 and 6 minutes. That makes ordinary runtime overlap alone an insufficient explanation for multi-hour gaps. The shared concurrency group can still serialize delayed/overlapping jobs, but no evidence presently proves it caused the gaps. Treat scheduler delivery/enablement/visibility as unresolved; do not change concurrency or remove the ledger coordination based on speculation.

### Current readiness decision

As of this checkpoint, neither reliable five-minute polling nor fresh market-hours IEX trade data is established. The monitor has a fail-closed stale-data guard, which is appropriate; do not disable it to create green workflow runs. No workflow dispatch, order submission, ledger write, or broker mutation was performed during this audit update. Next useful evidence must come from multiple consecutive market-hours scheduled runs with timestamps and fresh observation ages, plus a permitted independent real-time data source comparison.


### Follow-up: schedule-event timestamps fall outside the checked cron hours

I fetched the exact workflow files at commit `5c7f0fbd06460c6441caf93199dbce7d84259433`, the head SHA recorded on the three recent scheduled monitor runs and corresponding executor runs. At that SHA, the cron expressions are already the current UTC hour ranges `13-21`. Yet scheduled runs were created/started at 23:13Z on 2026-10-15 (monitor run [38822279465](https://github.com/eklu654/Trading-Bot/actions/runs/38822279465), executor [38822643862](https://github.com/eklu654/Trading-Bot/actions/runs/38822643862)), and the previous monitor run [38656061892](https://github.com/eklu654/Trading-Bot/actions/runs/38656061892) was created at 23:45:55Z on 2026-10-14. Those UTC hours are outside the configured 13:00–21:59Z cron window.

This is additional evidence of a schedule-delivery/timestamp discrepancy, not proof of its root cause. The run details show `created_at` and `run_started_at` equal, so the available metadata does not distinguish delayed schedule-event delivery from another GitHub Actions scheduling/reporting behavior. The exact workflow contents at the recorded head SHA rule out a simple explanation that those runs used a different cron expression. Do not infer the scheduled tick's intended minute from run creation time, and do not attempt to “fix” this by changing the cron hours without first collecting reliable scheduled-run metadata. The operational conclusion remains: five-minute market-hours polling is not proven.
