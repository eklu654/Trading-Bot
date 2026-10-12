# Adaptive LEAPS year-by-year coverage review — 2026-10-12

## Provenance

- Coverage workflow run: [38225648878](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878) (success).
- Artifact: [adaptive-leaps-data-coverage](https://github.com/eklu654/Trading-Bot/actions/runs/38225648878/artifacts/11736311901).
- Analysis uses `coverage_by_year_dte_delta.csv` from that artifact, not a new quote download.
- Filter for this review: calls, 270–539 DTE, absolute delta 0.60–0.84 (two buckets 0.60–0.74 and 0.75–0.84). Rows are contract-day observations, not unique contracts.

## Annual candidate-region coverage

`Valid + active %` = rows passing bid > 0, ask >= bid, mark > 0, and (volume > 0 OR open interest > 0), divided by contract-day rows in the filtered region. Spread is the median of the bucket-level median relative spreads; it is a descriptive approximation, not a row-weighted spread estimate.

### SPY

| Year | Candidate rows | Valid + active | Pass % | Median bucket spread | Observation dates (max bucket) |
|---:|---:|---:|---:|---:|---:|
| 2008 | 3,302 | 2,485 | 75.3% | 1.82% | 220 |
| 2009 | 661 | 587 | 88.8% | 2.51% | 138 |
| 2010 | 8,327 | 5,333 | 64.0% | 1.48% | 238 |
| 2011 | 15,068 | 11,832 | 78.5% | 2.02% | 252 |
| 2012 | 14,734 | 11,273 | 76.5% | 1.80% | 250 |
| 2013 | 13,476 | 11,869 | 88.1% | 1.37% | 252 |
| 2014 | 16,860 | 14,193 | 84.2% | 1.60% | 252 |
| 2015 | 16,408 | 14,269 | 87.0% | 1.57% | 252 |
| 2016 | 15,892 | 12,973 | 81.6% | 1.17% | 252 |
| 2017 | 26,292 | 22,605 | 86.0% | 1.00% | 251 |
| 2018 | 18,710 | 13,939 | 74.5% | 1.55% | 250 |
| 2019 | 32,241 | 26,246 | 81.4% | 1.09% | 251 |
| 2020 | 44,379 | 35,649 | 80.3% | 1.57% | 252 |
| 2021 | 45,216 | 34,421 | 76.1% | 2.03% | 252 |
| 2022 | 24,091 | 19,091 | 79.2% | 3.41% | 251 |
| 2023 | 22,039 | 18,139 | 82.3% | 3.96% | 250 |
| 2024 | 35,150 | 31,204 | 88.8% | 3.33% | 252 |
| 2025 | 33,088 | 29,555 | 89.3% | 4.32% | 238 |

### QQQ

| Year | Candidate rows | Valid + active | Pass % | Median bucket spread | Observation dates (max bucket) |
|---:|---:|---:|---:|---:|---:|
| 2011 | 5,031 | 3,298 | 65.6% | 2.73% | 197 |
| 2012 | 6,012 | 4,767 | 79.3% | 2.12% | 250 |
| 2013 | 5,029 | 4,252 | 84.5% | 2.33% | 252 |
| 2014 | 10,909 | 8,135 | 74.6% | 4.38% | 252 |
| 2015 | 8,229 | 6,705 | 81.5% | 3.40% | 251 |
| 2016 | 8,109 | 5,179 | 63.9% | 2.40% | 251 |
| 2017 | 9,077 | 6,951 | 76.6% | 2.65% | 251 |
| 2018 | 16,641 | 11,111 | 66.8% | 3.34% | 250 |
| 2019 | 18,397 | 11,676 | 63.5% | 6.11% | 251 |
| 2020 | 34,595 | 23,713 | 68.5% | 4.80% | 252 |
| 2021 | 30,591 | 20,097 | 65.7% | 2.92% | 251 |
| 2022 | 19,185 | 14,603 | 76.1% | 2.25% | 251 |
| 2023 | 24,739 | 19,181 | 77.5% | 1.72% | 250 |
| 2024 | 32,074 | 27,086 | 84.4% | 2.42% | 252 |
| 2025 | 30,394 | 29,322 | 96.5% | 3.60% | 239 |

## Findings and decisions

1. **Broad historical coverage is present**, but it is uneven. SPY's 2009 candidate region is much thinner than adjacent years; QQQ begins only in 2011 and has fewer observation dates in 2011. Do not treat these periods as equivalent to full-year coverage.
2. **Quote/activity pass rates are not execution rates.** The metric combines quote validity with nonzero volume or open interest; it does not establish that a selected contract could be bought/sold at the displayed EOD mark.
3. **Spreads are regime- and year-dependent.** QQQ's 2019 candidate-region median of bucket medians is about 6.1%, and SPY spreads rise in 2022–2025. Replay must apply explicit, conservative fill/slippage assumptions and stress them; do not assume midpoint fills.
4. **The source's 2025 observation window is incomplete** (238–239 dates in this filtered region), so annual comparisons should label it partial-year/source-window coverage.
5. **No strategy conclusion follows from coverage.** This is a data availability gate only, not a return, drawdown, or paper-trading result.

## Required next validation before lifecycle replay

- Join candidate rows to same-date underlying prices and assert match coverage and positive prices.
- Confirm stable option identity fields and detect duplicate rows for (date, expiration, strike, type); do not infer continuity from a delta bucket alone.
- Define candidate selection deterministically (target DTE, delta, liquidity tie-breaks) with no future-data leakage.
- Define conservative entry/exit prices from bid/ask and explicit slippage; mark-to-market using mid is a separate sensitivity, not the primary executable model.
- Handle expirations, exercise/assignment, cash requirements, contract multipliers, corporate actions, and missing quotes explicitly.
- Freeze the long-call lifecycle rules before evaluating the short-call overlay. Preserve the already-frozen rebound rule: when the market improves, close/remove the short call rather than automatically writing another; if deterioration persists, manage it only under explicit predeclared rules.
