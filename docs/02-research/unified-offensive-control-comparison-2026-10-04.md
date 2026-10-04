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
| **TQQQ 200-DMA/next-open** | **$504,212** | **32.12%** | -48.14% | 162 |
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

## Path-survivability evidence update

The ETF-031 frozen artifact has now been extended with rolling-window path diagnostics for TQQQ buy-and-hold. These show that severe drawdowns are not an isolated single-event statistic: for example, **57.30% of observed 3-year windows breached a 50% internal drawdown, 38.01% breached 60%, and 20.78% breached 70%**. The corresponding 5-year incidences were 67.23%, 56.71%, and 37.17%. These are overlapping-window diagnostics, not independent samples or time-under-water percentages.

The same analysis found a worst 1-year rolling CAGR of **-81.15%**, worst 3-year CAGR of **-11.25%**, and worst 5-year CAGR of **+5.66%**. This reinforces the need to evaluate terminal wealth and path survivability together.

See `docs/02-research/etf031-path-survivability-addendum-2026-10-04.md`.


## Tier-A path survivability — completed 2026-10-04

The dedicated Tier-A rolling audit completed successfully on GitHub Actions run **37182850500**. The artifact covers **2010-03-11 → 2026-10-02** and evaluates overlapping 1-, 3-, 5-, and 10-year windows. This is a descriptive path audit; the overlapping windows are not independent samples.

### Worst rolling CAGR

| Strategy | 1y | 3y | 5y | 10y |
|---|---:|---:|---:|---:|
| TQQQ buy-and-hold | -81.15% | -11.25% | +5.66% | +25.34% |
| SOXL buy-and-hold | -87.42% | -39.81% | -3.76% | +15.02% |
| SPXL buy-and-hold | -60.91% | -15.56% | -4.54% | +14.28% |
| TQQQ 200-DMA/next-open | -39.03% | -5.48% | +12.96% | +21.90% |
| DMA250/top-2/5 family rotation | -63.05% | -10.83% | -0.05% | +11.73% |

### Rolling drawdown breach incidence

| Strategy | Window | >=50% DD | >=60% DD | >=70% DD | >=80% DD |
|---|---|---:|---:|---:|---:|
| TQQQ buy-and-hold | 1y | 26.84% | 12.67% | 5.23% | 1.43% |
| TQQQ buy-and-hold | 3y | 57.30% | 38.01% | 20.78% | 16.41% |
| TQQQ buy-and-hold | 5y | 67.23% | 56.71% | 37.17% | 34.22% |
| TQQQ buy-and-hold | 10y | 100.00% | 100.00% | 65.59% | 60.38% |
| SOXL buy-and-hold | 1y | 52.48% | 40.12% | 22.80% | 13.56% |
| SOXL buy-and-hold | 3y | 94.90% | 83.59% | 55.54% | 48.21% |
| SPXL buy-and-hold | 1y | 21.99% | 8.38% | 6.10% | 0.00% |
| SPXL buy-and-hold | 3y | 56.89% | 35.81% | 21.78% | 0.00% |
| TQQQ 200-DMA/next-open | 1y | 0.00% | 0.00% | 0.00% | 0.00% |
| TQQQ 200-DMA/next-open | 3y | 0.00% | 0.00% | 0.00% | 0.00% |
| DMA250/top-2/5 family rotation | 1y | 31.36% | 12.36% | 0.00% | 0.00% |
| DMA250/top-2/5 family rotation | 3y | 80.13% | 59.70% | 0.00% | 0.00% |

The key result is that **TQQQ 200-DMA/next-open is not merely lower in terminal wealth than TQQQ buy-and-hold; it has a radically different path profile in this audit**. No observed rolling window breached 50% drawdown for the 1-, 3-, 5-, or 10-year windows, while its worst 5-year CAGR remained +12.96%.

The raw family rotation has substantially more path risk than the TQQQ 200-DMA/next-open control despite lower full-period terminal wealth. Its 3-year windows breached 50% drawdown in 80.13% of observations and 60% in 59.70%.

### Negative-CAGR incidence

| Strategy | 1y | 3y | 5y | 10y |
|---|---:|---:|---:|---:|
| TQQQ buy-and-hold | 17.16% | 3.69% | 0.00% | 0.00% |
| SOXL buy-and-hold | 32.46% | 13.34% | 0.89% | 0.00% |
| SPXL buy-and-hold | 22.42% | 1.47% | 0.07% | 0.00% |
| TQQQ 200-DMA/next-open | 24.00% | 1.23% | 0.00% | 0.00% |
| DMA250/top-2/5 family rotation | 34.58% | 3.99% | 0.03% | 0.00% |

This creates an important distinction: the 200-DMA control eliminates the observed severe drawdown breaches but does **not** eliminate poor short-horizon outcomes. Its worst 1-year rolling CAGR was still -39.03%.

### Research implication

The current evidence makes **TQQQ 200-DMA/next-open the most important defensive control to compare directly against the newly tested DMA/re-entry grid**, while TQQQ buy-and-hold remains the wealth benchmark. The next-open execution sensitivity is therefore being tested across the full 56-cell DMA/re-entry matrix rather than assuming that the prior-close grid's 250-DMA/10-session leader survives execution realism.


## Decision principle

**Maximize robust wealth subject to predeclared survivability and operational constraints.**

The objective is neither minimum drawdown nor unconstrained historical CAGR.

No production strategy is selected by this document.
