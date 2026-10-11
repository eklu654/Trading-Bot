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

