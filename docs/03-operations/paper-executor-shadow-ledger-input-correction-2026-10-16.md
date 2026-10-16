# Paper Executor Shadow-Ledger Input Correction — 2026-10-16

## Finding

The executor workflow had been reading the legacy F75 shadow ledger and manifest. The F75 monitor had already moved to a validated v2 pair because the legacy ledger's persisted return did not reconcile to persisted prices.

## Change made

Commit `2b3e328125a6c51171f8e403688aa08214127f44` on `main` updates `.github/workflows/alpaca-paper-order-executor.yml` to fetch the v2 ledger and manifest from `research/qqq-slow-bear-audit`:

- `data/research/f75_shadow_daily_ledger_v2.csv`
- `data/research/f75_shadow_state_v2.json`

No strategy rules, credentials, or order payload logic were changed.

## Verification timeline

### First dry-run — correctly blocked

Push-triggered executor run [38851008693](https://github.com/eklu654/Trading-Bot/actions/runs/38851008693) passed compile/tests and distinct-account verification, then safely blocked both B0 and F75 in preparation. The reason was `fill-backed virtual ledger is not marked through latest signal session`: the v2 signal ended on 2026-10-14 while the virtual ledgers were marked through 2026-10-15. Intent commit, arm, and submit steps were skipped; no broker POST was attempted.

### Shadow ledger refresh — successful

Monitor run [38851092847](https://github.com/eklu654/Trading-Bot/actions/runs/38851092847) succeeded. It passed all 34 monitor tests, appended one completed session (2026-10-15), and committed the append-only v2 ledger/manifest on `research/qqq-slow-bear-audit`.

Verified manifest summary:
- Last observation: `2026-10-15`
- Rows: 6 total (1 initialization + 5 return-bearing sessions)
- Mode: `SHADOW_ONLY_NO_ORDERS`
- Ledger SHA-256: `44c414b438f6d99f3ef4ccf444ef208edfb69c23103b1ad4220f68a6745a7a64`
- Frozen cutoff remains `2026-10-07`

This resolves the *signal-ledger freshness* side of the earlier mismatch. The executor still needs a fresh dry-run against the updated research branch to prove both signal and fill-backed state now align; no successful prepare result is claimed yet.

## Existing execution safety model

Code review confirms:
- Broker endpoint hard-pinned to `https://paper-api.alpaca.markets`.
- B0/F75 account fingerprints checked for distinct identities.
- Staged intent and `SUBMITTING` state persisted before scheduled-run POST.
- Only scheduled events receive the ephemeral one-run permit; push/manual events are dry-run.
- Existing orders are looked up by client order ID before a new submission.
- Ambiguous POST outcomes are reconciled; no automatic retry without the same-run permit.
- Fresh QQQ checks run before a buy POST, and an active emergency latch blocks a new buy.

## Remaining gap

Historical TQQQ buys and GET-only reconciliation do not prove that the current executor can execute and reconcile an emergency sell. Keep emergency-exit validation open until a controlled paper-only test demonstrates the sell order, filled activity, resulting broker position, virtual-ledger update, and duplicate-order prevention. Do not trigger a synthetic emergency in an unattended scheduled run.

## Next steps

1. Run a fresh push/manual dry-run after the v2 monitor commit and inspect both sanitized prepare reports.
2. If prepare is still blocked, identify the remaining date/state invariant and fix its root cause without weakening fail-closed guards.
3. Run read-only reconciliation and record its state.
4. Design an isolated paper-only emergency-exit test before any order mutation.
