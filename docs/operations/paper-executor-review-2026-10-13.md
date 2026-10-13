# Paper Executor Review — 2026-10-13

## Scope and evidence

Reviewed the current default-branch source directly through GitHub:
- `research/alpaca_paper_order_executor.py` blob `b10c059b89445269cdac53724f844086232c9f9f`
- `research/paper_virtual_portfolio.py` blob `dc3934f32781abc1381ab3d6e5428fd8b13ac6f3`
- Existing readiness gate: [market-open-readiness-2026-10-13.md](market-open-readiness-2026-10-13.md)

This was a source review, not a runtime test. No broker mutation was performed.

## Confirmed safeguards

- Broker mutation URL is hard-pinned to Alpaca paper API.
- Account verification rejects non-active/blocked accounts, non-USD accounts, and identical B0/F75 account identities.
- TQQQ-only long exposure is enforced; unexpected positions and untracked bot-tagged orders block.
- The latest market trade must be no more than 180 seconds old and price drift over 0.25% aborts a staged order.
- Durable intent is moved to `SUBMITTING` before POST; ambiguous POST results are looked up by exact client order ID and are not blindly retried.
- Fill activity IDs are idempotent, sells exceeding the virtual long quantity are rejected, and terminal intent completion requires broker quantity reconciliation.

## Gaps that remain release-blocking

1. **No broker lifecycle evidence:** source inspection and mocked tests do not prove that either paper account can place, fill, and reconcile an order using the scheduled workflow.
2. **Emergency exit is absent from this executor interface:** CLI modes are only `verify-accounts`, `prepare`, `arm`, and `submit`. There is no dedicated shock-trigger/exit-intent command here. A separate monitor must not be called operational until its signal, durable state, and order lifecycle are wired and verified.
3. **Workflow authorization needs end-to-end confirmation:** the executor's `ENABLE_PAPER_ORDER_SUBMISSION` environment flag is necessary but not sufficient. Workflow-level event gating and same-run permit handling must be inspected together before enabling it.
4. **Terminal order reconciliation requires a demonstrated complete path:** state helpers expose fill application and terminal completion, but a paper run must show broker activities applied exactly once and broker positions matching the ledger before the intent clears.
5. **Cross-process concurrency must be tested:** filesystem state writes alone do not establish atomic locking between the five-minute monitor and executor. Overlapping runs must fail closed or use a shared concurrency/locking mechanism.

## Next implementation/verification sequence

- Inspect the exact workflow YAML and monitor source; verify scheduled-only submission gates and artifact redaction.
- Add an emergency-exit path that uses the same paper-only broker adapter, durable idempotency, and fill reconciliation as normal orders; do not create an independent unsafe POST implementation.
- Add deterministic tests for trigger persistence, duplicate trigger, restart, partial fill, rejected exit, ambiguous response, and no-short enforcement.
- Run the full unit suite and a dry-run workflow first.
- During eligible market hours, run a deliberately small paper-only lifecycle on B0 and F75 separately, then reconcile broker order, fills, positions, and ledger.
- Keep the no-new-orders gate in place until all acceptance criteria in the readiness audit pass.

## Audit log

2026-10-13: Read-only source review completed. Findings above are grounded in the current source blobs and are not claims that tests or broker operations were executed. No credentials, account IDs, or tokens are included.
