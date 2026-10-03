# E4/E5/E6 AI Research Gate — 2026-10-02

The E4 AI regime research workflow completed successfully on commit `169ef10255ae77bbcdd751361607d83b0d83fba3`.

## Current evidence

### E4 Ridge raw action selector

Chronological validation (2020-2022):
- CAGR: -3.83%
- Sharpe: 0.506
- Max drawdown: -88.38%
- Worst day: -38.59%

Untouched holdout (2023-09-25):
- CAGR: 53.27%
- Sharpe: 1.040
- Max drawdown: -84.25%
- Worst day: -18.03%

The model over-selected high leverage; SOXX 3x was about 34.5% of decision sessions. It is not a robust candidate despite the high holdout return.

### E4 fixed risk overlays

The combined SPY 200-DMA + VIX 80th-percentile gate reduced the full-period drawdown from roughly -88.4% to -68.2% and worst day from -38.6% to -17.0%.

The split results remain inconsistent:
- Validation: 24.5% CAGR, -59.1% max drawdown.
- Holdout: 22.2% CAGR, -51.0% max drawdown.

The controller improves failure severity but does not establish a durable advantage.

### E4c risk-aware objective

The risk-aware Ridge experiment materially improved the risk profile relative to raw AI, especially with a 1x cap:

| Policy | Validation CAGR | Validation Max DD | Holdout CAGR | Holdout Max DD |
|---|---:|---:|---:|---:|
| 1x cap | 11.19% | -39.82% | 17.30% | -31.33% |
| 2x cap | 8.58% | -66.74% | 25.88% | -56.33% |
| 3x cap | 6.23% | -70.08% | 26.97% | -56.79% |

The 1x cap is the most conservative and has much better drawdown characteristics, but its holdout return is not evidence of a superior leveraged strategy. The 2x/3x variants remain drawdown-heavy.

Cost sensitivity also shows that turnover is not the main explanation for the results: at 25 bps, the 1x policy still produced 6.28% validation CAGR and 12.74% holdout CAGR.

Stress tests:
- 1x cap: COVID -9.84%, 2022 rate-hike period -29.28%.
- 2x cap: COVID -15.21%, 2022 rate-hike period -55.52%.

### E4b HGB

The nonlinear HGB model produced:
- Validation CAGR: -3.39%, max DD -82.48%.
- Holdout CAGR: 82.12%, max DD -77.55%.

This is a classic robustness warning: substantially better holdout performance did not resolve the failed validation regime. It is not promoted.

### E5 meta-selector

E5 switched among E2, E3-square-root, SPY, and cash.

- Validation CAGR: 11.43%, max DD -40.63%.
- Holdout CAGR: 6.42%, max DD -62.47%.

The selector did not demonstrate durable holdout value and is not promoted.

### E6 binary overlay

E6 attempted to overlay AI selection on frozen E2.

- Validation: -2.58% CAGR vs E2 +5.96%.
- Holdout: 18.32% CAGR vs E2 39.10%.
- E6 did reach 100% cash during the COVID stress window, but it did not improve the later 2022 result and materially reduced returns in both evaluation splits.

E6 is not promoted.

## Research gate

The current evidence does **not** justify deploying an AI regime selector.

The strongest lesson is that model complexity is not solving the core problem. Raw return prediction tends to select excessive leverage; risk caps improve drawdown but can collapse the return advantage; meta-selection and binary overlays have not produced durable out-of-sample improvement.

The next research should therefore return to simple, interpretable controls and compare them against the strongest static controls, especially TQQQ 200-DMA/cash and buy-and-hold controls. Any new AI work should require a predefined validation improvement before being allowed to consume further research complexity.

No strategy is promoted by this document.
