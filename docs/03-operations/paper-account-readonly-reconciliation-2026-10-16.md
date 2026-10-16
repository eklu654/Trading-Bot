# Paper Account Read-Only Reconciliation Snapshot — 2026-10-16

## Scope and timestamp

Read-only queries were made through the connected Alpaca paper-account tools at approximately **2026-10-16 04:02 Eastern (03:02 Central)**, before the regular session. No order, cancellation, replacement, account-setting, or other broker write was called.

## Results

| Check | B0 | F75 |
|---|---:|---:|
| Account status | ACTIVE | ACTIVE |
| Currency | USD | USD |
| Trading blocked | false | false |
| Market open at query | false | false |
| Open orders returned | 0 | 0 |
| TQQQ position quantity | 64.170 | 64.228 |
| Ledger TQQQ quantity | 64.170 | 64.228 |
| Ledger pending intent | none | none |
| Ledger mark date | 2026-10-15 | 2026-10-15 |
| Ledger emergency latch | none | none |

The quantities agree exactly between each broker position response and the corresponding JSON ledger on `paper-execution-ledger`. Broker cash also agrees with ledger cash to the precision shown by the connector (B0 about $14.14 vs ledger $14.149300; F75 about $20.23 vs ledger $20.238600). Both ledgers contain persisted broker-account fingerprints and recent fill activity IDs.

## Important qualification

This was a set of independent read-only API calls, not an atomic account snapshot. The returned account-level market value/equity and position-level current-price/value fields were not perfectly synchronized within the response set. Do not treat that difference as a confirmed ledger defect or use those fields as a same-timestamp equity reconciliation. The ledger is marked through the prior session (2026-10-15), while broker position marks can move independently. Re-run a coherent fill/position reconciliation during the next executor cycle.

## Operational interpretation

- The paper account connections are responsive, both accounts are active/unblocked, and current TQQQ quantities match the durable ledgers.
- There are no open orders and no staged/pending intents in either ledger at this snapshot.
- No emergency latch was active in either ledger at this snapshot. This is not a statement that an emergency condition could not arise later.
- The next scheduled executor pass still needs to reconcile fresh broker fills/positions and advance state through the latest completed signal session before any new intent is eligible.
- This read-only check does **not** prove a future emergency sell will submit/fill; the controlled end-to-end paper sell test remains outstanding.

## Audit trail

Source state files:
- `data/paper_execution/b0_state.json` on `paper-execution-ledger`
- `data/paper_execution/f75_state.json` on `paper-execution-ledger`

Source workflows/scripts:
- `.github/workflows/alpaca-paper-order-executor.yml`
- `.github/workflows/qqq-intraday-monitor.yml`
- `research/alpaca_paper_order_executor.py`
- `research/record_emergency_exit_latch.py`

No strategy rule, workflow, ledger, or broker account was changed by this snapshot.
