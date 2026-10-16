# F75 Shadow Ledger Integrity Migration — 2026-10-16

## Purpose

Record the fail-closed response to the legacy F75 shadow ledger's return-reconciliation failure. This is a ledger-integrity repair, not a strategy change.

## Evidence

The legacy file `data/research/f75_shadow_daily_ledger.csv` and its manifest `data/research/f75_shadow_state.json` are preserved unchanged as audit evidence.

The 2026-10-12 row stored:

- Prior recorded adjusted TQQQ close (2026-10-09): `81.2799987793`
- Current recorded adjusted TQQQ open (2026-10-12): `80.7799987793`
- Stored overnight return: `-0.0339632130352`
- Overnight return implied by the two persisted prices: approximately `-0.00615157489554`

The stored return and persisted prices do not reconcile. The monitor correctly failed closed before appending or committing any further observations. All 33 tests passed, while the full monitor failed on the integrity guard.

The evidence is consistent with the refreshed vendor history having a different prior-session close than the immutable legacy ledger row. The exact historical vendor snapshot that produced the stored return is not available, so the original mismatch is not attributed to a more specific cause.

## Resolution approach

- Do not weaken or bypass the return-to-price reconciliation checks.
- Do not rewrite the legacy ledger in place.
- Switch the monitor to a separate append-only v2 ledger and manifest: `f75_shadow_daily_ledger_v2.csv` and `f75_shadow_state_v2.json`.
- The v2 ledger initializes from one consistent current price download after the frozen canonical B0 cutoff, with a fresh $5,000 shadow starting balance. Subsequent appended sessions anchor the first new overnight return to the persisted v2 ledger tail, so a later vendor-history revision cannot silently change the overnight return for an already-recorded prior close.
- Keep B0 frozen, F75 shadow-only, and all broker/order paths untouched.

## Verification result — passed 2026-10-16

- [F75 v2 creation run 38840710375](https://github.com/eklu654/Trading-Bot/actions/runs/38840710375) completed successfully and committed the v2 ledger/manifest at commit `e2c32ff`.
- The v2 ledger contains 5 completed observations from 2026-10-08 through 2026-10-14; 2026-10-08 is the zero-return initialization row.
- A subsequent rerun of the same workflow passed all 34 tests and the existing-ledger integrity checks, then correctly reported no new completed sessions and made no ledger change.
- The v2 manifest's ledger checksum and state counters validated successfully.

No performance conclusion or strategy promotion follows from this operational repair.
