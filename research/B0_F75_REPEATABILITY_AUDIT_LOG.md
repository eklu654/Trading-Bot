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
