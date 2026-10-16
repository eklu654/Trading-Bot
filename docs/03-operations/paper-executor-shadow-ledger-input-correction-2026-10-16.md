# Paper Executor Shadow-Ledger Input Correction — 2026-10-16

## Finding

During continuation of the Alpaca paper execution audit, code review found that the executor workflow still fetched the legacy F75 shadow ledger and manifest:

- `data/research/f75_shadow_daily_ledger.csv`
- `data/research/f75_shadow_state.json`

The F75 monitor had already been migrated to a validated v2 pair because the legacy ledger's persisted return did not reconcile to the persisted prices. Keeping the executor pointed at v1 meant its signal input was not aligned with the currently validated shadow-monitor output.

## Change made

Commit `2b3e328125a6c51171f8e403688aa08214127f44` on `main` updates `.github/workflows/alpaca-paper-order-executor.yml` to fetch:

- `data/research/f75_shadow_daily_ledger_v2.csv`
- `data/research/f75_shadow_state_v2.json`

into the executor's existing local shadow input paths. This changes only the source files read by the paper executor; it does not change B0/F75 strategy rules, broker credentials, or order payload logic.

## Verification result — v2 input loaded, but preparation safely blocked

The push-triggered workflow [38851008693](https://github.com/eklu654/Trading-Bot/actions/runs/38851008693) completed with failure during preparation. The sanitized artifact reports for both B0 and F75 were:

- `status: BLOCKED`
- `reason: fill-backed virtual ledger is not marked through latest signal session`

The compile/test guardrail and distinct-paper-account identity verification steps passed. Both prepare commands were blocked before staging a new intent; the arm and submit steps were skipped. The event was a push event, and the workflow is configured so push/manual runs cannot submit orders. No broker POST was attempted in this run.

The underlying date mismatch is now explicit: the v2 shadow signal ends on 2026-10-14, while both fill-backed virtual ledgers are marked through 2026-10-15. The executor correctly refuses to trade when the portfolio mark date and latest signal session disagree. This is a fail-closed safety result, not a reason to weaken the date guard.

A fresh F75 shadow-monitor run [38851092847](https://github.com/eklu654/Trading-Bot/actions/runs/38851092847) was triggered by an audit-only docstring clarification and is in progress to see whether the monitor can append the latest completed session. Its final result and the next executor dry-run must be checked before considering this issue resolved.

## Existing execution safety model

Code review confirms:

- The broker endpoint is hard-pinned to `https://paper-api.alpaca.markets`.
- B0 and F75 account fingerprints are checked to ensure distinct accounts.
- Staged intent and `SUBMITTING` state are persisted before a scheduled-run POST.
- Only scheduled events receive the ephemeral one-run permit; manual and push events are dry-run.
- Existing orders are looked up by client order ID before any new submission.
- An ambiguous POST outcome is reconciled; automatic retry is not allowed without the same-run permit.
- Fresh QQQ checks run before a buy POST, and an active emergency latch prevents a new buy.

## Remaining gap

The historical TQQQ buys prove that paper orders have filled, and the GET-only reconciliation workflow has reported both accounts synced. They do not prove that the current executor has successfully executed an emergency sell. Emergency-exit validation remains open until a controlled paper-only sell/exit path is demonstrated and the resulting order, fill activity, position, and virtual ledger reconcile. Do not create a synthetic emergency trigger in a live unattended schedule merely to test it.

## Next verification

1. Confirm run 38851008693 completes successfully.
2. Inspect its sanitized prepare and submit reports for B0 and F75 and verify the v2 signal/manifest passed integrity checks.
3. Re-run read-only account reconciliation after the executor change.
4. Design an isolated, explicitly paper-only emergency-exit test with clear position and duplicate-order assertions before any order mutation.
