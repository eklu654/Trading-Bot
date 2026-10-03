# ETF family-rotation $5,000 account replay — 2026-10-03

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

The replay completed successfully. The whole-share constraint did not prevent the strategies from being implemented with a $5,000 account.

At **25 bps** transaction cost, full-period account replay results were:

| Strategy | Execution | Ending equity | CAGR | Max drawdown |
|---|---|---:|---:|---:|
| BASE_ROTATE_DMA250_TOP2_C5 | prior close | $217,586 | 25.63% | -68.62% |
| BASE_ROTATE_DMA250_TOP2_C5 | next open | $166,456 | 23.61% | -69.91% |
| RISK_V30_L20_DD20 | prior close | $22,825 | 9.62% | -38.94% |
| RISK_V30_L20_DD20 | next open | $24,038 | 9.96% | -38.99% |
| RISK_V30_L20_DD25 | prior close | $28,599 | 11.12% | -41.27% |
| RISK_V30_L20_DD25 | next open | $32,254 | 11.93% | -42.22% |
| RISK_V30_L20_DD30 | prior close | $33,102 | 12.11% | -43.65% |
| RISK_V30_L20_DD30 | next open | $28,948 | 11.20% | -47.48% |

The risk overlays therefore materially reduce the historical drawdown of the raw family-rotation strategy, but the remaining drawdowns are still substantial. The $5,000 account constraint itself is not the dominant problem; portfolio risk remains the important gate.

## Chronological split behavior

At 25 bps, the three 30%/20-session overlay variants remained positive in each chronological split under both execution sensitivities.

For example, the **next-open** model produced:

| Strategy | Train CAGR | Validation CAGR | Holdout CAGR | Full CAGR |
|---|---:|---:|---:|---:|
| RISK_V30_L20_DD20 | 5.62% | 28.68% | 52.46% | 9.96% |
| RISK_V30_L20_DD25 | 5.98% | 29.59% | 64.98% | 11.93% |
| RISK_V30_L20_DD30 | 4.72% | 24.27% | 60.26% | 11.20% |

These split results are descriptive historical observations. In particular, the very strong 2023+ holdout should not be treated as an expected future return or used to select among the variants.

## Execution-model finding

The next-open sensitivity is important because executing at the prior close is an idealized convention.

For the base strategy, moving from prior-close to next-open execution reduced the full-period 25-bps CAGR from **25.63% to 23.61%** and increased maximum drawdown from **-68.62% to -69.91%**.

For the risk-overlay cluster, next-open execution did not eliminate the observed risk reduction. At 25 bps, full-period CAGRs remained about **9.96%–11.93%**, while maximum drawdowns ranged from approximately **-39% to -47%**.

This supports continuing the risk-overlay branch, but it does **not** establish a production configuration.

## Cost sensitivity

The full-period next-open account replay also remained positive at 50 bps for all three overlay variants:

- V30/L20/DD20: 7.11% CAGR, -41.59% max drawdown;
- V30/L20/DD25: 8.97% CAGR, -44.88% max drawdown;
- V30/L20/DD30: 8.21% CAGR, -49.81% max drawdown.

The positive result under high modeled costs is useful as a friction check, but it does not model bid/ask spread variability, partial fills, market impact, trading halts, broker outages, or overnight execution gaps beyond the open-price sensitivity.

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
