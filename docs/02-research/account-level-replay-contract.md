# Account-Level Options Replay Contract

**Status:** research specification; not production trading logic  
**Applies to:** OPTIONS-001 feasibility replay and, later, SWITCH-001 options sleeve  
**Purpose:** define what an account-level replay must calculate before interpreting historical options P/L as feasible for a small account.

## 1. Non-negotiable distinctions

The replay must not conflate:

- **Trade economics:** option-leg cash flows and mark-to-market P/L.
- **Capital usage:** buying power required by a position or order.
- **Feasibility:** whether the account could have entered and maintained the position under the selected account and broker assumptions.
- **Strategy performance:** returns after all accepted trades, rejected opportunities, fees, and account-level constraints.

The current one-contract SPY replay is a trade-economics study. Its P/L must not be presented as a return on a $2,000 account.

A modeled BPR estimate is not a historical broker preview. Actual broker-reported buying power must be stored separately when available.

## 2. Replay modes

Every result must identify one mode:

| Mode | Meaning | Permitted interpretation |
|---|---|---|
| trade_economics | Replays selected contracts without account constraints | Contract-level outcome only |
| account_feasibility_estimate | Applies modeled sizing, fees, buying-power and risk gates | Conditional estimate under disclosed assumptions |
| broker_reconciled | Uses broker preview/account-state records for the relevant paper account | Broker-observed feasibility for the captured period |

Never silently upgrade a result from one mode to another.

## 3. Input contract

Each candidate entry must include:

- candidate_id (stable unique identifier)
- strategy_id, regime_label, signal_timestamp
- underlying, structure_type, and complete ordered option legs
- expiration, entry_quote_timestamp, and source-data version
- per leg: contract identifier, call/put, long/short, strike, multiplier, bid, ask, mark, delta, and available liquidity fields
- configured target DTE/delta and the rule-set version that generated the candidate

Each account snapshot must include:

- account identifier and starting NLV
- timestamp, cash, open-position marks, accrued fees, and pending-order reservations
- broker-reported equity/buying-power/margin values, if available
- the allocation/risk configuration version

All timestamps must include an explicit timezone or be normalized to a documented exchange-local convention. The replay must reject ambiguous or duplicate keys rather than silently overwrite records.

## 4. Accounting model

For each position, maintain signed quantities and cash flows by leg. For a credit opening order, cash received is positive; for a debit closing order, cash paid is negative. Fees are separate cash outflows.

At each valuation timestamp:

- cash reflects settled modeled trade cash flows, fees, and explicit external cash flows.
- position_market_value is the sum of signed leg market values using a declared mark convention.
- NLV = cash + position_market_value.
- Open-position BPR and stress estimates are recalculated at each available valuation mark using the contemporaneous underlying price and option liability mark. These remain modeled estimates unless reconciled to broker snapshots.
- If a required mark is missing, retain the last known mark only as a clearly flagged stale valuation; do not treat it as a current quote or silently advance the valuation date.
- realized_pnl is calculated from closed lots and their actual modeled cash flows.
- unrealized_pnl is calculated from open lots relative to their entry cash flows.
- equity_return uses a declared denominator and must account for deposits/withdrawals separately.

The implementation must specify treatment of dividends, corporate actions, early exercise, assignment, expiration, and missing quotes. If the data cannot support a treatment, label it as omitted and do not imply full account realism.

Do not infer that a position is risk-free because its current mark is small or its BPR is low. Undefined-risk positions require explicit stress assumptions; defined-risk positions require expiration max-loss calculation from all legs and multipliers.

## 5. Candidate decision ledger

Write one row per candidate and account, including rejected candidates. Preserve all applicable rejection codes.

Required fields:

- candidate and account identifiers
- pre-trade NLV, cash, available buying power, and open positions
- VIX band, aggregate BP ceiling, and remaining sleeve capacities
- theoretical risk budget, integer quantity, and quantity-reduction reason
- pre/post-trade BPR estimate and methodology version
- defined-risk max loss, where applicable
- pre/post underlying concentration, beta-weighted Delta, gamma, notional, and correlation measures where available
- event, expiration, assignment, quote-quality, and transaction-cost checks
- accepted/rejected decision, complete rejection-code array, and explanation

A fractional contract is never rounded up. A zero-contract candidate remains in the ledger as rejected. Do not replace an infeasible candidate with a different structure unless that replacement is recorded as a separate candidate with its own signal and decision.

## 6. Position lifecycle and sequencing

Process events in deterministic timestamp order:

1. reconcile existing positions and pending orders;
2. apply corporate actions and expiration/assignment events supported by the model;
3. mark open positions using the configured quote policy;
4. update account NLV, buying power, and risk measures;
5. evaluate exits for existing positions;
6. evaluate new candidates against the post-exit account state;
7. record orders, fills, fees, and rejection outcomes;
8. persist the resulting account snapshot.

No future quote, future regime label, or future data revision may be used at a decision timestamp. Entry signals must use information available at or before the decision time. If a signal is computed from end-of-day data, the earliest permissible fill must be explicitly specified (normally no earlier than the next session).

## 7. Execution assumptions

Every run must state:

- entry and exit fill convention (bid/ask, midpoint, or other)
- whether partial fills are modeled
- fees and per-contract charges
- treatment of wide, crossed, stale, or missing markets
- order timing and whether fills are possible at the quoted timestamp
- slippage sensitivity assumptions

Midpoint fills are a sensitivity case, not a guaranteed execution. If only daily EOD quotes exist, the result is not an intraday execution simulation. A position that cannot be marked or exited under the declared data policy must be flagged, not silently assigned a favorable price.

## 8. Required validation tests

Before trusting an account-level replay, test at minimum:

1. **Cash-flow signs:** opening credits increase cash; closing debits and fees reduce cash.
2. **NLV identity:** NLV equals cash plus signed position market value at every snapshot.
3. **Closed-trade reconciliation:** realized P/L equals entry and exit cash flows net of fees.
4. **Quantity integrity:** quantities are nonnegative integers; leg ratios and signs are preserved.
5. **Expiration integrity:** all legs in a defined multi-leg position share the intended expiration unless the structure explicitly permits otherwise.
6. **No look-ahead:** decisions cannot read later timestamps or future regime labels.
7. **Buying-power gate:** an order that exceeds available modeled/broker BP is rejected.
8. **Aggregate constraints:** a candidate that passes alone but breaches a portfolio limit is rejected.
9. **Rejected-opportunity retention:** every candidate receives an outcome and rejection reasons are not lost.
10. **No-trade path:** zero feasible trades produces a valid report with counts and reasons, not a crash or fabricated return.
11. **Reproducibility:** identical data, code, configuration, and seed produce identical outputs.
12. **Sensitivity separation:** conservative and midpoint execution runs remain separately labeled.

## 9. Reporting requirements

For each tested account size, publish:

- starting/ending NLV and net external cash flows
- realized/unrealized P/L, fees, and return methodology
- candidate count, accepted count, rejected count, and entry conversion rate
- rejection counts by reason (reasons may overlap)
- completed trades, average/median P/L, win rate, worst trade, and drawdown
- concurrent positions and peak/median BPR as a percentage of NLV
- maximum observed BPR expansion and duration near configured limits
- mark coverage, stale-mark intervals, and whether BPR/stress were recalculated from contemporaneous option and underlying marks
- a timestamped account valuation path including cash, signed open-position value, NLV, open-position count, aggregate modeled BPR, and aggregate modeled stress loss; calculate drawdown from this path, not only from candidate-entry snapshots
- defined-risk maximum-loss exposure and named stress-scenario losses
- data coverage, missing-quote rate, execution assumptions, and all model limitations

Always report both unconstrained trade-economics results and account-constrained results, side by side but not as directly equivalent performance measures.

## 10. Acceptance criteria

The account-feasibility replay is not ready for use in strategy comparison until:

- the ledger and accounting tests above pass;
- all output fields identify modeled versus broker-observed values;
- account-level constraints are applied sequentially and reproducibly;
- rejected candidates remain auditable;
- data coverage and execution assumptions are present in the report;
- a second independent reconciliation confirms cash, positions, and NLV across a sample of dates.

Passing these criteria validates the replay implementation, not the profitability or suitability of the strategy.
