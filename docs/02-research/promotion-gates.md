# Strategy Promotion Gates

**Status:** Active research standard — 2026-09-30

This document defines the minimum evidence required before a research strategy
can advance toward autonomous paper trading or live deployment.

## Gate 0 — Implementation integrity

Required:

- research scripts compile successfully;
- inputs and outputs have explicit schemas;
- signal timing is causal;
- no same-bar/same-close look-ahead is present;
- missing, duplicated, or unresolved lifecycle data is detected rather than silently filled;
- transaction fees and execution assumptions are explicit.

A strategy does not advance if an implementation defect can materially change its result.

## Gate 1 — Historical robustness

Evaluate:

- nearby parameter variants;
- multiple market regimes;
- bull, bear, crash, recovery, low-volatility, high-volatility, and transition periods;
- conservative and midpoint execution assumptions where execution is material;
- drawdown, tail loss, volatility, and opportunity loss;
- sensitivity to transaction costs.

A single unusually strong parameter combination is not sufficient evidence of robustness.

## Gate 2 — Chronological out-of-sample validation

Use a fixed chronology:

1. development/training;
2. validation;
3. untouched holdout;
4. forward paper trading.

Selection and threshold tuning must not use the final holdout.

If a holdout is used to modify the strategy, that holdout is no longer an untouched holdout and a new confirmation period must be established.

## Gate 3 — Regime validity

For regime-dependent strategies, demonstrate that:

- the regime definition is available before the trade decision;
- the regime occurs often enough to matter;
- performance differences are economically meaningful rather than isolated anecdotes;
- the strategy does not depend on an extremely narrow historical regime;
- regime transitions do not create excessive churn or repeated false switching.

The regime selector must be validated separately from the strategy it selects.

## Gate 4 — Capital feasibility

Evaluate the full capital ladder:

- $2,000
- $3,000
- $5,000
- $7,500
- $10,000
- $15,000
- $25,000
- $50,000
- $100,000

Measure position feasibility, buying-power usage, diversification, opportunity loss,
drawdown, tail exposure, transaction-cost sensitivity, and the frequency of
falling back below a capital checkpoint.

A low-capital configuration is justified only when the mature strategy is materially
constrained and the alternative improves capital progression without unacceptable
additional tail or ruin risk.

## Gate 5 — Execution realism

For options and other execution-sensitive systems:

- compare conservative and midpoint fills;
- model commissions/fees;
- verify that required liquidity exists;
- test spread/slippage sensitivity;
- distinguish historical mark-based reconstruction from executable intraday fills;
- reject trades whose lifecycle cannot be reconstructed reliably.

A backtest result based on an optimistic fill assumption is not sufficient for promotion.

## Gate 6 — Risk and failure behavior

The system must have deterministic behavior for:

- stale or missing market data;
- API failures;
- order rejection;
- unknown positions;
- partial fills;
- duplicate events;
- market-data gaps;
- unexpected account equity;
- extreme volatility;
- strategy-state corruption or restart.

The default response to an unresolved safety condition should be to avoid opening new risk
until state is reconciled.

## Gate 7 — Forward paper trading

Before live deployment, compare paper execution against the historical model:

- fill rate;
- realized slippage;
- commissions;
- latency;
- missed opportunities;
- actual position lifecycle;
- signal timing;
- drawdown;
- regime classification.

Large systematic differences must be investigated before live capital is introduced.

## Gate 8 — Limited live deployment

Only after the preceding evidence is satisfactory should a minimal live allocation
be considered.

The first live phase should prioritize operational verification over maximizing returns.
Capital should increase only after observed execution remains consistent with the validated
research assumptions.

## Holdout discipline

The final holdout is a confirmation tool, not an optimization playground.

Any change motivated by holdout observations requires:

1. recording the change and reason;
2. returning the affected research stage to development/validation;
3. reserving a fresh unseen confirmation period.

## Promotion record

Every promoted strategy should have a machine-readable or documented record containing:

- exact strategy/version;
- data version;
- training/validation/holdout dates;
- execution assumptions;
- selected parameters;
- capital configuration;
- known failure modes;
- unresolved limitations;
- evidence supporting each gate;
- date of promotion.

The goal is not to prove that a strategy will make money. The goal is to establish
that its historical edge is robust enough, its risks are bounded enough, its execution
assumptions are realistic enough, and its failure behavior is safe enough to justify
the next research stage.
