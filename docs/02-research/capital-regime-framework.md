# Capital-Regime Research Framework

**Status:** Active research — 2026-09-30

## Objective

The starting account balance is a temporary operating condition, not a permanent
constraint on the strategy design.

The research should answer two separate questions:

1. Which trading system has the strongest evidence of durable risk-adjusted
   performance across market regimes?
2. Does the optimal implementation change at lower account values, and if so,
   what capital threshold should trigger a transition?

A strategy should not be rejected solely because a particular implementation is
inefficient at $2,000. Conversely, a strategy should not receive permission to
take extreme risk merely because the account is small.

## Capital ladder

The initial sensitivity ladder is:

- $2,000
- $3,000
- $5,000
- $7,500
- $10,000
- $15,000
- $25,000
- $50,000
- $100,000

These are research checkpoints, not predetermined strategy-transition points.

## Metrics

At each capital level, measure:

- position-sizing feasibility;
- buying-power utilization;
- diversification;
- transaction-cost sensitivity;
- expected and realized drawdown;
- tail-loss exposure;
- number of simultaneous positions;
- trade opportunity loss caused by capital constraints;
- time required to reach the next capital checkpoint;
- probability/frequency of falling back below a checkpoint.

## Low-capital configuration

A distinct low-capital configuration is justified only if evidence shows that
the mature strategy is materially constrained by account size and that an
alternative configuration improves capital progression without introducing
unacceptable additional ruin/tail risk.

The low-capital configuration should have an explicit transition rule rather
than becoming a permanently aggressive strategy.

## Transition testing

Candidate transition thresholds must be selected without using the final
holdout to optimize them.

For each candidate threshold, evaluate:

1. historical performance below the threshold;
2. performance after crossing the threshold;
3. frequency of crossing back below it;
4. drawdown and tail behavior around transitions;
5. whether the transition remains useful under conservative execution
   assumptions.

The final holdout is reserved for confirming the selected framework.

## Decision principle

The system should optimize for durable long-term growth and survival, while
recognizing that efficiently leaving the low-capital regime can be a legitimate
objective.

The research must therefore distinguish:

- **capital-constrained strategy failure** — the strategy itself is sound but
  cannot be implemented efficiently at the current balance;
- **strategy failure** — the underlying edge does not survive validation;
- **risk-budget failure** — acceptable returns require excessive tail risk;
- **transition failure** — changing configurations at a capital threshold makes
  the system less robust.

No capital threshold is authoritative until these distinctions are tested.
