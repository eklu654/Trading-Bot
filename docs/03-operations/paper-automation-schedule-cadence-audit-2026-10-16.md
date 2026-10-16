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
