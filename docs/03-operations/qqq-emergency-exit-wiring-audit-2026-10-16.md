# QQQ Emergency-Exit Wiring Audit — 2026-10-16

## Purpose

Resolve the earlier open question about whether the QQQ -4.5% monitor is connected to the durable B0/F75 emergency-defense latch and the paper executor. This is a read-only source audit; no Alpaca order was submitted, canceled, or modified.

## Corrected finding: the latch handoff exists

The earlier note in `paper-executor-shadow-ledger-input-correction-2026-10-16.md` described the monitor-to-latch connection as an unresolved integration question. That statement was incomplete. Inspection of the dedicated workflow and its persistence script confirms a concrete handoff:

1. **Monitor workflow:** `.github/workflows/qqq-intraday-monitor.yml` runs the QQQ monitor on a five-minute weekday schedule and also supports manual/push diagnostic runs.
2. **Observation:** `research/qqq_intraday_monitor.py` compares the latest Alpaca IEX QQQ trade with the last completed daily close. At or below -4.5%, it emits `THRESHOLD_BREACHED`; it explicitly does not submit orders.
3. **Durable latch:** the workflow copies the report and `research/record_emergency_exit_latch.py`, fetches the shared `paper-execution-ledger` branch, and processes the report against both `b0_state.json` and `f75_state.json`. When either a fresh breach is present or an existing one-sided latch needs repair, the script writes a common trigger identity to both ledgers and pushes changed state.
4. **Executor fallback:** `research/alpaca_paper_order_executor.py` independently runs `qqq_defense_preflight` before scheduled intent planning and again before a new POST. This reduces dependence on monitor/executor workflow ordering. A fresh breach activates the durable latch; stale or invalid observations fail closed for new planning unless a pre-existing latch already controls the state.
5. **Target override:** `effective_target` maps either portfolio's effective target to zero while its emergency latch is active. Therefore the next eligible scheduled executor pass can stage a TQQQ sell for a long position. A buy pending during defense is canceled/reconciled where possible and cannot be newly submitted after the final defense check.
6. **Recovery:** the persistence script tracks the QQQ trough and a 10% recovery threshold. Release is gated on both portfolio ledgers being flat and having no pending intent. Recovery handling is state/latch logic, not an order-submission action.

## Safety boundaries that remain

- The monitor/latch workflow itself never submits or cancels broker orders. A breach persisted between executor runs is **not an immediate sell**: the sell is planned by a later scheduled executor pass. The configured schedules are nominally five minutes apart, but workflow queueing, Git pushes, concurrency, API latency, and failed runs can add delay.
- Both workflows share the `paper-broker-mutations` concurrency group and use the shared `paper-execution-ledger` branch to reduce write races. This is useful coordination, not proof that every race or outage has been eliminated.
- The executor workflow's scheduled event is the only event allowed to submit paper orders. Push/manual executor runs remain dry-run. The dedicated monitor's push/manual run may still persist a validated defense latch; that state change is not a broker order.
- Existing tests cover monitor threshold/stale data, latch creation and synchronization, buy prevention during defense, and mocked sell-fill reconciliation. These are offline regression tests; they do not prove a real Alpaca paper emergency sell has filled end-to-end.
- A sell intent still depends on successful scheduled execution, valid account/position reconciliation, market availability, fresh price checks, and broker acceptance. If any gate fails, the system can remain invested while the latch blocks new buys; operators must not interpret a persisted latch as proof the portfolio is flat.
- The monitor uses the most recent trade from the IEX feed and polls periodically. It is not tick-by-tick protection and can miss a fast threshold breach between polls or experience stale/missing data.

## Evidence inspected

- `.github/workflows/qqq-intraday-monitor.yml` (workflow schedule, report processing, shared-ledger persistence)
- `research/qqq_intraday_monitor.py` (read-only observation and -4.5% threshold)
- `research/record_emergency_exit_latch.py` (fresh-report validation, common B0/F75 latch, trough/recovery and flatness gates)
- `research/alpaca_paper_order_executor.py` (preflight, latch synchronization, target override, final buy guard, paper-only submission/reconciliation)
- `research/test_qqq_intraday_monitor.py` and `research/test_alpaca_paper_order_executor.py` (offline regression coverage)
- `research/test_executor_fill_reconciliation.py` (mocked sell-fill-to-zero-position regression)

## Next steps

1. Inspect the latest QQQ monitor and executor Actions runs and confirm both are healthy, and confirm the two state files remain synchronized on the paper ledger.
2. At the next supervised market session, verify the ordinary read-only account/position/fill reconciliation before relying on the defense.
3. Design a controlled, explicitly supervised paper-only end-to-end test of a sell intent through broker fill, fill activity, broker position zero, ledger quantity zero, and duplicate prevention on rerun. Do not manufacture a threshold event in an unattended scheduled run.
4. Keep B0 frozen and F75 shadow-only; no strategy promotion follows from this operational audit.

## Change and risk statement

This commit documents an audit correction and residual limitations only. No Python, workflow, strategy rule, credential, or broker account was changed. No Alpaca trading write was made.
