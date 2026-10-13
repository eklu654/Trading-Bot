# Emergency-exit integration branch — 2026-10-13

Branch: `ops/emergency-exit-integration-2026-10-13`

## Changes made on this branch

- Added `emergency_exit_latch` to the virtual portfolio ledger schema and validation.
- Added `activate_emergency_exit_latch`: accepts only a QQQ price at or below 95.5% of the prior close, stores a SHA-256 trigger identity, and never replaces an already-active latch.
- Added `update_emergency_exit_latch` to track the lowest QQQ price after the trigger and calculate the re-entry threshold at 110% of that trough.
- Added `release_emergency_exit_latches`, which only clears both B0 and F75 latches when both ledgers have zero shares, neither has a pending order, and QQQ has recovered at least 10% from the tracked trough.
- Added `research/record_emergency_exit_latch.py` to validate fresh monitor reports, persist the latch to both shared ledger files, track troughs, and record recovery. It never calls a trading endpoint or submits orders.
- Updated the executor to override its daily target to zero while a durable latch is active. It continues using the existing two-phase paper executor and fill reconciliation rather than adding a second order-submission implementation.
- Changed the monitor and executor workflow concurrency group to `paper-broker-mutations` so they cannot race while writing the shared `paper-execution-ledger` branch.
- Updated the monitor workflow to persist trigger/recovery state to `paper-execution-ledger`. Broker submission remains controlled by the existing `ENABLE_PAPER_ORDER_SUBMISSION=false` release gate.

## Test and review status

- Added latch validation tests to `research/test_paper_virtual_portfolio.py`.
- Added `research/test_record_emergency_exit_latch.py` for fresh-report checks, idempotent activation, trough tracking, +10% recovery, and requiring both portfolios to be flat before release.
- Added executor target-override tests for B0 and F75.
- **Do not merge or enable this integration yet.** The final edit to the recovery test did not apply, leaving a known test-fixture mismatch: the recovery test updates QQQ price to 99 but must also set the report status to `MONITORING` and `threshold_breached=false`. The production validator correctly rejects a report whose status/flag contradicts its prices.
- This branch has not yet passed CI. Review workflow YAML, test results, shared-branch push permissions, and concurrency behavior before merging.
- No paper order has been submitted by this branch. No end-to-end broker acceptance has been established.

## Important operational rule

Keep the executor submission gate false until this branch's tests pass and a controlled, market-open paper acceptance test confirms both B0 and F75 account identities, order acceptance, fill reconciliation, durable ledger updates, emergency exits, and the +10% recovery gate.


## CI findings — 2026-10-13 12:19Z

- Focused integration run [38396353369](https://github.com/eklu654/Trading-Bot/actions/runs/38396353369) compiled the new modules and passed the 10 core emergency-exit tests plus 19 ledger tests, then found 3 failures in the new latch recorder tests.
- Fixed two production/test-contract issues in commit `5bb876bb37aff4733e8f57bf31721c97aa1e867f`: stale report errors are now preserved as stale rather than rewritten as malformed timestamp errors, and the recorder returns the original `trigger_sha256` for idempotence/audit checks.
- One test fixture remains incorrect: the +10% recovery test changes QQQ to 99/100 but retains the prior `THRESHOLD_BREACHED` status and `threshold_breached=true`. The production validator correctly rejects that contradiction. The attempted fixture correction was blocked; do not work around the validator. This branch remains draft/unmergeable until that test is corrected and the full focused workflow passes.
- The monitor workflow now commits state changes whenever `latch_changed=true`, not only when a latch is first activated, so trough updates and eventual recovery release are also durable.


## Latest focused CI result — 2026-10-13 12:20Z

- [Focused integration run 38396537435](https://github.com/eklu654/Trading-Bot/actions/runs/38396537435) compiled all modules; passed **10/10** core tests, **19/19** ledger tests, and **16/16** executor tests. The latch recorder suite passed 5/6 tests.
- The only remaining failure is `test_trough_moves_down_and_recovery_releases_both_flat_ledgers`: after the test sets QQQ to 99/100, it leaves the report marked as a -4.5% breach. The production validator correctly fails closed on that contradiction.
- This PR remains draft and must not be merged until the recovery test reports `status="MONITORING"` and `threshold_breached=false` for the 99/100 observation, the focused suite is green, and workflow branch-write behavior is reviewed.


## Additional pre-merge race found — 2026-10-13 12:21Z

- The monitor and executor share a concurrency group, which serializes ledger writes, but it does **not** guarantee the monitor runs first when both five-minute schedules are due together. If the executor acquires the lock first, it could stage an ordinary buy from the prior daily signal before the monitor writes the QQQ latch.
- Before merging, add an independent QQQ -4.5% preflight in the executor's buy path (or an equally strong ordering/permit design) so an active intraday breach prevents buys even if the monitor run is queued behind the executor. This branch is not yet sufficient to guarantee "no buy during a triggered defense" under scheduler ordering.
- Do not enable paper submission or merge this branch until this race is addressed, the one remaining test fixture is corrected, and all focused tests pass.


## Fixture correction — 2026-10-13 12:27Z

- Corrected the +10% recovery test fixture so its 99/100 QQQ observation is consistently marked `status="MONITORING"` and `threshold_breached=false`; the production price/status validator remains unchanged.
- This edit only repairs test data. It does not resolve the executor/monitor scheduling race, establish broker order acceptance, or authorize merging/enabling submissions.
