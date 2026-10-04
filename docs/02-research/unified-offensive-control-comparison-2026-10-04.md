# Unified Offensive Control Comparison — 2026-10-04

## Purpose
Authoritative return-first comparison for the current leveraged-ETF research. Aggressive controls remain first-class candidates; drawdown is measured as an explicit survivability/operational constraint, not an automatic veto.

## Canonical comparison
- Starting capital: **$5,000**
- ETF-031 direct-control period: **2010-03-11 → 2026-10-02**
- Family-rotation account replay: **2010-03-12 → 2026-10-02** because its signal needs prior observations.
- Direct controls use the same common period and adjusted-return conventions.
- No same-family bull/bear overlap is permitted.
- Holdout performance is evidence, not a forecast.

## Direct controls

| Strategy | Ending $5k | CAGR | Max DD | Recovery days |
|---|---:|---:|---:|---:|
| **TQQQ buy-and-hold** | **$1,558,429** | **41.44%** | -81.66% | 707 |
| **SOXL buy-and-hold** | **$1,363,182** | **40.30%** | -90.46% | 1,230 |
| **SPXL buy-and-hold** | **$339,693** | **29.01%** | -76.86% | 291 |
| **TQQQ 200-DMA/cash** | **$329,962** | **28.78%** | -50.01% | 105 |
| **TQQQ 200-DMA/next-open** | **$504,212** | **32.12%** | -48.14% | 164 |
| **Frozen DMA250/top-2/5 family rotation** | **$378,052** | **29.85%** | -67.40% | 354 |
| QQQ buy-and-hold | $91,390 | 19.18% | -35.12% | 405 |

## $5,000 family-rotation implementation replay — 25 bps

| Strategy | Execution | Ending | CAGR | Max DD | Max $ DD | Minimum equity | Max recovery |
|---|---|---:|---:|---:|---:|---:|---:|
| **DMA250/top-2/5** | prior close | **$228,285** | **25.96%** | -68.62% | -$143,072 | $2,032 | 913d |
| **DMA250/top-2/5** | next open | **$176,531** | **24.02%** | -69.91% | -$101,452 | $2,374 | 873d |
| DD20 overlay | prior close | $23,294 | 9.74% | -38.94% | -$6,117 | $3,214 | 1,052d |
| DD20 overlay | next open | $24,622 | 10.11% | -38.99% | -$7,031 | $3,477 | 1,052d |
| DD25 overlay | prior close | $29,187 | 11.24% | -41.27% | -$6,468 | $3,185 | 1,043d |
| DD25 overlay | next open | $33,039 | 12.08% | -42.22% | -$7,572 | $3,455 | 980d |
| DD30 overlay | prior close | $33,781 | 12.23% | -43.65% | -$8,177 | $3,003 | 1,080d |
| DD30 overlay | next open | $29,642 | 11.35% | -47.48% | -$7,247 | $3,151 | 990d |

### Family-rotation cost stress

| Cost | Prior-close ending | Next-open ending |
|---:|---:|---:|
| 0 bps | $377,251 | $291,682 |
| 10 bps | $308,608 | $238,890 |
| 25 bps | $228,285 | $176,531 |
| 50 bps | $137,744 | $106,542 |

## Interpretation

1. **Offensive controls are economically enormous.** From $5,000, the validated historical endpoints range from $91k for QQQ to $1.56M for TQQQ buy-and-hold.
2. **Drawdown alone cannot justify rejection.** Replacing the raw family rotation with DD20–30 overlays trades roughly $176k–$228k of 25-bps next/prior-close terminal wealth for approximately 39–47% maximum drawdown instead of ~69%. That is a real tradeoff, not an automatic improvement.
3. **TQQQ 200-DMA/next-open is a major control.** It historically reduced max DD from 81.66% to 48.14% while retaining 32.12% CAGR and ~$504k from $5k.
4. **CAGR alone is insufficient.** TQQQ and SOXL buy-and-hold experienced extreme drawdowns and long recoveries. Path-permutation tests also demonstrated that identical terminal returns can have radically different drawdown paths.

## Research-priority tiers

### Tier A — first-class offensive controls
1. TQQQ buy-and-hold
2. SOXL buy-and-hold
3. TQQQ 200-DMA next-open
4. Frozen DMA250/top-2/5 family rotation
5. SPXL buy-and-hold

### Tier B — defensive controls
6. TQQQ 200-DMA/cash
7. Family-rotation DD20/DD25/DD30
8. QQQ buy-and-hold benchmark

These are research priorities, **not production rankings**.

## Next gates

Before choosing a paper-trading candidate, compare Tier-A controls on:
- 25/50/60/70% drawdown frequency and time-under-water;
- minimum equity and maximum dollar loss;
- rolling and start-date robustness;
- train/validation/untouched holdout behavior;
- prior-close versus next-open execution;
- 10/25/50 bps costs and slippage sensitivity;
- parameter-neighborhood robustness;
- whole-share $5,000 feasibility;
- broker/margin constraints;
- restart recovery, duplicate-order prevention, stale-data fail-closed behavior, and fill reconciliation.

Do not run another broad parameter sweep until these controls have been characterized consistently.

## Decision principle

**Maximize robust wealth subject to predeclared survivability and operational constraints.**

The objective is neither minimum drawdown nor unconstrained historical CAGR.

No production strategy is selected by this document.
