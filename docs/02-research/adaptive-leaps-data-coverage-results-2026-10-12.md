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

## Contract-integrity follow-up

The second audit run [38226350847](https://github.com/eklu654/Trading-Bot/actions/runs/38226350847) completed successfully and uploaded [artifact 11735797875](https://github.com/eklu654/Trading-Bot/actions/runs/38226350847/artifacts/11735797875). In the tested call region (270–539 DTE, absolute delta 0.60–0.84):

- Both SPY and QQQ had **zero duplicate (date, expiration, strike, type) key groups**.
- Every candidate observation joined to a same-date underlying row with a positive close: **100% match coverage for every included year**.
- No candidate rows joined to duplicate underlying dates.
- The check identified underlying columns `date` and `close` in both datasets.

This clears those specific integrity checks, not the complete replay gate: corporate-action adjustments, executable fills, expiry/exercise/assignment, and account feasibility remain unvalidated.

## Year-by-year follow-up

The artifact was subsequently analyzed by year for calls in the 270–539 DTE / absolute-delta 0.60–0.84 region. The separate [year-by-year review](adaptive-leaps-yearly-coverage-review-2026-10-12.md) records thin early-year coverage, partial 2025 coverage, and material year-to-year spread variation. This narrows the next gate but does not establish executable prices.

## Immutable source and reproducibility

The source repository revision was identified as [37f6c456fe1a4775c875673fb8ef907d5cd2fd66](https://github.com/anahatsingh-ui/options-dataset-hist/commit/37f6c456fe1a4775c875673fb8ef907d5cd2fd66). The workflow has been updated to fetch from that immutable commit and record SHA-256 hashes for all downloaded Parquet files; the pin/hash run is pending as of this note.

## Known limitations

- EOD data cannot reconstruct intraday quote paths or order priority.
- DTE coverage can be biased near the dataset start/end.
- Coverage counts alone do not validate fills, exercise, assignment, or rolling.

## Target long-call region: 270–539 DTE calls by absolute-delta bucket

This narrower table focuses on the initial 270/365-day long-call candidates. Counts are contract-day observations aggregated across the full source period, not unique contracts.

| Underlying | Absolute-delta bucket | Contract-day rows | Valid quote + activity rows | Share passing |
|---|---|---:|---:|---:|
| SPY | 0.60–0.74 | 217,437 | 184,117 | 84.7% |
| SPY | 0.75–0.84 | 168,497 | 131,546 | 78.1% |
| SPY | 0.85–1.00 | 680,312 | 435,679 | 64.0% |
| QQQ | 0.60–0.74 | 148,895 | 117,280 | 78.8% |
| QQQ | 0.75–0.84 | 110,117 | 78,796 | 71.6% |
| QQQ | 0.85–1.00 | 316,702 | 203,885 | 64.4% |

**Interpretation:** there is substantial aggregate coverage in all three call-delta bands, but valid-quote-plus-activity share is lower in the highest-delta band. This is only a feasibility signal. Before replay, inspect year-level availability, spread distributions, underlying-price joins, contract identity/continuity, and the actual quote on each chosen entry/exit date. The audit currently does not enforce unique contract keys or model fills.
