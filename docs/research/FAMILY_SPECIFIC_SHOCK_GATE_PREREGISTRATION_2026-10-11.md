# Family-Specific Shock Gate Preregistration — 2026-10-11

## Hypothesis
A single family-specific shock/recovery gate may reduce the frozen leveraged-ETF family-rotation strategy's downside while allowing unaffected families to remain invested. This tests a portfolio structure the TQQQ-only experiments could not test; it is not another TQQQ-only threshold search.

## Frozen control
Use `research/test_dma_family_rotation_risk_overlay.py::base_weights()` unchanged:
- benchmark/family pairs: SPY/SPXL, QQQ/TQQQ, SOXX/SOXL, DIA/UDOW, IWM/TNA;
- DMA-250 eligibility, top-2 eligible families, rebalance cadence 5 sessions;
- bull ETFs or cash only; never hold bull and inverse from the same family;
- same common dates and same actual ETF return series.
This is the raw frozen family-rotation control, not the TQQQ B0 control.

## Fixed family-specific rule
- For each family independently, a benchmark adjusted-close daily return <= -4.5% places only that family's leveraged bull ETF weight at zero beginning next session.
- Keep that family's gate active until its benchmark closes at least +10% above the running low since the shock; re-entry can resume on the next session if the frozen base strategy still allocates to that family.
- A renewed shock while gated resets that family's running low.
- Other families' weights remain exactly as prescribed by the frozen base rotation; do not reallocate the gated weight to them. This avoids a portfolio-wide all-bull/all-cash switch.
- Signals are close-known and execute next session. No same-close execution or look-ahead.
- No threshold or window tuning.

## Evaluation and stop rule
Use $5,000 initial capital, common aligned ETF/benchmark dates, and 0/10/25/50 bps cost stress. Report full, train (through 2019), validation (2020-2022), and holdout (2023 onward) separately. Assert the ungated base is identical to the frozen base calculation.
The overlay passes only if it improves full-period max drawdown by at least 5 percentage points while retaining at least 80% of the base strategy's terminal wealth at 10 and 25 bps, without the result being isolated to one split. Otherwise reject this gate and do not tune its shock/recovery thresholds.
This uses actual ETF history from the common start date; it does not test 2000. Pre-inception data must be a separately labeled daily-reset simulation.
