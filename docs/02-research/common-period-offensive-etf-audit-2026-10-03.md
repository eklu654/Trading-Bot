# Common-Period Offensive ETF Audit — 2026-10-03

> **Endpoint update:** This document contains the earlier 2026-09-25 snapshot. ETF-031 has since established a newer validated common endpoint of **2010-03-11 → 2026-10-02** for TQQQ/QQQ/SOXL/SPXL comparisons. Do not use the older dollar figures below as the current headline benchmark; use `docs/02-research/etf-031-results.md` instead. The family-rotation replay is also being regenerated through 2026-10-02.

## Research rule

All headline comparisons use the same available historical endpoint: **2010-01-04 through 2026-09-25**, or the later common start date forced by the instruments in a particular portfolio. No 2018-2025 result should be compared directly with a 2010-present result.

Starting capital for terminal-wealth comparisons is **$5,000**.

## Core controls

| Strategy | Start | End | $5k ending balance | CAGR | Max DD |
|---|---|---|---:|---:|---:|
| TQQQ buy-and-hold | 2010-01-04 | 2026-09-25 | $1,939,711 | 42.83% | -81.66% |
| SOXL buy-and-hold | 2010-01-04 | 2026-09-25 | $1,261,095 | 39.19% | -90.46% |
| SPXL buy-and-hold | 2010-01-04 | 2026-09-25 | $359,058 | 29.12% | -76.86% |
| TQQQ 200-DMA/cash | 2010-01-04 | 2026-09-25 | $358,838 | 29.12% | -50.01% |
| SOXL 200-DMA/cash | 2010-01-04 | 2026-09-25 | $171,999 | 23.56% | -75.65% |
| SPXL 200-DMA/cash | 2010-01-04 | 2026-09-25 | $114,398 | 20.59% | -57.82% |
| SSO 2x buy-and-hold | 2010-01-04 | 2026-09-25 | $157,323 | 22.90% | -59.34% |
| SPY 1x buy-and-hold | 2010-01-04 | 2026-09-25 | $45,713 | 14.15% | -33.72% |

## Five-family always-bull control

The equal-weight five-family control uses SPXL, TQQQ, SOXL, UDOW and TNA. The common tradable start is **2010-03-11** because SOXL is the limiting instrument.

Recalculation from the historical artifact:

- 2010-03-11 → 2025-12-31: approximately **$346,315**
- 2010-03-11 → 2026-09-25: approximately **$616,117**
- CAGR through 2026-09-25: approximately **33.78%**
- Max drawdown: approximately **-78.26%**

The repository's documented benchmark reports approximately **$621,427**, 33.85% CAGR and -78.26% DD; the small terminal-value difference is attributable to the exact artifact/data version used for the reconstruction. The date range is the important correction: **the $621k figure includes 2026 and is not a 2010-2025 result.**

## ETF-001 three-sleeve controls

The historical artifact's ETF-001 portfolio uses equal TQQQ/SPXL/SOXL sleeves.

From 2010-03-11 through 2026-09-25:

- 100% invested buy-and-hold: total-return multiple 209.012493, approximately **$1,045,062** from $5,000; CAGR 38.12%; max DD -82.10%.
- 200-DMA, 0% cash: total-return multiple 38.974750, approximately **$194,874**; CAGR 24.79%; max DD -47.84%.
- 200-DMA, 25% cash: total-return multiple 18.992398, approximately **$99,962**; CAGR 19.85%; max DD -37.35%.
- 200-DMA+VIX, 25% cash: total-return multiple 6.941912, approximately **$34,710**; CAGR 13.34%; max DD -41.35%.

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
