# Small-Account Options Feasibility Research

**Status:** Research decision — not a production rule  
**Last reviewed:** 2026-09-28

## 1. Finding

The historical 2020 portfolio framework remains useful as a provenance baseline, but current tastylive research makes clear that small accounts face structural constraints when using undefined-risk positions.

In June 2025, tastylive specifically documented that small accounts can face substantially higher BPR and BPR volatility with naked positions. It reported an example in which a 15% IWM move increased BPR by more than 200%, with a worst-case example reaching 3.6× initial BPR. It also notes that lower-priced underlyings can improve premium-to-BPR efficiency.

A separate June 2025 guide says that $10,000 accounts already face meaningful constraints with naked strategies and suggests risk-defined structures such as spreads, iron condors, and time spreads for broader diversification.

These sources do not establish a universal rule that $2,000 accounts must use defined risk. They establish that account size materially changes the feasible strategy universe.

## 2. Project implication

The $2,000 OPTIONS-001 account must therefore be treated as a **feasibility experiment**, not simply as a scaled-down implementation of the historical 75/25 framework.

The system must measure:

- percentage of candidate trades rejected because of contract granularity;
- percentage rejected because of BPR;
- percentage rejected because of NLV sizing;
- percentage rejected because of the 15% underlying concentration limit;
- number of simultaneously feasible positions;
- achievable diversification;
- BPR expansion under stress;
- defined-risk versus undefined-risk opportunity frequency.

The bot must not relax the historical sizing rules merely to create more trades.

## 3. Initial account-size experiment

Run the same strategy framework at:

- $2,000
- $5,000
- $10,000
- $25,000
- larger reference accounts where useful

The objective is to determine where the strategy becomes operationally feasible.

Do not interpret better performance at a larger account as evidence that the strategy itself is better. The experiment is primarily about constraint feasibility, diversification, and risk behavior.

## 4. $2,000 structure-selection hypothesis

For the $2,000 account, the first research pass should explicitly compare:

### A. Historical-mix model

Attempt to preserve the historical:

- VIX BP ceiling;
- 75% undefined / 25% defined allocation;
- 3–7% NLV undefined sizing;
- 1–3% NLV defined sizing;
- 15% single-underlying limit.

Record every infeasible trade rather than modifying the rules.

### B. Defined-risk feasibility model

Permit only defined-risk structures while preserving the other portfolio controls.

Candidate structures:

- vertical credit spreads;
- iron condors;
- iron butterflies where appropriate;
- other defined-risk premium structures supported by the finalized strategy universe.

This is an **experimental comparison**, not a claim that tastylive universally recommends this exact $2,000 configuration.

## 5. Why this matters

The historical framework can mathematically permit a $60–$140 undefined-risk trade in a $2,000 account, but that does not mean an actual option contract can satisfy the intended percentage allocation.

Contract granularity, broker BPR formulas, option liquidity, and assignment risk can make the theoretical sizing infeasible.

The system must distinguish:

**theoretical allocation**

from:

**actually executable contract size**.

## 6. Beta-weighted Delta limitation

Recent tastylive material reinforces that beta-weighted Delta is useful for standardizing portfolio directional exposure, but it is not sufficient by itself.

A 2025 tastylive discussion notes that low-correlation products can underestimate actual risk when correlations rise sharply during volatility spikes, and that gamma must also be monitored for changing exposure.

Therefore the project will **not** freeze a numerical beta-weighted-Delta neutrality band until the underlying study/data is recovered.

The risk engine will continue to treat beta-weighted Delta as one dimension alongside:

- gamma;
- BPR;
- BPR expansion;
- notional/unit exposure;
- correlation;
- maximum loss;
- stress scenarios.

## 7. Undefined-risk defense

Official tastylive material on strangles documents rolling the untested side as a defensive technique after the tested side is breached. A 2025 study also reports favorable historical results for rolling the untested side in its tested scenario.

This does **not** justify automatically coding "always roll the untested side."

Before implementation, compare at minimum:

1. close immediately;
2. hold;
3. roll untested side;
4. roll tested side;
5. roll entire position;
6. convert to defined risk where operationally possible.

Each must be tested with identical entry conditions and realistic execution assumptions.

## 8. Current research conclusion

The project should preserve the historical tastytrade framework as a documented benchmark while treating the $2,000 account as a separate feasibility experiment.

The research question is not:

> "How do we force the historical portfolio into $2,000?"

It is:

> "At what account size and under what structure constraints does the documented methodology become executable without silently violating its own risk controls?"

That distinction is now part of the research specification.


## 9. Feasibility-ledger specification

The feasibility experiment must use a portfolio ledger, not a trade-by-trade pass/fail calculation in isolation. A candidate can pass its entry checks while causing the aggregate portfolio to violate a limit.

For every candidate opportunity, record the following before/after values:

- timestamp and source-data version;
- account NLV, cash, available buying power and open positions;
- VIX allocation band and resulting aggregate BP ceiling;
- available undefined-risk and defined-risk sleeve capacity;
- requested structure, legs, quantity, expiration and underlying;
- theoretical per-trade sizing amount and integer contract quantity;
- broker-reported or explicitly modeled BPR;
- current and projected portfolio BPR;
- defined-risk maximum loss, where applicable;
- underlying concentration before and after the trade;
- beta-weighted Delta, gamma and notional exposure before and after;
- event, expiration and assignment checks;
- liquidity and estimated transaction costs;
- final acceptance/rejection and every reason code.

The ledger must retain rejected candidates. Otherwise a strategy that rarely finds a feasible trade could appear deceptively clean because its rejected opportunities disappear from the sample.

### 9.1 Sequential hard-gate evaluation

Apply hard gates in a deterministic order and preserve all failure reasons, not only the first one:

1. Account state valid; no emergency halt.
2. Position and order state reconciled; no duplicate or conflicting order.
3. Expiration, exercise, assignment and event restrictions pass.
4. Aggregate BP ceiling and applicable sleeve allocation pass.
5. NLV trade-size cap passes at integer contract quantity.
6. Single-underlying concentration cap passes.
7. Broker BPR and available buying power pass.
8. Defined-risk max-loss or undefined-risk stress constraints pass.
9. Portfolio directional, gamma, notional and correlation limits pass.
10. Quotes and estimated fills pass liquidity/cost checks.

AI opportunity ranking occurs only after hard gates. A high score cannot rescue a rejected trade.

### 9.2 Integer contract sizing

For each structure, calculate the maximum theoretical risk budget first, then determine whether any integer contract quantity satisfies every hard limit. Never round a fractional contract quantity up.

For a defined-risk spread, calculate maximum expiration loss from the actual legs and multiplier; do not use entry credit or BPR as a substitute. For a multi-leg structure, account for all legs and fees. For undefined-risk positions, the historical percentage sizing amount is not a maximum-loss bound; apply BPR and stress constraints separately.

A candidate with zero feasible contracts is a rejected opportunity, not a reason to widen the spread, increase the allocation, or substitute a different risk definition.

### 9.3 Required account-size outputs

For each tested account size, report:

- eligible opportunities and completed trades;
- accepted and rejected candidate counts;
- rejection counts by reason (including multiple reasons per candidate);
- fraction of eligible opportunities that could actually be entered;
- mean/median and percentile BPR as % of NLV;
- peak BPR and BPR expansion;
- number of concurrent positions;
- realized and unrealized P/L, fees, and ending NLV;
- drawdown and worst trade;
- defined-risk maximum-loss exposure;
- stress loss under named scenarios;
- time spent at or above each allocation/concentration boundary.

Show both the raw strategy result and the result after applying feasibility gates. Do not compare a one-contract unconstrained replay with a constrained account as if they were the same experiment.

### 9.4 Broker-data distinction

Keep three values separate in the data model:

1. **Research estimate:** locally calculated BPR or stress proxy, with formula and version.
2. **Broker preview:** buying-power effect returned for a specific proposed order, if the broker API supports it.
3. **Broker account state:** actual buying power and margin values reported for the paper account.

A locally calculated proxy must never be labeled as broker BPR. If historical broker previews are unavailable, disclose that the backtest is an approximation and run conservative sensitivity bands rather than claiming exact historical feasibility.

### 9.5 No-trade is a valid outcome

A strategy that cannot satisfy its documented constraints at $2,000 may produce few or no trades. That is a valid experimental result. The feasibility report must distinguish:

- strategy has no signal;
- signal exists but no listed contract meets the sizing limit;
- contract exists but BPR/capital prevents entry;
- risk limits reject the trade;
- market data or quote quality is insufficient.

This distinction is necessary to diagnose whether an account-size limitation is structural, data-related, or caused by the strategy's entry rules.
