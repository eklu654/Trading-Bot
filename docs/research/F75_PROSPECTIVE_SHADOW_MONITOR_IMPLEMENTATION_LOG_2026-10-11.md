# F75 Prospective Shadow Monitor — Implementation Log — 2026-10-11

## Preregistered decision boundary

- Historical canonical Fed-DMA replay: Actions run #15, successful; all 4,189 B0 signals match the frozen input, zero-cost equity difference < $0.000001.
- F75 remains research-only. Historical 2022–2024 concentration warning stands. No parameter search or trading authorization.
- Preregistration: `F75_PROSPECTIVE_SHADOW_EVALUATION_PREREGISTRATION_2026-10-11.md`.

## Implementation added

- `research/f75_prospective_shadow_monitor.py`: read-only monitor, no broker APIs or order submission. Verifies canonical input SHA-256 `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`, combines frozen history with fresh QQQ/TQQQ sessions, independently reconstructs and reconciles B0, uses the existing one-session-lagged Fed lifecycle mapper and frozen F75 overlay, and appends new dates to a persistent ledger.
- `research/test_f75_prospective_shadow_monitor.py`: three guardrails for exact B0 match and fail-closed mismatch/length behavior.
- `.github/workflows/f75-prospective-shadow-monitor.yml`: dependency install, canonical artifact retrieval, compilation/tests, daily shadow update, and commit of ledger/state to the research branch. Workflow is scheduled for 22:35 UTC weekdays and has no order-execution steps.
- Ledger targets: `data/research/f75_shadow_daily_ledger.csv`; state/hash record: `data/research/f75_shadow_state.json`. The first run may legitimately report no new sessions because the frozen cutoff is 2026-10-07 and the current date is Sunday, 2026-10-11.

## Validation runs

- Run #1: [38129869684](https://github.com/eklu654/Trading-Bot/actions/runs/38129869684) was created from the first workflow commit before the test file was committed; treat it as an initial wiring check only.
- Run #2: [38129880953](https://github.com/eklu654/Trading-Bot/actions/runs/38129880953) covers the updated monitor and guardrails. Record final outcome and any corrections below once complete.
- Important platform boundary: GitHub scheduled workflows are activated from the repository's default branch. This workflow currently lives on `research/qqq-slow-bear-audit`; its push-triggered validation can run there, but weekday schedule is **not active until the workflow is merged/copied to the default branch**. Do not claim automated daily observation has begun before that branch-placement issue is resolved.

## Correctness notes / remaining verification

- Historical B0 is checked against the immutable source before any new rows are accepted; duplicate dates, missing columns, non-finite values, source hash mismatch, and signal mismatches fail closed.
- Existing ledger rows are preserved and new rows must be strictly later than the prior ledger tail.
- After first successful run, verify the artifact download, test step, live-data step, and ledger commit behavior in the Actions logs. Inspect the resulting ledger and state JSON before treating the monitor as validated.
- Do not use prospective results to tune thresholds. At 252 return-bearing sessions, publish a full-path review and separate operational/risk review before considering any paper-trading proposal.
