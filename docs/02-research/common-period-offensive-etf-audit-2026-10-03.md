# Common-Period Offensive ETF Audit — 2026-10-04

## Research rule

All headline comparisons use the same available historical endpoint: **2010-03-11 through 2026-10-02 for the ETF-031 common control set**, or the later common start date forced by the instruments in a particular portfolio. No 2018-2025 result should be compared directly with a 2010-present result.

Starting capital for terminal-wealth comparisons is **$5,000**.

## Core controls

| Strategy | Start | End | $5k ending balance | CAGR | Max DD |
|---|---|---|---:|---:|---:|
| TQQQ buy-and-hold | 2010-03-11 | 2026-10-02 | $1,558,429 | 41.44% | -81.66% |
| SOXL buy-and-hold | 2010-03-11 | 2026-10-02 | $1,363,181 | 40.30% | -90.46% |
| SPXL buy-and-hold | 2010-03-11 | 2026-10-02 | $339,693 | 29.01% | -76.86% |
| TQQQ 200-DMA/cash | 2010-03-11 | 2026-10-02 | $329,962 | 28.78% | -50.01% |
| SOXL 200-DMA/cash | 2010-03-11 | 2026-10-02 | [not part of ETF-031 direct-control artifact] | — | -75.65% |
| SPXL 200-DMA/cash | 2010-03-11 | 2026-10-02 | [not part of ETF-031 direct-control artifact] | — | -57.82% |
| SSO 2x buy-and-hold | 2010-03-11 | 2026-10-02 | [not part of ETF-031 direct-control artifact] | — | -59.34% |
| SPY 1x buy-and-hold | 2010-03-11 | 2026-10-02 | $91,390 | 19.18% | -33.72% |

## Five-family always-bull control

The equal-weight five-family control uses SPXL, TQQQ, SOXL, UDOW and TNA. The common tradable start is **2010-03-11** because SOXL is the limiting instrument.

Recalculation from the historical artifact:

- 2010-03-11 → 2025-12-31: approximately **$378,052**
- 2010-03-11 → 2026-10-02: approximately **[superseded; see ETF-031 frozen family-rotation control]**
- CAGR through 2026-09-25: approximately **29.85%**
- Max drawdown: approximately **-78.26%**

The repository's documented benchmark reports approximately **[superseded; see ETF-031]**, 29.85% CAGR and -78.26% DD; the small terminal-value difference is attributable to the exact artifact/data version used for the reconstruction. The date range is the important correction: **the $621k figure includes 2026 and is not a 2010-2025 result.**

## ETF-001 three-sleeve controls

The historical artifact's ETF-001 portfolio uses equal TQQQ/SPXL/SOXL sleeves.

From 2010-03-11 through 2026-09-25:

- 100% invested buy-and-hold: total-return multiple 209.012493, approximately **[superseded; see ETF-031 common-period controls]** from $5,000; CAGR [superseded]; max DD -82.10%.
- 200-DMA, 0% cash: total-return multiple 38.974750, approximately **$329,962**; CAGR 28.78%; max DD -47.84%.
- 200-DMA, 25% cash: total-return multiple 18.992398, approximately **[superseded; separate ETF-001 accounting]**; CAGR [superseded]; max DD -37.35%.
- 200-DMA+VIX, 25% cash: total-return multiple 6.941912, approximately **[superseded; separate ETF-001 accounting]**; CAGR [superseded]; max DD -41.35%.

## Important methodological distinction

The single-ETF controls above use the common research endpoint in the dynamic-leverage artifact. The five-family control has a later common start because SOXL did not have observations before 2010-03-11.

This is preferable to truncating every strategy to 2018-2025 merely for convenience. The goal is now to use **the longest identical available period for each explicitly defined comparison set**, while never mixing periods in the same table.

## Interpretation

The date-range correction materially changes the apparent comparisons. The five-family $621k figure is a 2010-2026 result. It should be compared against other strategies over that same period before drawing conclusions.

The next research gate is:

1. Keep **2010-01-04 → 2026-09-25** as the common headline period where the required instruments permit it.
2. Preserve the exact common start date when an instrument limits availability.
3. Use exact $5,000 terminal wealth, not CAGR-derived approximations.
4. Keep maximum drawdown alongside terminal wealth rather than using drawdown as an automatic rejection criterion.
5. Separately evaluate train/validation/holdout behavior so the long full-period result is not mistaken for evidence of future performance.
6. Retain buy-and-hold TQQQ/SOXL and the five-family always-bull portfolio as aggressive controls.
7. Compare dynamic/switching strategies against these controls over the identical full period before spending more compute on parameter refinement.


## 2026-10-04 authority note

The older 2026-09-25 dollar figures in this document are superseded. For headline offensive-control comparisons, use `docs/02-research/etf-031-results.md` and `docs/02-research/dma-family-rotation-5000-account-replay.md`. Do not mix the older endpoint with the current 2026-10-02 controls.
