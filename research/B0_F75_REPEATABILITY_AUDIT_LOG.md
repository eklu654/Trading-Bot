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
