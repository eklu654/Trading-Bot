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


## Focused CI after fixture correction — 2026-10-13 12:28Z

- Dedicated workflow run [38397435777](https://github.com/eklu654/Trading-Bot/actions/runs/38397435777) completed successfully after the fixture correction. Compile, 10 core emergency-exit tests, 19 ledger/latch tests, 16 executor tests, and the six latch-recorder tests all passed in the workflow's final step.
- Broad research run [38397435788](https://github.com/eklu654/Trading-Bot/actions/runs/38397435788) was still in progress at the time of this note; do not mark it passed until its final conclusion is checked.
- The scheduling race remains an independent, unresolved safety blocker. CI green does not prove monitor-first ordering, live market quote freshness, broker acceptance, fills, or end-to-end exit behavior. Submission gate remains false; PR remains draft.


## Re-run on latest branch head — 2026-10-13 12:29Z

- Latest focused workflow [38397527644](https://github.com/eklu654/Trading-Bot/actions/runs/38397527644) passed again on branch head `a3f466618f245ab702dffa57a908a726c7e4edef`; every step, including all core, ledger, executor, and recorder tests, is green.
- Broad research workflow [38397527759](https://github.com/eklu654/Trading-Bot/actions/runs/38397527759) remains in progress. Check its final result before closing the CI review.
- No code has been merged to `main`; PR #27 remains draft. Executor-side QQQ preflight, end-to-end paper order acceptance/fill evidence, and the market-open acceptance test remain required before enabling submission.


## Broad research CI disposition — 2026-10-13 12:30Z

- Broad research run [38397527759](https://github.com/eklu654/Trading-Bot/actions/runs/38397527759) was cancelled by a subsequent branch update; it did not pass or fail on test results. Do not cite it as successful.
- Dedicated focused emergency-exit run [38397527644](https://github.com/eklu654/Trading-Bot/actions/runs/38397527644) is green on the prior code head. The audit-only follow-up does not change tested runtime code.
- Runtime blocker remains unchanged: no executor-side live QQQ preflight yet; no broker order/fill acceptance evidence; keep PR draft and submission gate false.


## Executor-side QQQ preflight implementation — 2026-10-13 12:49Z

- Added `qqq_defense_preflight` to the paper executor. It reads broker market clock, recent QQQ daily bars and latest IEX trade, reuses the monitor's threshold/staleness evaluator, and fails closed on stale/malformed QQQ observations.
- When QQQ breaches -4.5%, the executor persists a per-portfolio latch before planning; the target is forced to zero while latched. Repeated breach observations update the post-trigger trough. Latch digest format now matches the monitor recorder's canonical identity.
- Added an independent QQQ check before planning and a **second check after broker context/price validation immediately before order payload/POST**. If either check sees an active latch/breach, or the final QQQ observation is stale, an unsubmitted buy intent is retired and no POST is attempted. Defensive sell path remains allowed when an existing latch is active and the QQQ feed is stale; normal buys fail closed.
- Expanded focused CI to compile the QQQ monitor and run its eight tests. Added tests for preflight breach activation, stale trade rejection, trough tracking, and a breach appearing specifically at the final pre-POST check.
- An intermediate focused run failed because older executor tests had not yet mocked the newly required preflight; the tests were adapted. Latest focused workflow [run 38399942594](https://github.com/eklu654/Trading-Bot/actions/runs/38399942594) passed before the final-check test was strengthened. A fresh focused run triggered by commit `f8a5cbbbacc37b071fbcee5f4dd29c06c6a248ed` must be checked before considering this work verified.
- Still no merge and no live order submission. Workflow submission gate remains false. The preflight narrows the monitor/executor scheduling race but is not a tick-by-tick guarantee: a fast market move can occur between the final quote and broker acceptance. Controlled market-open paper acceptance and broker order/fill evidence remain required.


## Open-buy cancellation and final verification — 2026-10-13 12:54Z

- Added a paper-endpoint-only DELETE helper and executor logic to cancel an existing nonterminal bot buy when a QQQ defense latch is active or a fresh preflight confirms a breach. It re-fetches by exact client order ID and reconciles fills/position before treating cancellation as terminal; unknown cancellation remains pending and is not treated as success.
- Fixed target evaluation in the submit path to apply the active latch, so a valid target-zero defensive sell is not rejected as inconsistent with the ordinary daily target.
- Added coverage for a breach arising at the final pre-POST check, allowing a defensive sell with a stale QQQ observation only when a latch is already active, and canceling/reconciling an existing open buy during defense.
- Focused workflow [run 38400569989](https://github.com/eklu654/Trading-Bot/actions/runs/38400569989) passed on commit `c11cfeec7102112854281661dee587e74552dd76`: 10 emergency-exit core tests, 19 ledger tests, 23 executor tests, 8 QQQ monitor tests, and 6 recorder tests. An earlier run failed only because the new test fixture contained a double-escaped newline; that fixture was corrected and the follow-up passed.
- Expanded the focused workflow to include `test_executor_fill_reconciliation.py` and to trigger when QQQ monitor source/tests change. This workflow change has its own new CI run pending.
- Safety status: the executor now performs independent preflight before planning and again directly before POST, and cancels detected open buys under defense. This reduces scheduler-order risk but cannot guarantee protection against a market move between the final quote and broker processing. The submission gate remains false, PR #27 remains draft, and no end-to-end broker order/fill acceptance has been demonstrated.


## Latest end-to-end CI and ledger snapshot — 2026-10-13 12:56Z

- Focused safety workflow [38400856114](https://github.com/eklu654/Trading-Bot/actions/runs/38400856114) passed on code head `26df715aaf7eb5b18743e799b798c4d6a6252336`: **70 tests total** — 10 emergency-exit core, 19 ledger, 24 executor (including preflight, final-check, cancel/reconcile, and identity-mismatch cases), 3 fill-reconciliation, 8 QQQ monitor, and 6 latch-recorder tests.
- Broad research workflow [38400856132](https://github.com/eklu654/Trading-Bot/actions/runs/38400856132) passed, including `pytest -q` and the TQQQ three-layer event-attribution step.
- Actual TQQQ partial-DMA matrix workflow [38400850188](https://github.com/eklu654/Trading-Bot/actions/runs/38400850188) also completed successfully. This is research validation, not broker acceptance.
- Current `paper-execution-ledger` snapshot: both B0 and F75 state files have $5,000 cash/equity, zero TQQQ quantity, no pending intent, and distinct stored account fingerprints. These are virtual ledger values; they do **not** prove current broker positions or a broker order/fill.
- The focused workflow now includes fill reconciliation and watches QQQ monitor source/tests in its PR path filters. PR #27 remains draft and unmerged; main's `ENABLE_PAPER_ORDER_SUBMISSION` remains false.
- Branch-protection review is still incomplete: repository rulesets API returned an empty list, while the classic branch-protection endpoint returned HTTP 403 (not accessible to the GitHub integration). Therefore I cannot confirm whether classic branch protection exists or whether Actions can push to the ledger branch under its protection settings.

## Current handoff — do not skip

1. Keep PR #27 draft; do not merge or enable paper submission yet.
2. Review branch protection / push permissions through an authorized repository settings view.
3. In a controlled market-open paper session, verify distinct broker accounts, actual open-buy cancellation under defense, order acceptance, fill activity reconciliation, broker-position match, durable state writes, both portfolios exiting to flat, and +10% recovery release.
4. Only after those checks should the submission gate be considered for a separate explicit release change. The current preflight is repeated but cannot eliminate a price move between final QQQ observation and broker processing.


## Cross-portfolio latch synchronization — 2026-10-13 13:02Z

- Found and fixed an additional race: the executor can persist a latch to one portfolio before the monitor's next poll. If QQQ rebounded before the monitor poll, the other portfolio could otherwise remain unlatch­ed and potentially stage a buy.
- Added `synchronize_latches_across_ledgers` to the executor and passed both state paths to prepare/submit calls. Any active latch is now propagated to both B0/F75 states before signal planning or order reconciliation, even with the submission gate false. If independently generated latch identities differ, B0's durable trigger identity is canonicalized across both ledgers and the lowest trough is retained. Recovery evidence is reset only when trigger identity/trough changes; repeated sync no longer clears valid recovery evidence.
- Updated the monitor recorder to propagate a one-sided latch even when the current QQQ observation has rebounded above -4.5%, using the existing trigger identity rather than creating a new one.
- Added tests for one-sided latch synchronization after rebound, cross-ledger trigger identity, trough merge, recovery-evidence preservation, broker order identity mismatch, open-buy cancellation, stale-feed defensive sells, and final pre-POST breach detection.
- Latest focused workflow [38401607086](https://github.com/eklu654/Trading-Bot/actions/runs/38401607086) passed **72 tests total**: 10 core, 19 ledger, 25 executor, 3 fill-reconciliation, 8 QQQ monitor, and 7 latch-recorder tests.
- Latest broad research workflow [38401607110](https://github.com/eklu654/Trading-Bot/actions/runs/38401607110) passed, including full `pytest -q` and TQQQ event attribution.
- Latest actual TQQQ partial-DMA matrix [38401603814](https://github.com/eklu654/Trading-Bot/actions/runs/38401603814) also passed.
- These are software/research checks. The paper-order submission gate is still false, PR #27 remains draft/unmerged, and no end-to-end broker order acceptance or fill has been demonstrated. Do not infer actual broker position from virtual ledger balances.
