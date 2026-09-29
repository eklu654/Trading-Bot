# Running findings — 2026-09-28

## Very brief status

- **ETF-001:** 200-DMA baseline beat the current VIX-filter variant in the corrected historical run; the current VIX filter is **not validated as a safety improvement**.
- **OPTIONS-001:** historical one-contract SPY replay produced positive aggregate P/L, but that result is **not account-valid** by itself; worst trades were roughly **-$2.1k**, already a major warning for a $2k account.
- **Defense test:** rolling the untested side reduced aggregate P/L in the corrected run and did not materially improve the worst observed trade; retain as a comparison, not a promoted rule.
- **Data/model audit:** an expiration-selection defect was found and corrected before relying on the latest options results.
- **Account feasibility:** a separate $2k NLV ledger now enforces modeled buying-power, stress-loss, concurrency, lifecycle, and mark-quality gates and records every rejection.
- **Risk accounting:** daily valuation snapshots now drive drawdown, BPR utilization, stress exposure, stale-mark, and BPR-expansion metrics.
- **Broker audit:** Alpaca performs its own options buying-power/eligibility checks; our modeled BPR is only a research estimate and must never be treated as broker approval.

## What is still unproven

The most important unanswered question is whether the historically generated OPTIONS-001 candidates produce a **sufficient number of feasible trades inside the $2,000 account** after all hard gates, and what the surviving account-level equity curve looks like.

- **0DTE free-data decision:** no paid historical dataset will be purchased. Free research will use public benchmark logs/code, free samples, legitimate free trials where available, expiry-only replay, synthetic sensitivity studies, and prospective data collection.
- **0DTE benchmark source found:** a public SPX 0DTE credit-spread repository provides source code and a trade log with 9:45 AM ET entries, VIX1D expected-move strike selection, $5 defined-risk wings, and expiration settlement. It is useful as an independent benchmark/control, but it is not raw historical OPRA quote data.
- **0DTE data conclusion:** the lack of free minute-by-minute historical option quotes does not block the project. It blocks only high-fidelity historical testing of path-dependent exits. Expiry-only defined-risk structures can still be researched with a separate evidence label.


We also still need runtime fail-closed protections, broker-state verification, order/fill reconciliation, restart recovery, duplicate-order prevention, and live/paper operational tests before trusting unattended execution.

## Current disposition

**Do not treat the bot as ready for unattended live money yet.** The research architecture is getting substantially stronger, but the account-constrained historical run and execution-safety validation are still required.
