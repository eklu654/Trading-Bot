# Adaptive LEAPS data coverage audit — 2026-10-12

## Execution record

- Workflow: [Adaptive LEAPS Data Coverage Audit](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878)
- Commit under test: `adbfd186f2f71d5668c8cbaebb005a63cffb8022`
- Result: **success**; all audit steps completed, including dataset downloads, Python compilation, coverage report generation, and artifact upload.
- Artifact: [adaptive-leaps-data-coverage](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878/artifacts/11736311901) (contains `summary.json` and `coverage_by_year_dte_delta.csv`).

## Findings

| Underlying | EOD contract-day rows | DTE >=270 rows | DTE >=270 valid + active rows | Valid + active share |
|---|---:|---:|---:|---:|
| SPY | 24,681,665 | 5,792,357 | 4,455,633 | 76.9% |
| QQQ | 15,345,882 | 3,089,957 | 2,275,977 | 73.7% |

- SPY source coverage: 2008–2025.
- QQQ source coverage: 2011–2025.
- EOD quote validity requires bid > 0, ask >= bid, and mark > 0. Activity means volume > 0 OR open interest > 0.
- The reported rows are contract-day observations, **not** unique contracts, independently executable fills, or proof of realistic assignment/roll execution.

## Decision and next work

1. The data acquisition and coverage-report pipeline is now operational and reproducibly produces an artifact.
2. Do **not** treat this audit as strategy-performance validation. It establishes broad candidate-data coverage only.
3. Next: inspect the year-by-year and DTE/delta buckets for gaps and quote-quality concentration, then build a deterministic long-call lifecycle replay with explicit quote selection, spread/slippage assumptions, contract continuity, and lifecycle/assignment handling. Keep the short-call rebound behavior frozen as already specified; do not optimize thresholds during this validation stage.
4. Before interpreting any replay results, document survivorship, dataset-boundary bias, missing/crossed/zero quotes, and how an order is priced when the EOD snapshot is not demonstrably executable.

## Known limitations

- EOD data cannot reconstruct intraday quote paths or order priority.
- DTE coverage can be biased near the dataset start/end.
- Coverage counts alone do not validate fills, exercise, assignment, or rolling.
