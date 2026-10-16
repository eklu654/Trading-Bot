# Paper Executor Shadow-Ledger Input Correction — 2026-10-16

## Finding

The executor workflow had been reading the legacy F75 shadow ledger and manifest. The F75 monitor had already moved to a validated v2 pair because the legacy ledger's persisted return did not reconcile to persisted prices.

## Changes and verification

### 1. Executor now consumes F75 v2

Commit `2b3e328125a6c51171f8e403688aa08214127f44` on `main` updated `.github/workflows/alpaca-paper-order-executor.yml` to fetch the v2 ledger and manifest from `research/qqq-slow-bear-audit`:

- `data/research/f75_shadow_daily_ledger_v2.csv`
- `data/research/f75_shadow_state_v2.json`

No strategy rules, credentials, or order payload logic were changed.

### 2. First dry-run failed closed for a valid reason

Executor run [38851008693](https://github.com/eklu654/Trading-Bot/actions/runs/38851008693) passed compile/tests and distinct-account verification, then blocked both portfolios in preparation. Reason: `fill-backed virtual ledger is not marked through latest signal session`. At that time the v2 signal ended 2026-10-14 while virtual portfolio state was marked through 2026-10-15. Staging, arm, and submit were skipped; no broker POST was attempted.

### 3. F75 monitor appended the missing session

Monitor run [38851092847](https://github.com/eklu654/Trading-Bot/actions/runs/38851092847) succeeded. It passed all 34 monitor tests, appended one completed session (2026-10-15), and committed the append-only v2 ledger/manifest on `research/qqq-slow-bear-audit`.

Verified manifest:
- Last observation: `2026-10-15`
- Rows: 6 total (1 initialization + 5 return-bearing sessions)
- Mode: `SHADOW_ONLY_NO_ORDERS`
- Ledger SHA-256: `44c414b438f6d99f3ef4ccf444ef208edfb69c23103b1ad4220f68a6745a7a64`
- Frozen cutoff remains `2026-10-07`

### 4. Fresh executor dry-run passed the date guard

A harmless comment was added to the executor regression test to trigger a new push/manual diagnostic run; it does not alter test behavior or order logic. Executor run [38853183639](https://github.com/eklu654/Trading-Bot/actions/runs/38853183639) completed successfully:

- Python compile and executor guardrail tests passed.
- B0 and F75 account identity verification passed.
- Both prepare reports were `SKIPPED_MARKET_CLOSED`, each naming signal session `2026-10-15`. In the current code path, the fill-backed `mark_date == signal_session` check occurs before this market-closed result, so the previous date mismatch no longer blocks preparation.
- Submit reports were `NO_PENDING_INTENT`; each explicitly says no POST was attempted.
- Arm and SUBMITTING steps were skipped because this was a push event, not a scheduled order-enabled event.
- No broker order was placed, canceled, or replaced by this run.

The paired emergency-exit core test workflow [38853183640](https://github.com/eklu654/Trading-Bot/actions/runs/38853183640) also passed.

### 5. Read-only broker snapshot after the dry-run

Direct read-only Alpaca queries returned zero open orders for both accounts. The only recent order returned for each account remained its October 13 TQQQ buy, status `filled`:
- B0: 64.170 shares at average $77.697533
- F75: 64.228 shares at average $77.532562

Account/position snapshots are broker data as of the latest available session and are not a substitute for the next scheduled fill-backed reconciliation. No write API was called in these checks.

## Existing execution safety model

Code review confirms:
- Broker endpoint hard-pinned to `https://paper-api.alpaca.markets`.
- B0/F75 account fingerprints checked for distinct identities.
- Staged intent and `SUBMITTING` state persisted before scheduled-run POST.
- Only scheduled events receive the ephemeral one-run permit; push/manual events are dry-run.
- Existing orders are looked up by client order ID before a new submission.
- Ambiguous POST outcomes are reconciled; no automatic retry without the same-run permit.
- Fresh QQQ checks run before a buy POST, and an active emergency latch blocks a new buy.

### 6. Added offline emergency-sell fill regression test

The existing fill reconciliation suite only exercised buy fills. Added `test_filled_emergency_sell_reconciles_to_zero_position` in `research/test_executor_fill_reconciliation.py`: it starts from a filled long position, applies a mocked TQQQ sell fill, returns an empty broker-position response, and asserts virtual quantity zero, proceeds/cash updated, the fill ID processed, and terminal intent cleared only after position reconciliation. No network call or broker mutation is made by this test.

The first test revision failed because the test assumed `last_terminal_order` stored a `side` field that the schema does not include. Removed that unsupported assertion while retaining the core sell-fill/zero-position assertions. Corrected run [38853334318](https://github.com/eklu654/Trading-Bot/actions/runs/38853334318) passed the emergency-exit core tests and durable ledger/latch tests. Executor run [38853334301](https://github.com/eklu654/Trading-Bot/actions/runs/38853334301) also passed; both prepare reports were `SKIPPED_MARKET_CLOSED`, and both submit reports were `NO_PENDING_INTENT` with no POST attempted.

This improves offline sell-fill reconciliation coverage, but it is not evidence of an actual Alpaca emergency sell.

## Remaining gap

The executor now passes its dry-run date guard, but this does not prove a new scheduled order can be placed, nor that an emergency sell is filled and reconciled end-to-end. Emergency-exit validation remains open until a controlled paper-only test demonstrates the sell order, filled activity, resulting broker position, virtual-ledger update, and duplicate-order prevention. Do not trigger a synthetic emergency in an unattended scheduled run.

## Next steps

1. Allow the next scheduled GET-only reconciliation to run and verify broker position, fill activities, and virtual state remain aligned.
2. Design an isolated paper-only emergency-exit test before any order mutation; explicitly verify sell fill, position zero, ledger quantity zero, and no duplicate sell on rerun.
3. Keep B0 frozen and F75 shadow-only; do not promote a defense on drawdown reduction alone. A defense must improve terminal balance versus its matched control while avoiding near-ruin.

## Follow-up audit — latest workflow snapshot, 2026-10-16 00:06 Central

Checked current GitHub Actions runs and downloaded the sanitized artifact from executor run [38853334301](https://github.com/eklu654/Trading-Bot/actions/runs/38853334301). The artifact confirms:

- B0 prepare: `SKIPPED_MARKET_CLOSED`, signal session `2026-10-15`, no intent staged.
- F75 prepare: `SKIPPED_MARKET_CLOSED`, signal session `2026-10-15`, no intent staged.
- B0 submit/reconcile: `NO_PENDING_INTENT`, no POST attempted.
- F75 submit/reconcile: `NO_PENDING_INTENT`, no POST attempted.

The run passed its compile/test and distinct-paper-account identity checks. It was a push-triggered diagnostic run, so the schedule-only arm/submit gate remained closed. This validates the corrected date path in a market-closed dry-run only; it does not demonstrate behavior during a live market session or successful scheduled order submission.

Latest workflow inventory showed the three checks at commit `fce3bc7e0397152d73460664927e58bde9fad6a9` completed successfully: executor, emergency-exit core tests, and research tests. Earlier test runs at commit `0df8c697d97bff034bf1b56e39a5f2bcca9f9e69` failed during the first test revision; corrected revision passed at `fce3bc7e0397152d73460664927e58bde9fad6a9`.

No new broker mutation was made during this audit. Keep the real emergency-sell integration test and next scheduled-session reconciliation as open operational tasks.

