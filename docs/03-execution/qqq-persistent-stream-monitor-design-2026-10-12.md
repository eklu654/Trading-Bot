# Persistent QQQ Stream Monitor — Design and Audit (2026-10-12)

## Purpose and boundary
This service listens to Alpaca's stock-trade WebSocket stream for QQQ and records intraday -4.5% threshold events against the latest completed daily close. It is **read-only**: it has no order-submission code, does not alter B0/F75 targets, and cannot invoke the paper executor.

## Implemented
- `research/qqq_stream_monitor.py`: authenticated Alpaca IEX WebSocket client; QQQ trade subscription; reconnect loop with exponential backoff (1 to 60 seconds); 20-second ping interval; UTC timestamps; New York regular-session filtering; stale/future trade rejection; fail-closed baseline acquisition; threshold and recovery event detection.
- SQLite event journal with unique `(session, kind)` event keys and WAL journaling. Repeated messages/reconnects do not duplicate the same threshold/recovery event for a session.
- `Dockerfile.qqq-stream-monitor` and pinned `requirements-stream-monitor.txt` for an always-on container deployment with a persistent `/data` volume.
- `research/test_qqq_stream_monitor.py` for deterministic detection and event-idempotency tests.

## Operational assumptions and limitations
- The initial baseline is the most recent QQQ daily bar whose session date is earlier than today's New York date. The stream only evaluates regular-session trade timestamps; extended-hours prints are ignored.
- This is a detection and audit component, not a defensive trading rule. A threshold event is logged once per session, and a recovery event is logged once if price subsequently returns above the threshold during the same process lifetime.
- Credentials are environment variables `ALPACA_PAPER_API_KEY_B0` and `ALPACA_PAPER_API_SECRET_B0`. They are used for authenticated market-data access only; no trading endpoint is called. Store them as hosting-provider secrets, never in the image or repository.
- Mount a persistent volume at `/data`; otherwise the SQLite journal may be lost when the container is replaced. Configure restart-on-failure and health/restart alerts in the host.
- GitHub Actions is not the persistent runtime. The existing five-minute workflow remains a backup monitor; cron is best-effort and can miss short-lived events.
- This service is not yet deployed or validated against a live WebSocket session. Unit tests do not prove hosting uptime, stream entitlement, correct secret configuration, or live event delivery.
- Before connecting this signal to any paper order, separately approve the precise trigger semantics, response sizing, recovery/re-entry policy, and restart reconciliation. No live trading.

## Local test
```sh
python -m pip install -r requirements-stream-monitor.txt
PYTHONPATH=research python research/test_qqq_stream_monitor.py
```

## Next deployment checklist
1. Choose an always-on container host that supports a persistent volume and restart policies.
2. Add the two B0 paper-data credentials as encrypted service secrets.
3. Mount durable storage at `/data`; set restart-on-failure and uptime/error notifications.
4. Deploy initially in read-only observation mode during market hours.
5. Verify auth/subscription acknowledgements, trade freshness, baseline session/close, timestamp behavior, and end-to-end event recording with a controlled test harness (do not wait for or fabricate a live market breach).
6. Keep the GitHub Actions five-minute monitor enabled as fallback.
7. Do not authorize automated defensive orders until a separate rule specification and review is complete.


## Follow-up audit — 2026-10-16

### Why this matters after the polling feed incident

The repository already contains a more appropriate candidate for continuous observation than the GitHub cron poller: `research/qqq_stream_monitor.py`, packaged by `Dockerfile.qqq-stream-monitor`. It subscribes to Alpaca's IEX QQQ trade WebSocket and processes each received trade with a 180-second freshness guard. This avoids relying exclusively on the REST `trades/latest` response that was observed to be about 38.7 minutes stale on 2026-10-15.

However, source inspection and unit tests are **not** proof that a deployed socket receives fresh QQQ trades under the currently connected account's data entitlement. The persistent monitor remains undeployed and unverified against a live WebSocket session. Do not describe it as an operational fix until a host is configured, authentication/subscription acknowledgements are observed, and multiple market-hours trade timestamps are checked.

### Newly noted journal semantics

The SQLite journal uses a unique key of `session:kind`. This intentionally suppresses duplicate threshold/recovery records in a session, including across reconnects. Consequence: it records at most one `THRESHOLD_BREACHED` event and one `RECOVERED_ABOVE_THRESHOLD` event per session. If price crosses below the threshold, recovers, then crosses below again, the second threshold event is suppressed. That is acceptable only while this component remains an observational journal or when downstream policy explicitly treats the first breach as a one-way daily latch. It must not be wired as a re-armable trigger without redesigning episode identity and adding repeat-crossing tests.

### Safe next action

Deploy only in read-only observation mode on an always-on host with persistent `/data`, restart-on-failure, and health/error alerts. Record auth, subscription, last-trade timestamp/age, baseline session/close, and event journal growth. Do not connect the event journal to the executor or change the emergency latch from this monitor until the exact episode/recovery semantics are approved and a supervised paper-only end-to-end test is designed.

No deployment, credential change, broker mutation, or strategy-rule change was performed for this audit.


### Readiness review — 2026-10-16 09:10Z: idle-stream observability gap

A source-level review of `research/qqq_stream_monitor.py`, its unit tests, and `Dockerfile.qqq-stream-monitor` found a further production-readiness gap:

- The 180-second age check runs only when a QQQ trade message is received. It rejects a stale timestamp in a received trade, but it does not independently evaluate the age of the last received trade/message while the socket is idle or the subscription is silently broken.
- The container has no Docker `HEALTHCHECK`, heartbeat file, external heartbeat, or last-message-age alert. The process can therefore remain running without proving that it is authenticated, subscribed, and receiving fresh data.
- Unit tests exercise the pure detector and SQLite event idempotency; they do not test a silent socket, lost subscription, idle timeout, reconnect recovery, or deployment health signals.
- The code resets reconnect backoff after a valid non-stale regular-session trade (and on subscription acknowledgement), but it does not expose a machine-readable service-health state separate from its logs.

**Required before deployment is considered operational:** add an independent last-message/last-trade watchdog and a health signal that becomes unhealthy when authentication/subscription is missing or the stream has no valid regular-session trade for a documented interval; ensure the host can alert on that state. Test disconnect, silent socket, authentication failure, reconnect, and restored fresh trade. Keep this read-only and do not connect it to the order executor as part of this change.

The Dockerfile does create a persistent `/data` volume and runs as a non-root user, which are useful foundations, but those features do not substitute for runtime health checks. No code, Dockerfile, workflow, service, credentials, or broker state was changed during this review.
