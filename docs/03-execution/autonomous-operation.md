# Autonomous Operation Architecture

**Status:** design specification — 2026-09-28

## 1. Objective
The bot has two simultaneous objectives: make money over a sufficiently robust sample, and operate autonomously without uncontrolled risk from execution or state failures. Safety is not a substitute for profitability, and profitability alone is not enough for deployment.

## 2. Authority hierarchy
Market/data integrity -> broker/account reconciliation -> strategy/regime logic -> candidate selection -> risk engine -> execution engine -> broker.

AI/classification may propose a regime or candidate. It cannot increase size, bypass risk limits, suppress reconciliation failures, declare positions closed without broker evidence, or submit duplicate logical orders.

## 3. Durable state
Persist at least: account NLV/cash/buying power snapshots; positions; open orders; logical strategy positions; broker order IDs; client order IDs; candidate IDs; intended legs/quantities; fills and partial fills; realized P/L; last trusted data timestamp; broker synchronization timestamp; regime; strategy eligibility; risk-engine status; emergency-stop state.

Local state is an audit/cache layer, not the ultimate source of truth. Broker state must be reconciled before trading.

## 4. Startup and restart
Every restart begins in RECONCILIATION, never directly in TRADE.

1. Load durable state.
2. Query broker account, positions, open orders, and recent orders/fills.
3. Reconcile every local logical order and position against broker state.
4. Check option assignment/expiration activity.
5. Verify market/session state.
6. Refresh required market data.
7. Resolve discrepancies or enter HALTED.
8. Only then enter READY.

Any unresolved discrepancy causes a halt rather than autonomous guessing.

## 5. Duplicate-order protection
Every logical order gets a unique internal operation ID and broker-facing client order ID.

Before submission, check local state, broker order state, current positions, and current risk. A network timeout after submission is UNKNOWN OUTCOME, not a failed submission. Reconcile before retrying.

Never blindly retry an uncertain order.

## 6. Execution state machine
Logical orders use explicit states: PLANNED, RISK_APPROVED, SUBMITTING, SUBMITTED, PARTIALLY_FILLED, FILLED, CANCEL_REQUESTED, CANCELED, REPLACEMENT_PENDING, REPLACED, REJECTED, EXPIRED, UNKNOWN, RECONCILED.

UNKNOWN is a safety state requiring broker reconciliation before another action.

For multi-leg options, the strategy position is not considered established merely because the parent order was accepted. Actual fills must be confirmed.

## 7. Streaming plus REST reconciliation
Use Alpaca trade-update streaming for low-latency order events and periodic REST reconciliation for state verification. On startup, reconnect, uncertain submission, or detected divergence, perform targeted or full reconciliation before new orders.

Alpaca documents streaming order updates including fills, partial fills, cancellations and rejections, and recommends streaming for maintaining order state.

## 8. Market/session gate
Before every order: verify broker clock/session state, instrument tradability, option-contract validity, data freshness, and expiration/corporate-action conditions. Do not infer market-open status from the local machine clock.

## 9. Options controls
Verify options approval/trading level, every leg, expiration/strike, position intent, order construction, current buying power, and resulting position state. Monitor assignment and expiration activity.

Alpaca currently supports multi-leg options orders and documents Level 3 support for spreads/straddles. Runtime account permissions must be checked rather than assumed.

## 10. Hard risk limits
Reject new risk when any configured limit is breached: aggregate buying-power allocation; BPR/NLV; stress loss/NLV; single-underlying exposure; beta-weighted Delta; position count; expiration concentration; correlated exposure; drawdown; minimum available buying power; stale-data threshold; or broker/account ineligibility.

Risk is recalculated immediately before submission. Previous approval is invalid after another order changes account state.

## 11. Emergency hierarchy
1. Normal strategy exit.
2. Strategy loss management.
3. Portfolio risk intervention.
4. Account hard limit.
5. Operational emergency halt.

Operational halt means stop opening new risk, preserve existing positions, continue monitoring, execute only pre-authorized hard-risk exits, and require explicit recovery criteria before normal trading resumes.

## 12. Data failure
Missing, stale, inconsistent, or invalid required market data causes a fail-closed state for new entries. Existing positions continue to be monitored through independent data where available. Never invent a favorable mark.

## 13. Broker divergence
If local and broker state disagree, broker state controls actual exposure. Mark the system DIVERGED, stop new entries, persist the discrepancy, and reconcile. Do not submit compensating trades until the discrepancy is understood.

Examples: local flat/broker long; local position/broker flat; unexpected fill; unexpected assignment; unexpected order; quantity mismatch; option-leg mismatch.

## 14. Regime switching
ETF-001 remains the default strategy in normal/trending conditions. OPTIONS-001 becomes eligible only when validated regime logic indicates it is appropriate. A regime change does not automatically liquidate existing options positions; existing positions continue under their structure-specific exits and portfolio hard-risk controls.

No regime threshold is production-ready until it survives chronological validation and account-level testing.

## 15. Profitability gate
Before live deployment require positive net expectancy after realistic fills and fees, acceptable drawdown/tail loss, sufficient trade count, conservative-fill robustness, account-level feasibility at the intended NLV, held-out or walk-forward validation, parameter sensitivity, and no material look-ahead or survivorship bias.

A strategy that works only under midpoint fills, one narrow parameter choice, or a handful of outlier trades is not considered robust.

## 16. Operational readiness gate
Before unattended paper/live operation, test: startup/restart reconciliation; duplicate orders; partial fills; rejected orders; cancel/replace races; websocket disconnect/reconnect; stale data; broker/API timeouts; unexpected positions; assignment/expiration; market-close boundaries; process crashes; idempotent recovery; and audit-log integrity.

## 17. Paper soak test
Paper trading is an operational test environment, not proof of future profitability. Record every strategy decision, risk rejection, order, fill, broker event, reconciliation, restart/reconnect, stale-data incident, divergence, and P/L result.

## 18. Required observability
At any moment the system should be able to answer: what the strategy wants to do; why; what the broker actually holds; what orders are open; what risk is actually carried; what data produced the decision; which rule approved/rejected it; what happened after submission; and when broker state was last reconciled.

## 19. Current project gate
As of 2026-09-28:

- Strategy profitability: still under historical validation.
- $2,000 account feasibility: replay exists, but the latest historical workflow exposed a strike-column schema defect before account-level results could be produced.
- Autonomous execution: not implemented yet.
- Live trading: not authorized by this design.

Immediate priority:
1. Finish the corrected $2,000 account-level replay.
2. Inspect accepted/rejected opportunity rates and the resulting equity path.
3. Resolve accounting/model defects.
4. Run chronological robustness tests.
5. Build the execution engine around the validated strategy contract.