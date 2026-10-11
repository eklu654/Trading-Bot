# B0 vs F75 Mechanism Repeatability Audit Log

## 2026-10-11 — protocol and execution notes

- Research branch: `research/qqq-slow-bear-audit`.
- Research question: test whether frozen F75 repeatedly improves bear-market survival without materially impairing recovery participation; do not optimize thresholds.
- Controls: B0 is the canonical control; F75 remains frozen and shadow-only.
- Preregistered episode windows: dot-com 2000–2002, GFC 2007–2009, 2011 stress, 2015–2016 stress, 2018 selloff, COVID-19 2020, and Fed tightening 2022–2024.
- Pre-inception TQQQ periods must be labeled unavailable; no synthetic TQQQ proxy may be represented as actual TQQQ history.
- First workflow attempt (run 38131362335) failed at guardrails because `pytest` was absent from the runner environment; canonical artifact download and dependency installation succeeded.
- Run 38131400138 then exposed the next guardrail defect: pytest collection could not resolve the existing sibling import `f75_prospective_shadow_monitor` when tests imported the script as `research.b0_f75_mechanism_repeatability`. No attribution ran.
- Workflow dependency correction committed as `91c7257542f937c4db2110276d37895ace5b3f4d`: guardrail step installs declared `requirements-dev.txt`, which includes pytest.
- Run [38131502311](https://github.com/eklu654/Trading-Bot/actions/runs/38131502311) was in progress at last check; it predates the PYTHONPATH correction and may reproduce the import failure. Workflow fix committed as `ee10163d9dc43d94aa6bb7797ded890ec9d1fdd8`; verify the next run. No attribution results are validated yet.
- Do not promote F75 based on aggregate terminal balance alone. Review episode win counts, drawdown changes, recovery exposure at 20/60 sessions, transaction-cost sensitivity, and input/signal reconciliation.
- Important implementation caveat to audit in the next pass: confirm episode return windows and recovery horizons are aligned to the intended next-open execution convention, and that each episode's equity normalization is documented clearly.

## Next actions

1. Inspect run 38131502311 steps and logs; fix the first genuine code/data defect.
2. Run the attribution and retrieve its CSV/JSON artifacts.
3. Independently reconcile representative episode calculations against canonical daily rows.
4. Add validated findings and explicit limitations here before any promotion decision.

## 2026-10-11 — first successful run and methodological corrections

- Run [38131526416](https://github.com/eklu654/Trading-Bot/actions/runs/38131526416) passed all workflow steps; 4 original guardrail tests passed, canonical SHA-256 matched, and the CSV/JSON artifact uploaded (artifact ID `11699346208`).
- Initial uncorrected summary reported 5 measured episodes, 2 unavailable, 2 F75 return wins at 25 bp, 3 drawdown improvements, and zero median incremental return. These results are **superseded and must not be used**: inspection of the CSV and code found episode-accounting defects.
- Defect A: episode return divided terminal equity by the equity after the first episode session, excluding that first session's return even though terminal equity included it.
- Defect B: each episode simulation reset prior exposure to cash, distorting the first session's overnight return and opening rebalance cost versus the actual strategy state entering the episode.
- Defect C: recovery participation used close signals rather than lagged realized exposure and included the trough session, not exactly the next 20/60 sessions.
- Fixes committed:
  - `ac7ab61988a1f3855d717a88391f7d84483411b8`: first-session return baseline and realized recovery exposure.
  - `a6115b35582d46db2ecae2d1764ad218e0e48ead` and `aa214e6da557d1c9afd65864bf8edad06f5e66b1`: simulate full actual-TQQQ history to preserve pre-episode exposure; normalize each episode at the prior close to $5,000 and retain that baseline for drawdown.
  - `b26d0295dcf5fbbcfaabcffc22522b37318c0c2f` and `4abd1492d915bb24e8a67226de11eedf62076ce1`: add/update regression tests for episode path normalization and drawdown boundaries.
- Runs triggered by intermediate commits were cancelled by later commits before completing; the latest run [38131928120](https://github.com/eklu654/Trading-Bot/actions/runs/38131928120) is queued against the test-updated code.
- Do not cite the original episode metrics as valid. Await a successful run against the corrected accounting, then inspect the new artifact and independently reconcile calculations.

## 2026-10-11 — corrected accounting run completed

- Corrected run [38131928120](https://github.com/eklu654/Trading-Bot/actions/runs/38131928120) succeeded against commit `4abd1492d915bb24e8a67226de11eedf62076ce1`; guardrails and attribution completed and artifact ID `11698384838` was uploaded.
- Corrected CSV/JSON inspected locally. It now uses the full actual-TQQQ history to preserve prior exposure state, normalizes the prior-close episode equity to $5,000, includes the first episode session in return, and uses lagged realized exposure for the next 20/60 sessions after the low.
- Corrected 25 bp episode results:
  - 2011 stress: B0 and F75 identical; return -15.20%, max drawdown -40.07%.
  - 2015–2016 stress: F75 return -20.38% vs B0 -20.11% (slightly worse after costs), but max drawdown improves from -43.45% to -34.17%; normalized terminal equity is about $13.36 lower.
  - 2018 selloff: F75 return -29.47% vs B0 -29.51%, a very small improvement (~$1.93 on a $5,000 episode baseline); max drawdown improves by only ~0.04 percentage points.
  - COVID 2020: B0 and F75 identical; return +111.78%, max drawdown -47.27%.
  - 2022–2024: F75 return +78.06% vs B0 +40.92%; max drawdown improves from -72.88% to -53.42%; normalized terminal equity improves by about $1,857 after 25 bp modeled costs.
- Across the five measured episodes, F75 has 2 positive return differences at 25 bp, 3 drawdown improvements, and median incremental return approximately zero. The net return advantage remains highly concentrated in 2022–2024. There is evidence of drawdown improvement in 2015–2016, but the candidate's extra turnover gives back the small 25 bp terminal-return benefit there.
- Interpretation: **mixed evidence, not enough to promote**. The defense mechanism can reduce episode drawdown in multiple episodes, but repeatable net return improvement is not established and COVID/2011 show no difference. Continue F75 shadow-only and frozen.
- Artifact digest: `sha256:f716942a868ff5f27039f3e8b17b2d312e55cf30ea04b2d041459ec185e97b54`.
- Follow-up required: add an episode-level independent reconciliation that asserts terminal equity = $5,000 × (1 + episode return), checks all reported incremental fields, and validates that exposure horizons contain exactly 20/60 post-trough sessions when available. Then run a separate full-period compounded comparison; episode normalization is not a substitute for full-period portfolio accounting.

- Additional hardening committed after the corrected run: `bb70e91ec070e84e1e5d9b01cb325a2e6e421427` adds fail-closed checks for return/terminal-equity identity, incremental return/equity/drawdown identities, and exact post-trough recovery sample counts; `78c2ca827ed582b0528136e7d5026d060dad5f88` adds a regression test that verifies inconsistent terminal equity is rejected. Await the resulting workflow before considering the hardening validated.

- Run [38132031780](https://github.com/eklu654/Trading-Bot/actions/runs/38132031780) passed with fail-closed report reconciliation enabled; `episodes_accounting_validated=5`, confirming all five measured episode rows satisfy return/terminal-equity and incremental-metric identities. Artifact ID `11699711470`; digest `sha256:8e6b1a1763c4dd845ec56841aad2bfcb255475948b6afc1a310c6d3cf448f51e`.
- A further regression test was committed at `78c2ca827ed582b0528136e7d5026d060dad5f88` to prove the validator rejects inconsistent terminal equity. Workflow run [38132039628](https://github.com/eklu654/Trading-Bot/actions/runs/38132039628) is the validation of that final test commit; await its result before declaring the latest branch head green.

## Next audit extension — full-period compounded comparison

- Added `_full_period_comparison` to compute B0 and frozen F75 compounded terminal equity, total return, max drawdown, average realized exposure, defensive sessions, and incremental differences at 0/25/50 bp costs over the full actual-TQQQ history.
- The output is `data/research/b0_f75_full_period_compounded.csv`; the JSON summary includes the rows, date bounds, and session count. The workflow uploads this file alongside episode attribution.
- Added a synthetic regression test for return/terminal consistency and cost sensitivity.
- Commits: `7dae2bc711b783fe9a5b75f42053926735cde163` (full-period metrics), `a9837231f34b00a4cfe8d61628ba49ef464c7080` (artifact upload), `d72256b0b66d778ddad4aba5507eb371e231e222` (test).
- These full-period figures must be checked against previously reported B0/F75 balances before interpretation; if they differ, reconcile execution timing, start/end dates, and cost conventions rather than silently choosing one result.

## 2026-10-11 — candidate definition mismatch found; full-exit results invalidated

- The full-period audit initially produced a misleading F75 result because the audit script composed `f75 = min(B0, overlay_state)`, treating the active overlay state of 0 as a full cash exit.
- The existing frozen chronological robustness implementation defines F75 differently: `overlay_weight = where(overlay_state == 0, 0.75, 1.0)`, then `F75 = min(B0, overlay_weight)`. Therefore F75 holds 75% exposure during active overlay states unless B0 independently requires 0%. F50 analogously uses 50%.
- This mismatch explains why B0's 25 bp terminal balance exactly matched $3,852,657 while the initial full-exit F75 replay incorrectly returned $3,383,559 instead of the earlier approximately $3,898,853.
- The full-exit episode and full-period metrics are invalid for evaluating F75 and are superseded. Do not use them for promotion or strategy judgment.
- Corrected composition committed as `d02948a478349e93801a4a4a8170344e0730e951`; regression test committed as `f898425f306ec7a00e7181d0df22f062cd7f5fd2`.
- New workflow run will recompute all episode and full-period metrics with the true frozen F75 75% overlay. Reconcile the resulting 25 bp full-period terminal equity and max drawdown against the prior robustness report before accepting the comparison.

## 2026-10-11 — frozen F75 exposure restored; canonical full-period figures reconcile

- The corrected partial-exposure run [38132232294](https://github.com/eklu654/Trading-Bot/actions/runs/38132232294) completed successfully with 5/5 episode accounting validations and uploaded artifact `11698769710` (SHA-256 `a7495abadfcd706f5e7e7263e4367d6f545f978b263d712ce430d4b55bae6c94`).
- Full-period 25 bp result now matches the previously recorded F75 result exactly to displayed precision: B0 $3,852,657.34; F75 $3,898,852.68; F75 incremental terminal equity +$46,195.34; B0 max DD -73.7979%; F75 max DD -67.9938%.
- Full-period cost sensitivity (B0 / F75 terminal equity):
  - 0 bp: $4,040,315 / $4,124,681 (F75 +$84,366); max DD -73.53% / -67.65%.
  - 25 bp: $3,852,657 / $3,898,853 (F75 +$46,195); max DD -73.80% / -67.99%.
  - 50 bp: $3,673,277 / $3,684,972 (F75 +$11,695); max DD -74.06% / -68.33%.
- Corrected episode summary at 25 bp: 3/5 measured episodes show positive F75 return difference; 3/5 show improved maximum drawdown; median incremental episode return is +0.00010498 (about +0.0105 percentage points), median incremental episode equity +$0.52 on normalized $5,000.
- Episode detail: 2015–2016 F75 is +0.77 percentage points vs B0 and reduces max DD from -43.45% to -38.43%; 2018 difference is negligible; 2022–2024 F75 return +54.20% vs +40.92% and DD -66.87% vs -72.88%; 2011 and COVID are unchanged.
- These results supersede all full-exit candidate results and the prior 2-win/zero-median summary. The frozen F75 definition is 75% exposure when the tightening overlay is active, capped by B0's independent defense.
- A final guardrail test for the 75% partial-exposure composition was added in commit `f898425f306ec7a00e7181d0df22f062cd7f5fd2`; run [38132237766](https://github.com/eklu654/Trading-Bot/actions/runs/38132237766) must pass before calling the current branch head green.

- Final regression run [38132237766](https://github.com/eklu654/Trading-Bot/actions/runs/38132237766) passed on the code containing the F75 75%-exposure regression test. All accounting guardrails and artifact upload succeeded; latest artifact ID `11698829610`, digest `sha256:ec034e1ce9267367a06b094ab5090d824b2adf9ccfda40293deb6264c26f8ebb`.
- Full-period reconciliation is now confirmed: B0/F75 terminal balances at 25 bp are $3,852,657.24 / $3,898,852.58; max drawdowns -73.7979% / -67.9938%. The F75 implementation matches the prior recorded figures.
- Recovery-participation diagnostic supports the hypothesis that F75 trades some recovery exposure for defense: in 2022–2024 its realized exposure averages 52.5% vs B0's 70% for the next 20 sessions after the episode low, and 68.75% vs 90% over the next 60 sessions. In 2015–2016 it averages 75% vs 100% for the next 20 sessions and 89.58% vs 100% over 60 sessions. COVID and 2011 show no F75/B0 exposure difference after the trough.
- Decision remains unchanged: F75 is not promoted yet. Its aggregate historical balance is modestly higher at 0/25/50 bp and max drawdown improves by about 5.7–5.9 percentage points, but gains diminish sharply at 50 bp and episode returns remain concentrated in 2022–2024. Continue prospective shadow observation and next validate whether recovery-lag behavior repeats in future live observations.

## 2026-10-11 — prospective shadow F75 composition mismatch corrected

- Follow-up inspection found a consequential parity defect: the historical repeatability audit used the frozen F75 rule (75% exposure while the tightening overlay is active, capped by B0), but `research/f75_prospective_shadow_monitor.py` still used `np.minimum(b0, overlay)`. Since overlay state 0 means active, the monitor was recording a full exit rather than the frozen 75% exposure rule.
- Corrected the monitor to call `compose_f75_signal(b0, overlay, partial_exposure=0.75)`, with shape/range validation and the same composition semantics as the historical audit. No threshold or strategy optimization was made.
- Added a regression test asserting the prospective monitor returns [1.0, 0.75, 0.0, 1.0] for a representative B0/overlay input, and verifies the helper's 50% parameter behavior as well.
- Code fix commit: `7b82d808d011de8865ecbbbbb0dfc88cbba11e00`. Regression test commit: `d53ca5abad4d840048bc3367ca5e92cb1a6171a1`. The workflow is configured to run on changes to both the monitor and its guardrail test; verify a green run before considering the correction validated.
- No `data/research/f75_shadow_daily_ledger.csv` or `data/research/f75_shadow_state.json` exists at the expected branch paths at the time of inspection. Therefore no existing ledger rows were found to mix old full-exit observations with corrected partial-exposure observations. The first future shadow observation should be explicitly labeled as a fresh initialization, not represented as a long-running live ledger.
- Important next check: verify the prospective workflow's actual schedule/trigger and commit permissions, then verify that it appends only completed sessions and that the first initialized observation is clearly distinguished from a full-history backtest. F75 remains shadow-only and unpromoted.

## 2026-10-11 — shadow ledger persistence guard corrected

- The first post-fix monitor run [38132930488](https://github.com/eklu654/Trading-Bot/actions/runs/38132930488) completed successfully and printed a valid state summary (canonical hash matched, frozen cutoff 2026-10-07, latest source session 2026-10-09, two sessions calculated, shadow-only/no orders). However, its commit step reported no changes and did not persist the generated files.
- Root cause: the workflow used `git diff --quiet -- <paths>`, which does not detect newly created untracked files. The ledger/state files were absent from the branch before this run, and remained absent afterward; the successful script execution must not be confused with a persisted observation.
- Corrected the commit guard to inspect `git status --porcelain -- <paths>`, which detects both tracked modifications and new files. The workflow will then stage, commit, and push the append-only ledger and state files. The standard GitHub Actions bot identity is retained.
- Workflow fix commits: `9211b239d5b074e6771c3f0fbdfe0160cc0ee500` (detect untracked files) and `f8ab04941328ae7f2f30b30e5b46cce5ae05bed5` (restore standard bot email after an intermediate typo). A new workflow run is required to verify persistence end-to-end.
- The monitor's actual schedule is weekdays at 22:35 UTC; it also runs on relevant code/workflow pushes and supports manual dispatch. The first real persisted ledger must be checked for its initialization flag, dates, SHA-256, and F75 exposure semantics before treating the shadow observation series as established.

- Verification completed: monitor run [38133062634](https://github.com/eklu654/Trading-Bot/actions/runs/38133062634) passed all steps, including branch refresh, compilation/tests, two-session calculation, ledger commit, and push. The persisted ledger commit is `81ff2ab`; ledger file SHA-256 recorded in state is `5d649c56b94ebe8aed84f034daee67b95fdafeb74c5e24b62660e531c5697f4e`.
- Persisted first observation state is correctly marked `initialization_session=True` for 2026-10-08; 2026-10-09 is the first return-bearing session. The ledger has two rows, frozen source cutoff 2026-10-07, canonical source hash matches the pinned SHA-256, and mode is `SHADOW_ONLY_NO_ORDERS`. On both dates the tightening overlay is inactive (`f75_overlay_signal_close=1`), so B0 and F75 exposure/equity correctly match; these two ordinary sessions do not count as evidence for the overlay's efficacy.
- The two earlier ledger-persistence attempts failed at push because their checkouts were behind newer branch commits. The workflow now refreshes the latest research branch before reading the ledger, preventing a stale checkout from discarding or failing to append observations. The final run on the refreshed head passed and the files are now present on the branch.
- Regression verification: repeatability workflow run [38132935361](https://github.com/eklu654/Trading-Bot/actions/runs/38132935361) passed after the cross-monitor test was added; shadow monitor workflow run [38132974333](https://github.com/eklu654/Trading-Bot/actions/runs/38132974333) also passed the expanded monitor tests. The monitor's separate persistence fix is verified by run [38133062634](https://github.com/eklu654/Trading-Bot/actions/runs/38133062634).

## 2026-10-11 — prospective decision criteria preregistered

- Added [`research/F75_PROSPECTIVE_SHADOW_DECISION_PROTOCOL.md`](https://github.com/eklu654/Trading-Bot/blob/research/qqq-slow-bear-audit/research/F75_PROSPECTIVE_SHADOW_DECISION_PROTOCOL.md), commit `18d68dc97d5f08e648f60864ac2ca0ad14a0afc0`.
- The protocol requires at least 252 completed prospective sessions and one completed overlay-active episode with at least 20 sessions of actual exposure reduction before a performance review. Inactive-overlay days do not count as efficacy evidence.
- Predeclared screening criteria prioritize terminal equity at 25 bp costs, require no terminal-equity underperformance at 50 bp, require at least a 3 percentage-point max-drawdown improvement at 25 bp, and cap the 60-session post-trough realized-exposure gap at 20 percentage points when the full window is available. Data-integrity failures invalidate the review.
- Passing only authorizes a separate paper-trading evaluation; it does not promote F75 or permit live deployment. Failing leaves F75 frozen and shadow-only. No threshold optimization is authorized.
- Current sample is explicitly insufficient: two recorded rows, one return-bearing session, and no overlay activation. No efficacy conclusion or performance decision is permitted.

## 2026-10-11 — ledger integrity validation and idempotent reruns

- Added fail-closed validation before appending to an existing shadow ledger: required columns, valid strictly increasing unique dates, canonical source hash per row and in state, ledger SHA-256, state tail-date agreement, shadow-only mode, finite numeric values, and exposure bounds are checked. A state manifest without a ledger, or a ledger without state, is rejected.
- A rerun exposed another operational defect: the market download intentionally overlaps the frozen cutoff and prior ledger tail, but the monitor treated those already-recorded rows as an error. Extracted `only_unrecorded_sessions` and now filters to dates strictly after the validated ledger tail. A no-new-session rerun validates the existing manifest and exits successfully without rewriting the ledger.
- Regression coverage now tests ledger-hash mismatch, tail mismatch, duplicate dates, canonical-source mismatch, non-finite equity, complete overlap/idempotency, and mixed old/new sessions.
- Run [38133271821](https://github.com/eklu654/Trading-Bot/actions/runs/38133271821) passed the shadow monitor workflow with **14 tests**; it validated the persisted ledger/state and reported no new completed sessions, leaving the ledger unchanged as intended. This is the required idempotency check after the initial persisted ledger.
- Earlier monitor failures [38133168157](https://github.com/eklu654/Trading-Bot/actions/runs/38133168157) and [38133206610](https://github.com/eklu654/Trading-Bot/actions/runs/38133206610) are diagnostic failures from before the explicit tracking-ref refresh and/or idempotent-tail fix; they are superseded by the green run above, not silently treated as passes.
- Current shadow evidence remains two dates only (one return-bearing session), with no active overlay. The prospective minimum-evidence trigger has not been reached; F75 remains frozen and shadow-only.

- The historical repeatability workflow also passed on commit `609385e0e440b8b05ffce88252eb8fd346da839e`: run [38133265384](https://github.com/eklu654/Trading-Bot/actions/runs/38133265384), 10/10 tests passed, fixed attribution completed, and artifact ID `11700315891` uploaded (ZIP SHA-256 `3173e6b3c533aab427821d64ff6b9c0c86f7a72fdc52925c0fa3738d29f5fe8f`). The latest monitor-specific run [38133271821](https://github.com/eklu654/Trading-Bot/actions/runs/38133271821) passed 14/14 tests, including the new integrity and idempotency cases.

## 2026-10-11 — final shadow ledger invariants added

- Extended the persisted-ledger validator to verify the initialization marker occurs only on the first row, B0 and overlay state signals are binary, every stored F75 close signal exactly matches the frozen 75%-partial-exposure formula, and realized B0/F75 exposure is the prior session's close signal.
- Added regression tests for a full-exit value incorrectly recorded as F75, non-lagged realized exposure, and invalid initialization markers. These checks directly guard against reintroducing the historical-versus-prospective rule mismatch.
- Final validation run [38133368499](https://github.com/eklu654/Trading-Bot/actions/runs/38133368499) passed **17/17 shadow-monitor tests**, validated the existing ledger and state manifest, and completed an idempotent no-new-sessions run successfully. The ledger was not rewritten.
- Intermediate run [38133358288](https://github.com/eklu654/Trading-Bot/actions/runs/38133358288) failed because the validator was committed before the synthetic test fixture was updated to include the newly required signal columns. The fixture update and full 17-test run above supersede that expected sequencing failure.

## 2026-10-11 — persisted daily equity path reconciliation

- Extended existing-ledger validation to recompute every B0/F75 equity transition at 0/25/50 bp from prior realized exposure, the recorded overnight and intraday returns, and turnover costs. The validator now rejects non-positive equity as well as any balance that fails the accounting identity.
- Reordered validation so signal/lagged-exposure violations are reported before downstream equity mismatches. This makes the guardrail diagnostic and ensures the test for non-lagged exposure checks the intended invariant.
- Added tests for corrupted daily equity and non-positive equity. The first test run at `abf90c1` exposed a validation-order issue; the code was reordered and verified on the next run.
- Final monitor workflow [38133551399](https://github.com/eklu654/Trading-Bot/actions/runs/38133551399) passed **19/19 tests**, verified the current persisted ledger/state, reconciled daily balances across all three cost cases, and completed an idempotent no-new-sessions run without changing the ledger.
- This closes the current operational-integrity pass: historical and prospective F75 now share the same frozen 75% composition; ledger/state hashes, initialization, lagged exposures, and daily equity accounting are checked before future append operations. F75 still has only one return-bearing prospective session and no active-overlay observation, so there is still no prospective efficacy evidence.

- Historical attribution guardrail workflow [38133551400](https://github.com/eklu654/Trading-Bot/actions/runs/38133551400) also passed on commit `e7f46e3b2b5d4b2571e52781ec56fb0920cdb5fd`: 10/10 tests passed, fixed attribution completed, and artifact ID `11700430203` uploaded (ZIP SHA-256 `7dc88e76bafb4cfaf8c5775b9446104af1293b47e9ced6cef22bf9d784c4043a`).

## 2026-10-11 — shadow state manifest count semantics clarified

- Code audit found that the manifest field `sessions_appended` was set to `len(new)`, so it represented only the latest invocation's append batch despite sounding cumulative. This was ambiguous for audits and downstream monitoring.
- Updated the manifest to explicitly record `sessions_appended_this_run`, `ledger_rows_total`, `return_bearing_sessions_total`, and `initialization_date`, alongside the latest observation, pinned canonical hash, ledger hash, cost cases, and shadow-only mode.
- Change committed as `14a2a796b377f2a2811c418542dd9eb5b9c18e1b`. The push-triggered monitor run must verify compilation/tests and regenerate the manifest; the existing manifest is expected to be refreshed on the next successful append because the idempotent no-new-session path intentionally does not rewrite ledger or state.
- Scheduling audit: the research-branch workflow is configured for weekdays at 22:35 UTC and explicitly checks out/updates `research/qqq-slow-bear-audit`. GitHub scheduled workflows are evaluated from the repository's default branch; the workflow and monitor script were not found on `main` during this check. Therefore, do not assume this schedule will fire automatically while the workflow exists only on the research branch. Push/manual triggers work independently. Keep `main` unchanged; determine a branch-safe scheduled invocation mechanism before relying on unattended daily collection.

## 2026-10-11 — manifest semantics change verified by CI

- Monitor run [38135005143](https://github.com/eklu654/Trading-Bot/actions/runs/38135005143) passed all workflow steps on commit `14a2a796b377f2a2811c418542dd9eb5b9c18e1b`; all **19/19 tests passed**, canonical artifact download succeeded, and the monitor validated the persisted ledger/state. It found no new completed sessions after the frozen cutoff and existing ledger tail, so it correctly made no ledger/state change. The revised manifest fields will be written on the next actual append; do not claim the currently persisted manifest has been migrated yet.
- Historical repeatability run [38135005183](https://github.com/eklu654/Trading-Bot/actions/runs/38135005183) passed all steps; `episodes_accounting_validated=5`, and artifact ID `11701076047` uploaded with ZIP SHA-256 `a14f6be6011d57bc4fa72d1849475a16ea5fed6009398197148b9531c39f7c2b`.
- Full-period figures are unchanged and reconfirmed: B0/F75 terminal equity at 0 bp = $4,040,315 / $4,124,681; at 25 bp = $3,852,657 / $3,898,853; at 50 bp = $3,673,277 / $3,684,972. These are historical simulated results, not prospective evidence. The 50 bp incremental advantage is only about $11,695 on the same historical interval and the episode-level return advantage remains concentrated in 2022–2024.
- Scheduling remains an open operations issue: this workflow file and monitor script were not present on `main` during the check, while GitHub scheduled workflows are evaluated from the default branch. The research-branch workflow's explicit checkout does not by itself guarantee that its cron trigger runs. Research branch remains isolated; no change to `main` was made.
- Decision remains frozen: B0 control, F75 shadow-only, no parameter tuning, no broker orders. The prospective ledger remains only two dates (one return-bearing session) with zero active-overlay sessions, so the 252-session and 20-session overlay-episode gates remain unmet.


## 2026-10-11 — fail-closed F75 input validation and scheduler proposal

- Hardened `compose_f75_signal` so it rejects non-finite/non-binary B0 or overlay inputs and rejects non-finite or out-of-range partial exposure. This prevents malformed inputs from silently being converted into an apparently valid F75 signal.
- Added four regression cases covering non-binary B0, non-binary overlay, non-finite signal data, and non-finite partial exposure. Commit `02f0797f33fc78ea6d04d62c3ce49b383adaac28` contains the validator; `f8727d1da54820ee2ed24e81a9a81d181ec4271b` adds tests.
- Monitor run [38136059751](https://github.com/eklu654/Trading-Bot/actions/runs/38136059751) passed compilation and **23/23 tests**, downloaded the immutable canonical B0 artifact, validated the persisted ledger/state, and completed the idempotent no-new-session path. It explicitly logged that no ledger/state change was made. Historical attribution run [38136053359](https://github.com/eklu654/Trading-Bot/actions/runs/38136053359) also passed its guardrails, completed the fixed attribution, and uploaded the report.
- The scheduler concern was verified against the live repository: `.github/workflows/f75-prospective-shadow-monitor.yml` returns 404 on `main`, while it exists on `research/qqq-slow-bear-audit`. To preserve the explicit no-change-to-`main` constraint, opened draft PR [#26](https://github.com/eklu654/Trading-Bot/pull/26) from `ops/f75-shadow-scheduler-default-branch`. It proposes a default-branch scheduled workflow that checks out and writes only the research branch. The PR is unmerged; `main` remains unchanged. Before merge, review the workflow and confirm repository Actions settings allow the default `GITHUB_TOKEN` to write to the research branch.
- No strategy rules or thresholds changed. B0 remains control; F75 remains frozen, shadow-only, and no-orders. Prospective efficacy remains insufficient: one return-bearing session and zero active-overlay sessions; 252 sessions and a 20-session active-overlay episode are still required for the preregistered review.

## 2026-10-11 follow-up — canonical artifact and scheduler review

- Independently downloaded and inspected canonical B0 artifact `11694047458` from run `38117700318`. ZIP contains the exact expected `tqqq_actual_partial_dma_frozen_input.csv`, matrix, periods, and manifest. Manifest reports PASS, 4,189 input rows, evaluation end `2026-10-07`, $5,000 initial balance, and canonical B0 signal match. Extracted frozen-input SHA-256 is `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`, matching the hard-coded monitor hash. ZIP SHA-256: `11ab93b082db11c813ff09a0b069e7bbd4e48c86fa542f6f1189e6b1b9c68439`.
- Reviewed draft scheduler against the working monitor workflow: Python 3.12, declared research requirements, pinned artifact run/name, compile + unit tests, append-only monitor, and push limited to ledger/state files match the existing tested path. Scheduler uses the same concurrency group to prevent overlap with manual/push-triggered monitor runs.
- Remaining deployment check is repository-level Actions write permission for `GITHUB_TOKEN`; the connector cannot confirm that repository setting from the available read endpoint. Keep PR #26 draft/unmerged until the setting is verified and the owner explicitly chooses to enable default-branch scheduling. This is an operational gate, not a strategy result.
- Current source of truth remains unchanged: `main` SHA `2644cd8afe167afe2667c7831d3967328f337595`; PR #26 remains open, draft, and unmerged. No change to B0/F75 rules, no broker access, no orders.

- Static syntax check of the draft `.github/workflows/f75-shadow-scheduler.yml` passed with a YAML parser: one job (`shadow-monitor`), schedule `35 22 * * 1-5`, and expected workflow keys. This is a syntax check only—not a live GitHub Actions run—because the draft scheduler is intentionally unmerged and the default-branch workflow cannot be exercised until enabled there.


## 2026-10-11 — default-branch scheduler activated

- Merged PR [#26](https://github.com/eklu654/Trading-Bot/pull/26) as commit `271bb26eeef3a430927ff3c1cbbda5017b07fcb1`. The scheduler is now on `main`; this is the first main-branch change for the shadow monitor and is limited to `.github/workflows/f75-shadow-scheduler.yml`.
- Reverified `main` points at the merge commit and the scheduler file is present on `main`. Workflow requests `contents: write` and `actions: read`, schedule `35 22 * * 1-5`, and has a manual dispatch trigger.
- Merge triggered existing `research-tests` workflow run [38178501790](https://github.com/eklu654/Trading-Bot/actions/runs/38178501790), initially queued at 2026-10-11 21:57:59 UTC. This is a repository test workflow, not the F75 scheduler itself.
- The F75 scheduler has not yet run on the default branch; its next cron is Monday 2026-10-12 at 22:35 UTC unless manually dispatched. Therefore runtime artifact-download, test, and research-branch push permissions remain unverified until a scheduler run completes.
- Safety unchanged: frozen F75 shadow-only, no broker connection/orders, no strategy threshold changes. At each run, validate the exact result and push behavior; do not infer a ledger write if no new completed session exists.
