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


## Validation update

- [Run #3](https://github.com/eklu654/Trading-Bot/actions/runs/38129886801) completed successfully: artifact download passed; Python compilation and three guardrail tests passed; canonical/fresh-data check completed; because the latest completed market session did not exceed the 2026-10-07 frozen cutoff, the monitor correctly reported “No new completed sessions; ledger unchanged” and did not fabricate a row.
- [Run #1](https://github.com/eklu654/Trading-Bot/actions/runs/38129869684) failed because its triggering commit preceded the test file and unittest discovery returned exit code 5 (“Ran 0 tests”). The test file was added, and the workflow was changed to execute it directly so missing tests cannot silently pass.
- [Run #4](https://github.com/eklu654/Trading-Bot/actions/runs/38129922083) is validating the direct-test command and final workflow revision. Confirm its final status before closing this implementation checkpoint.
- The successful no-new-session run verifies setup, frozen artifact retrieval, compilation, guardrails, and safe no-op behavior; it does **not** yet validate appending a real new session or committing a populated ledger. That requires a completed market session after the frozen cutoff.


## Execution timing correction

- Corrected first-run initialization so the $5,000 shadow account is initialized at the close of the first new market session with zero return credited for that initialization session. Subsequent sessions accrue overnight return on the previously held exposure, apply exposure-change cost at the open, and accrue intraday return on the newly executed exposure. This matches the preregistered close-to-next-open convention.
- The correction is in commit `09a6517c3e6c70f2689558808faf1ec26e3dfe6a`; [run #5](https://github.com/eklu654/Trading-Bot/actions/runs/38129970930) validates it.
- [Run #4](https://github.com/eklu654/Trading-Bot/actions/runs/38129922083) completed successfully after switching to explicit test execution. Its head predates the initialization correction; use run #5 for the latest code.


## Latest validation closed — run #5

- [Run #5](https://github.com/eklu654/Trading-Bot/actions/runs/38129970930) completed successfully on commit `09a6517c3e6c70f2689558808faf1ec26e3dfe6a`.
- Artifact download, compile, all three explicit guardrail tests, and shadow-monitor execution passed. The monitor safely found no completed session after the frozen 2026-10-07 cutoff and left the ledger unchanged. This is an expected Sunday no-op, not evidence of a forward-return result.
- The monitor is implemented and its no-new-session path is validated. Real forward-session append, cost/equity progression, and persistent ledger commit remain to be verified after the next completed market session.
- Schedule caveat remains: scheduled execution is not active while this workflow exists only on the research branch. The default-branch integration step is intentionally not performed here; no changes have been made to `main`.


## 2026-10-12 03:27 UTC — Alpaca paper account preflight

- Added default-branch workflow `.github/workflows/alpaca-paper-portfolio-preflight.yml` and execution readiness note `docs/03-execution/alpaca-paper-readiness-2026-10-12.md`.
- Credential check [38199438537](https://github.com/eklu654/Trading-Bot/actions/runs/38199438537) passed for B0 and F75. Follow-up read-only preflight [38199816562](https://github.com/eklu654/Trading-Bot/actions/runs/38199816562) also passed for both.
- Verified per account: ACTIVE, USD, not trading-blocked, not account-blocked, zero positions, zero open orders, valid broker clock timestamp; market was closed at the check time.
- Preflight only used GET requests and printed sanitized metadata. No order was submitted. Do not interpret the preflight as proof of an active strategy executor.
- Next implementation gate: frozen signal-to-target mapping, $5,000 virtual sleeve sizing independent of Alpaca's default account NLV, client-order-ID idempotency, broker reconciliation, and fail-closed data/session checks. B0 remains control; F75 remains frozen experimental overlay. Continue the prospective ledger in parallel; 252 return-bearing sessions is an efficacy-review gate, not a start gate for diagnostic paper tracking.


## 2026-10-12 03:30 UTC — B0/F75 execution contract recorded

- Added [B0/F75 Paper Execution Contract](https://github.com/eklu654/Trading-Bot/blob/research/qqq-slow-bear-audit/docs/research/B0_F75_PAPER_EXECUTION_CONTRACT_2026-10-12.md), commit `10497e8e4970a785c6dc0bc04d6f75e19b1e3503`.
- Frozen contract: TQQQ long/flat; $5,000 virtual sleeve per account; B0 uses its binary signal; F75 remains capped by B0 eligibility and targets 75% while the tightening overlay is active or 100% otherwise.
- The active-tightening implementation confirms its state is 0 when the sticky defensive condition is armed (QQQ below its 200-session SMA with lagged Fed state TIGHTENING_ACTIVE), and 1 when not armed; F75 applies 75% to the baseline while state 0. The overlay exits on QQQ reclaiming the 200-session SMA.
- Contract lists fresh-signal, close-to-next-session timing, paper-only endpoint, broker reconciliation, fixed-sleeve sizing, idempotency, durable ledger and fault-test requirements. It does not claim any orders have been submitted.
- Paper-order execution remains gated on implementing the actual broker adapter and fresh signal feed; diagnostic tracking and the 252-session prospective research continue in parallel.


## 2026-10-12 03:31 UTC — scheduler branch-placement correction

- Correction to the older schedule caveat above: the default branch currently contains `.github/workflows/f75-shadow-scheduler.yml`, which schedules a monitor run at 22:35 UTC on weekdays and checks out `research/qqq-slow-bear-audit` before executing the monitor. Therefore the default-branch scheduling wrapper is present; the old statement that the schedule is not active until the workflow is copied/merged is stale.
- The most recent validated monitor run remains [38195586167](https://github.com/eklu654/Trading-Bot/actions/runs/38195586167), which passed all 32 tests and verified ledger integrity, but was a no-op because no new completed session was eligible. The next scheduled opportunity is 2026-10-12 at 22:35 UTC; the monitor intentionally excludes the current New York calendar date, so do not expect a same-day row from that run.
- Continue to verify the actual scheduled run's conclusion and logs rather than assuming that the presence of a schedule proves successful execution.
