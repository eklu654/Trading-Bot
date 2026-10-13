# Adaptive LEAPS Research — Status and Next Actions

**Updated:** 2026-10-13  
**Scope:** Frozen adaptive long-call LEAPS baseline for SPY and QQQ; conditional short-call overlay remains a later, separate experiment.

## Verified repository state

- Source data is pinned to `anahatsingh-ui/options-dataset-hist` commit `37f6c456fe1a4775c875673fb8ef907d5cd2fd66`.
- Coverage research previously recorded: duplicate keys = 0; positive underlying joins = 100%; 270-DTE candidate availability SPY 99.98%, QQQ 99.84%. These are coverage findings, not strategy-performance findings.
- Frozen selection: target 270 DTE, target absolute delta 0.80; eligible DTE window 225–315; calls only; absolute delta 0.60–0.95; valid positive bid and mark; ask >= bid; volume or open interest positive.
- Replay code currently uses close-observation signals and next available observation execution; buys at ask and sells at bid; exits when observed DTE <= 30; logs missing/invalid entries and exits; supports a $5,000 cash-enforced mode.
- Replay workflow defines four outputs: SPY theoretical one-contract, SPY cash-constrained at $5,000, QQQ theoretical one-contract, and QQQ cash-constrained at $5,000. It uploads daily ledgers, transactions, summaries, and source hashes as `adaptive-leaps-chronological-replay`.
- The replay and unit-test workflow files exist on `main`. The replay workflow has a 45-minute job timeout; unit tests have a 5-minute timeout.

## Important distinction

The code and workflow definitions are present, but this audit did **not** independently verify a completed chronological replay run or inspect its generated artifacts. Therefore there is still no validated historical P/L conclusion and no paper-trading approval from this research.

## Next actions — in order

1. Inspect the latest Adaptive LEAPS Unit Tests and Data Coverage Audit workflow runs; capture run IDs, conclusions, and artifact links.
2. Inspect the latest Adaptive LEAPS Chronological Replay run. Confirm all four replay commands completed and the artifact upload succeeded.
3. Download and reconcile each `summary.json`, `daily_ledger.csv`, and `transactions.csv`:
   - observation dates and source period;
   - starting cash + transaction cash flows = final cash;
   - no same-observation fills;
   - buys use ask, sells use bid;
   - rejected orders are counted and explained;
   - terminal open positions have a valid bid mark, otherwise terminal equity stays unavailable;
   - the $5,000 constrained runs never spend more cash than available.
4. Report SPY vs QQQ separately. Include final equity, return, max drawdown, time invested, completed trades, rejected orders, and periods with missing marks. Do not conflate theoretical one-contract results with feasible $5,000 results.
5. Only after reconciliation passes, freeze the long-call baseline and add the conditional short-call overlay as a separately attributable experiment. Preserve the rebound rule: close the short call on unwind; do not automatically re-enter; require a fresh risk activation.
6. No paper trading until the historical outputs are reproducible and reviewed.

## Workflow references

- [Adaptive LEAPS Unit Tests](../.github/workflows/adaptive-leaps-unit-tests.yml)
- [Adaptive LEAPS Data Coverage Audit](../.github/workflows/adaptive-leaps-data-coverage.yml)
- [Adaptive LEAPS Chronological Replay](../.github/workflows/adaptive-leaps-replay.yml)
- [Lifecycle primitives](../research/adaptive_leaps_lifecycle.py)
- [Replay engine](../research/adaptive_leaps_replay.py)
- [Replay runner](../research/run_adaptive_leaps_replay.py)

## Audit note

This document records repository/code inspection only. It does not assert that a workflow run succeeded or that the strategy is profitable. Update this file with actual run IDs, artifact names, reconciliation results, and any defects found after reviewing the generated outputs.
