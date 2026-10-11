# Family-Gate Replacement Rotation Results — 2026-10-11

## Run status
- Validated workflow run ID: `38120511756` — [success](https://github.com/eklu654/Trading-Bot/actions/runs/38120511756).
- Tested commit: `369571092deb9c031fd72ecdd9314c6173936356`.
- All family shock-gate and replacement-rotation tests passed; backtest and artifact upload succeeded.
- Artifact ID: `11695720783`, `family-specific-shock-gate-results`.
- Actual leveraged ETF/benchmark data, common calendar 2010-03-11 through 2026-10-02; performance split begins 2010-03-12.
- Fixed strategy: DMA-250/top-2/5-session cadence; family-specific -4.5% daily shock / +10% rebound gate; 0/10/25/50 bps cost stress.

## Candidates
- `BASE_ROTATE_DMA250_TOP2_C5`: frozen family rotation control.
- `FAMILY_SHOCK_GATE_45_10`: family gate exits the affected family; its slot stays cash.
- `FAMILY_SHOCK_GATE_ROTATE_45_10`: same gate, but on the existing 5-session rebalance dates selects the top two eligible, ungated families. A gated family is exited immediately, does not re-enter off-cycle, and any unfilled 50% slot remains cash.

The replacement candidate's weights are asserted to reproduce the frozen base exactly when no gate is active. It cannot exceed 100% total exposure, and a gated family slot can only be filled at the scheduled rebalance.

## Full-period results

| Cost | Frozen base final | Cash-gated final | Replacement-rotation final | Replacement wealth change vs base | Base max DD | Replacement max DD | DD improvement |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | $378,052 | $119,952 | $207,701 | -45.06% | -67.40% | -65.20% | +2.19 pp |
| 10 bps | $320,190 | $99,986 | $170,070 | -46.88% | -67.85% | -65.65% | +2.20 pp |
| 25 bps | $249,490 | $76,067 | $125,965 | -49.51% | -68.53% | -66.32% | +2.21 pp |
| 50 bps | $164,471 | $48,185 | $76,301 | -53.60% | -69.63% | -67.41% | +2.22 pp |

Replacement rotation recovers a substantial amount of the cash-gated strategy's lost wealth, but still sacrifices roughly half the base strategy's terminal wealth for only about 2.2 points of full-period maximum-drawdown improvement. It fails the preregistered requirement to retain at least 80% of base wealth while improving drawdown by at least 5 points.

At 25 bps, split behavior is mixed:
- Train: replacement ends at $17,920 vs base $21,323; max DD improves from -65.85% to -63.40%.
- Validation (2020-2022): replacement ends at $7,235 vs base $6,827; max DD improves from -65.48% to -62.34%.
- Holdout (2023-2026): replacement ends at $24,290 vs base $42,845; max DD improves from -66.50% to -53.01%.
The holdout drawdown reduction is meaningful, but the large holdout wealth penalty and weak full-period trade-off prevent promotion.

## Decision
**Reject the replacement-rotation candidate under the preregistered rule.** Do not tune shock/recovery thresholds, rebalance cadence, or top-N. The result does establish that replacement rotation is less costly than leaving gated slots in cash, but it still does not solve the risk/wealth trade-off.

Across the tested controls:
- TQQQ-only re-entry variants R1/R2/R2P/R3/R4 failed to improve the risk/wealth trade-off.
- Fixed 95%/90% TQQQ exposure caps failed the terminal-wealth criterion.
- Family-specific shock gate and replacement rotation also failed their predeclared criteria.

The evidence now argues against another threshold-based shock gate. The next step should be to audit the frozen family-rotation selector and its existing risk-overlay candidates for concentration and loss-path behavior, then decide whether any structural family allocation hypothesis remains worth one bounded test. No candidate is approved for paper/live trading.

## Superseded provisional run
Workflow run ID `38120483192` ran the replacement candidate before the final one-eligible-family cash-slot fix. Its results are superseded. This report uses only validated workflow run ID `38120511756`.

## Artifact hashes
- Benchmark panel SHA-256: `b501b17de09174db7f62ba6aae388a55a96866df976f3d204f6ebd4feaca326d`
- Bull-return panel SHA-256: `082e508cd2e60746a57224b14e57ad7d40a97320cfcc8b29d4f4a38ca8c83359`
- Base weights SHA-256: `12931192a84ea1147e0c5346ee6509e38df158c4384067055202f5ea91014a41`
- Cash-gated weights SHA-256: `b43ef299b76664827384d4a2d1864432a3e32789e373cbe399f507cefd0d0ee5`
- Replacement weights SHA-256: `24d8cfbad38e7a46005087348eaa8bc7ecc7f3080f6e1733c15e1456e34f5876`
- Gate states SHA-256: `6a0995b43a8d5549d4077a67eb886667c110c62261e92c66029627ab2a866e31`
- Summary SHA-256: `714f35ec1f835896409d37cf33edff244c8c4dbf7cfbc753a6a952317d205f80`
- Equity curves SHA-256: `f678ebf8357665018736baab4803dbcabc518c2af366d5087ce052be46ded627`
- Manifest SHA-256: `8a145646bda6a22e8bd77d3ebd7f75a094e91beae5c53fe183af7e9e20093a26`
