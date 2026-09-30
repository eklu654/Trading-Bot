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

### 2026-09-29 — OPTIONS-002 2-point wings reclassified as feasibility probe

The initial defined-risk OPTIONS-002 replay uses 45 DTE, ~16-delta shorts, and 2-point SPY wings. This is useful for testing whether a very small defined-risk structure can fit a $5,000 account, but it is not an adequate stand-in for the wider iron-condor constructions studied by tastylive. Current tastylive research covers 45-DTE SPY iron condors with $5/$10/$20 wings and separately reports weaker historical behavior for $1–$2-wide iron condors than wider structures. The next options pass therefore needs methodology-aligned wider-wing candidates before any ETF-vs-options conclusion is made.

The existing 2-point OPTIONS-002 run should still be completed because it answers the narrow capital-feasibility question. If it performs poorly, that result should not be generalized to all tastytrade-informed defined-risk options. Planned next candidates: 20-delta/$5-wide, 20-delta/$10-wide, and dynamic 20/10-delta SPY iron condors, all under identical $5,000 feasibility, conservative/mid fill, 50% profit, and 21-DTE controls.

### 2026-09-30 — Historical Research run #150 completed

The full Historical Research workflow completed successfully. The OPTIONS-002 2-point-wing replay was the longest stage, but it completed successfully rather than hanging.

The six base OPTIONS-002 replays produced these **raw trade-level** results over the available option-chain history:

| Candidate | Fill | Trades | Total P/L | Win rate | Worst trade |
|---|---|---:|---:|---:|---:|
| ALL_DAYS | conservative | 246 | +$209 | 63.8% | -$151 |
| ALL_DAYS | mid | 240 | +$263 | 63.8% | -$147 |
| BROAD_SIDEWAYS | conservative | 96 | +$641 | 63.5% | -$138 |
| BROAD_SIDEWAYS | mid | 90 | +$811 | 70.0% | -$135 |
| TURBULENT_ONLY | conservative | 58 | +$512 | 62.1% | -$83 |
| TURBULENT_ONLY | mid | 55 | +$492 | 69.1% | -$222 |

These are **not deployment results**. They are full-history replay results before the account-level capital ladder and chronological OOS discipline are applied.

The chronological split gives a more important picture:

- ALL_DAYS/conservative: train -$62, validation +$263, holdout +$8.
- ALL_DAYS/mid: train +$330, validation +$99, holdout -$166.
- BROAD_SIDEWAYS/conservative: train -$60, validation +$425, holdout +$276.
- BROAD_SIDEWAYS/mid: train +$357, validation +$295, holdout +$159.
- TURBULENT_ONLY/conservative: train -$68, validation +$417, holdout +$163.
- TURBULENT_ONLY/mid: train +$194, validation +$239, holdout +$59.

The chronological results are encouraging enough to justify deeper research into regime-conditioned defined-risk options, but the small number of trades in several splits and the fact that this 2-point-wing construction is only a feasibility probe mean **no promotion decision is made**.

The capital ladder also exposed an important implementation constraint: the 2-point-wing structure is frequently infeasible at low NLV, and simply raising the risk percentage does not reliably solve that problem. For example, ALL_DAYS at $2,000 accepted only 0–4 trades across the tested 3%–7% risk bands, while at $5,000 it accepted substantially more trades but still finished below starting NLV across all tested fill/risk combinations. By contrast, regime-filtered capital tests can show positive small-account outcomes in some configurations. This supports treating capital and market regime as separate dimensions rather than using account size alone as a strategy selector.

The current evidence therefore supports this research direction:

1. Keep ETF-001 and defined-risk options as separate candidates.
2. Do not promote the 2-point OPTIONS-002 structure as the mature options strategy.
3. Build the planned wider-wing, methodology-aligned options candidates.
4. Evaluate those candidates chronologically before any regime-selector training.
5. Treat $2k–$5k feasibility as a capital-regime problem, not as proof that the mature strategy itself is invalid.
6. Preserve the final holdout from strategy selection.

### Current disposition after run #150

**The bot remains research-only.** Run #150 materially advances the evidence base, but it does not satisfy the promotion gates for unattended live trading. The next highest-value work is wider-wing OPTIONS-002 variants plus a formal chronological/regime comparison that evaluates the strategy and the regime selector separately.
