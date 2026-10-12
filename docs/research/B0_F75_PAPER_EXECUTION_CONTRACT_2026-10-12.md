# B0/F75 Paper Execution Contract — 2026-10-12

## Frozen portfolio contract

| Field | B0 control | F75 experiment |
|---|---|---|
| Instrument | TQQQ | TQQQ |
| Direction | Long or flat | Long or flat |
| Initial virtual allocation | $5,000 | $5,000 |
| Target when baseline signal is flat | 0% | 0% |
| Target when baseline is active | 100% | 75% or 100%, per frozen overlay state |
| Purpose | Control portfolio | Experimental comparison |

F75 remains an overlay on B0 eligibility. It does not independently enter when B0 is flat. The $5,000 is initial virtual capital, not a fixed daily notional cap: target notional must use the evolving virtual portfolio equity. The virtual equity is separate from whatever default cash/equity Alpaca displays for a paper account. Until a fill-backed virtual-equity ledger exists, the shadow equity is only a reference for diagnostics, not sufficient authority for order submission.

## Current state, verified 2026-10-12

- Both credentials authenticate against Alpaca's paper API.
- Both accounts are ACTIVE, USD, and not account- or trading-blocked.
- Both accounts had zero positions and zero open orders at the preflight.
- Broker clock data was reachable; the market was closed during the check.
- Evidence: [credential check](https://github.com/eklu654/Trading-Bot/actions/runs/38199438537) and [read-only preflight](https://github.com/eklu654/Trading-Bot/actions/runs/38199816562).

## Mandatory execution gate

Do not submit an order until every item below is implemented and independently checked:

1. **Fresh signal:** derive B0 and F75 from the latest completed session only; never use the last historical signal as if it were current.
2. **Causal timing:** a close-derived decision may only affect the next eligible execution session.
3. **Paper-only endpoint:** hard reject any endpoint other than https://paper-api.alpaca.markets.
4. **Account identity:** select the correct independent B0/F75 key pair and verify the account is ACTIVE and unblocked.
5. **Reconciliation:** fetch broker positions, open orders, recent orders/fills, and clock before planning; broker state controls actual exposure.
6. **Fixed sleeve:** calculate target notional from the $5,000 virtual allocation, not the account's default NLV.
7. **Idempotency:** deterministic client order IDs; after a timeout or unknown result, reconcile before any retry.
8. **Risk and data gates:** fail closed for stale/inconsistent prices, missing data, an unresolved open order, blocked account, or exposure above the frozen sleeve.
9. **Durable ledger:** persist signal date, source hashes, target, current position, order intent, client/broker order IDs, fills, and reconciliation outcome without credentials.
10. **Fault tests:** cover duplicate submission, unknown outcome, partial fill, rejection, stale data, unexpected position, restart, and session boundaries.

## Promotion boundaries

- Diagnostic tracking starts immediately and continues alongside research.
- The 252-return-bearing-session plus active-overlay-event requirement is for the preregistered efficacy review, not for starting the comparison.
- F75 stays frozen and experimental until its predefined evidence gates are met.
- No live trading is authorized by this contract.
- The read-only preflight and this contract do not claim that any order has been submitted.
