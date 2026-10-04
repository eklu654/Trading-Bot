# ETF family-rotation $5,000 account replay — 2026-10-04

## Purpose

This replay checks implementation feasibility of the frozen DMA-250 / top-2 / 5-session family-rotation strategy and the small risk-overlay robustness cluster using a canonical **$5,000 starting balance**.

It is an implementation-feasibility test, not a live-trading simulator or a forecast.

The replay uses:

- SPXL, TQQQ, SOXL, UDOW, and TNA;
- whole-share positions only;
- explicit residual cash;
- 0 / 10 / 25 / 50 bps transaction-cost stress;
- causal signal timing;
- two execution sensitivities:
  - **prior close** — the existing research convention;
  - **next open** — a more realistic execution sensitivity;
- chronological full/train/validation/holdout reporting.

For the next-open model, the prior close supplies the signal, the next session's adjusted open is the execution price, and the position is marked at the following adjusted open. Adjusted OHLC is constructed from the downloaded OHLC and adjusted-close series so splits/distributions remain represented.

## Results

The replay was regenerated after discovering that the shared CI yfinance snapshot stopped at 2026-09-25. A pinned endpoint patch was added for the five leveraged family ETFs and their five benchmark ETFs for 2026-09-28 through 2026-10-02, using published daily OHLC/adjusted-close data. The replay now reaches **2026-10-02 under both execution models**.

At **25 bps** transaction cost:

| Strategy | Execution | Ending equity | CAGR | Max DD | Max dollar DD | Minimum equity | Max recovery |
|---|---|---:|---:|---:|---:|---:|---:|
| BASE_ROTATE_DMA250_TOP2_C5 | prior close | $228,285 | 25.96% | -68.62% | -$143,072 | $2,032 | 913 days |
| BASE_ROTATE_DMA250_TOP2_C5 | next open | $176,531 | 24.02% | -69.91% | -$101,452 | $2,374 | 873 days |
| RISK_V30_L20_DD20 | prior close | $23,294 | 9.74% | -38.94% | -$6,117 | $3,214 | 1,052 days |
| RISK_V30_L20_DD20 | next open | $24,622 | 10.11% | -38.99% | -$7,031 | $3,477 | 1,052 days |
| RISK_V30_L20_DD25 | prior close | $29,187 | 11.24% | -41.27% | -$6,468 | $3,185 | 1,043 days |
| RISK_V30_L20_DD25 | next open | $33,039 | 12.08% | -42.22% | -$7,572 | $3,455 | 980 days |
| RISK_V30_L20_DD30 | prior close | $33,781 | 12.23% | -43.65% | -$8,177 | $3,003 | 1,080 days |
| RISK_V30_L20_DD30 | next open | $29,642 | 11.35% | -47.48% | -$7,247 | $3,151 | 990 days |

The raw family rotation therefore retains dramatically more historical terminal wealth than the risk overlays, while also carrying materially larger drawdown and dollar-loss exposure.

At **0 bps**, the raw family rotation ends at approximately **$377,251 prior-close / $291,682 next-open**. At **50 bps**, it still ends at approximately **$137,744 / $106,542** respectively. The result remains positive under all modeled cost levels.

## Chronological behavior at 25 bps

| Strategy | Execution | Train CAGR | Validation CAGR | Holdout CAGR |
|---|---|---:|---:|---:|
| BASE_ROTATE_DMA250_TOP2_C5 | prior close | 15.49% | 76.80% | 175.27% |
| BASE_ROTATE_DMA250_TOP2_C5 | next open | 18.99% | 66.70% | 158.98% |
| RISK_V30_L20_DD20 | prior close | 4.54% | 25.59% | 50.30% |
| RISK_V30_L20_DD20 | next open | 5.62% | 28.68% | 53.06% |
| RISK_V30_L20_DD25 | prior close | 4.63% | 25.33% | 59.68% |
| RISK_V30_L20_DD25 | next open | 5.98% | 29.56% | 65.56% |
| RISK_V30_L20_DD30 | prior close | 4.94% | 31.36% | 66.08% |
| RISK_V30_L20_DD30 | next open | 4.72% | 24.25% | 60.83% |

These are descriptive chronological results. The 2023–2026 holdout is particularly strong and must not be interpreted as an expected future CAGR or used as a post-hoc selection target.

## Execution-model finding

The next-open model now uses the same final date as the prior-close model. On each session after the initial signal-observation session, it executes at that day's adjusted open using the prior close signal. On non-final sessions it measures through the following adjusted open. On the final session, it marks the newly executed position at that day's adjusted close because no following open exists. This preserves the terminal observation while remaining causal.

At 25 bps, moving from prior-close to next-open execution reduces the raw family-rotation ending balance from **$228,285 to $176,531** and CAGR from **25.96% to 24.02%**, while maximum drawdown changes from **-68.62% to -69.91%**.

## Endpoint provenance

The shared CI market-data builder was observed to return 2026-09-25 as its latest row despite an updated requested endpoint. The replay therefore applies the committed endpoint patch:

- leveraged ETFs: SPXL, TQQQ, SOXL, UDOW, TNA;
- benchmarks: SPY, QQQ, SOXX, DIA, IWM;
- dates: 2026-09-28 through 2026-10-02;
- adjusted close equals close for these supplied rows;
- source: published StockAnalysis daily history pages using S&P Global Market Intelligence data.

The patch is intentionally explicit and version-controlled so the replay cannot silently regress to the 2026-09-25 endpoint.

## Research gate status

This stage establishes:

1. the frozen strategy can be represented with a $5,000 account using whole shares;
2. residual cash from share rounding is manageable;
3. the risk-overlay cluster survives both prior-close and next-open execution sensitivities;
4. the overlay reduces historical drawdown substantially relative to the raw family-rotation strategy;
5. positive full/train/validation/holdout results survive 25 bps modeled transaction costs.

It does **not** establish:

- that any single overlay parameter is selected for production;
- that historical holdout performance will persist;
- that maximum drawdown is acceptable for the intended account;
- realistic intraday execution, spreads, slippage distributions, partial fills, or broker behavior;
- operational safety for unattended trading.

The next research gate should therefore focus on **execution/risk realism and walk-forward stability**, rather than another broad parameter sweep. Paper trading remains downstream of those gates.
