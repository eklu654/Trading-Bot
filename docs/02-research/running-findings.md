# Running findings — 2026-09-28

## Very brief status

- **0DTE chronological validation:** the 16D/6D iron condor 15:55 control was -3.98% in 2022–2024, +10.30% in 2025, and +7.69% in the 2026 holdout. The adjacent 15:00 version was -4.37%, -1.09%, and +12.96%. This confirms strong time/regime dependence; the full-sample +14.01% result is not an unconditional edge.

- **0DTE timing matrix:** 45 frozen 0DTESPX configurations completed across 1,012 sessions. The 16D/6D iron condor was positive only at the two latest exits; the 15:55 cell reproduced the earlier +14.01% result. This is an in-sample control, not a deployment selection.

- **ETF-001:** 200-DMA baseline beat the current VIX-filter variant in the corrected historical run; the current VIX filter is **not validated as a safety improvement**.
- **OPTIONS-001:** historical one-contract SPY replay produced positive aggregate P/L, but that result is **not account-valid** by itself; worst trades were roughly **-$2.1k**, already a major warning for a $2k account.
- **Defense test:** rolling the untested side reduced aggregate P/L in the corrected run and did not materially improve the worst observed trade; retain as a comparison, not a promoted rule.
- **Data/model audit:** an expiration-selection defect was found and corrected before relying on the latest options results.
- **Account feasibility:** a separate $2k NLV ledger now enforces modeled buying-power, stress-loss, concurrency, lifecycle, and mark-quality gates and records every rejection.
- **Risk accounting:** daily valuation snapshots now drive drawdown, BPR utilization, stress exposure, stale-mark, and BPR-expansion metrics.
- **Broker audit:** Alpaca performs its own options buying-power/eligibility checks; our modeled BPR is only a research estimate and must never be treated as broker approval.

- **Replay integrity fix (2026-09-29):** OPTIONS-001 and OPTIONS-002 now explicitly prevent duplicate same-day entries and overlapping positions in the sequential trade replay. This closes a bookkeeping issue that could otherwise inflate trade counts/P&L before account feasibility is applied.
- **$5,000 options challenger:** OPTIONS-002 is now implemented as a defined-risk 45-DTE SPY iron condor with ~16-delta short strikes, 2-point wings, 50%/21-DTE management, and separate $5k 3%/5%/7% risk-band feasibility tests. The historical run is currently executing; no performance conclusion has been accepted yet.
- **Validation discipline:** the first CI test pass exposed a missing DuckDB dev dependency and then a package-import issue; both were corrected before accepting research output. This is a useful guard against treating an unvalidated implementation as a result.

## What is still unproven

The most important unanswered question is whether the historically generated OPTIONS-001 candidates produce a **sufficient number of feasible trades inside the $2,000 account** after all hard gates, and what the surviving account-level equity curve looks like.

- **0DTE free-data decision:** no paid historical dataset will be purchased. Free research will use public benchmark logs/code, free samples, legitimate free trials where available, expiry-only replay, synthetic sensitivity studies, and prospective data collection.
- **0DTE benchmark source found:** a public SPX 0DTE credit-spread repository provides source code and a trade log with 9:45 AM ET entries, VIX1D expected-move strike selection, $5 defined-risk wings, and expiration settlement. It is useful as an independent benchmark/control, but it is not raw historical OPRA quote data.
- **0DTE data conclusion:** the lack of free minute-by-minute historical option quotes does not block the project. It blocks only high-fidelity historical testing of path-dependent exits. Expiry-only defined-risk structures can still be researched with a separate evidence label.


We also still need runtime fail-closed protections, broker-state verification, order/fill reconciliation, restart recovery, duplicate-order prevention, and live/paper operational tests before trusting unattended execution.

## Current disposition

**Do not treat the bot as ready for unattended live money yet.** The research architecture is getting substantially stronger, but the account-constrained historical run and execution-safety validation are still required.
