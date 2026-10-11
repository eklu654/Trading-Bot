# Family-Specific Shock Gate Results — 2026-10-11

## Run and reproducibility
- Validated workflow run ID: `38120255917` — [success](https://github.com/eklu654/Trading-Bot/actions/runs/38120255917).
- Tested commit: `76854f0063a484e42577d27048e41ab917a5b1d1`.
- State-transition tests passed; backtest completed; artifacts uploaded.
- Artifact ID: `11695430351`, `family-specific-shock-gate-results`.
- Common family calendar: 4,167 sessions from 2010-03-11 through 2026-10-02; performance reporting starts 2010-03-12 after the initial signal-observation session.
- Families: SPXL/SPY, TQQQ/QQQ, SOXL/SOXX, UDOW/DIA, TNA/IWM.
- Frozen base: DMA-250 eligibility, top-2 eligible families, 5-session rebalance cadence, bull ETF or cash only.
- Shock gate: family-specific benchmark daily loss <= -4.5%; that family's weight is zero next session until a +10% rebound from its running low. Renewed shocks reset only that family's low. Other families remain at their frozen base weights; no reallocation of gated weight.
- Costs: 0/10/25/50 bps per turnover.

## Full-period results

| Cost | Frozen base ending equity | Shock-gated ending equity | Wealth change | Base max DD | Gate max DD | DD improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | $378,052 | $119,952 | -68.27% | -67.40% | -65.20% | +2.19 pp |
| 10 bps | $320,190 | $99,986 | -68.77% | -67.85% | -65.65% | +2.20 pp |
| 25 bps | $249,490 | $76,067 | -69.51% | -68.53% | -66.32% | +2.21 pp |
| 50 bps | $164,471 | $48,185 | -70.70% | -69.63% | -67.41% | +2.22 pp |

The full-period max drawdown improvement is only about 2.2 percentage points, well below the preregistered 5-point threshold, while terminal wealth falls by about 68-71%. At 25 bps, the worst rolling 252-session return improves from -63.77% to -61.96%, but this is also a modest gain relative to the wealth cost.

The gate does help in some periods: at 25 bps in the 2023-2026 holdout, max drawdown improves from -66.50% to -47.27%, while ending equity falls from $42,845 to $31,134. In 2020-2022 validation, ending equity falls from $6,827 to $4,751. The effect is not consistent enough across splits to justify the opportunity cost.

## Decision
**Reject the family-specific shock gate under the preregistered rule.** It demonstrates that family-specific controls can reduce drawdown without shutting off the entire portfolio, but this particular rule's wealth penalty is far too large. Do not tune the -4.5% or +10% thresholds.

The prior fixed-exposure risk-budget tests also failed: 95% exposure cut B0 terminal wealth by about 20% for only 2.2 points of drawdown improvement; 90% exposure cut wealth by about 37% for 4.6 points. The TQQQ-only re-entry candidates R1/R2/R2P/R3/R4 were also rejected. These results argue against repeatedly layering simple shock or exposure scalars onto the current controls.

## Next research direction
Do not expand this gate's parameter search. Before proposing another rule, audit the frozen family-rotation account replay and its existing risk-overlay results at the event level, especially the large drawdown/low-equity intervals and recovery delays. Then define one distinct family-allocation hypothesis only if the audit identifies a specific mechanism that the current rule fails to address. Continue to report actual history separately from any pre-inception synthetic daily-reset stress test; this experiment does not test the 2000 crash.

## Artifact hashes
- Benchmark panel SHA-256: `91e99d8158c3328b739da8f0289b7f7b5365567af7cc1367b182b12a471adc25`
- Bull-return panel SHA-256: `9a3fc474c36da695b2d68d3be772eff4d9d5eabb679983d860239d544c6bb633`
- Base weights SHA-256: `12931192a84ea1147e0c5346ee6509e38df158c4384067055202f5ea91014a41`
- Overlay weights SHA-256: `b43ef299b76664827384d4a2d1864432a3e32789e373cbe399f507cefd0d0ee5`
- Gate states SHA-256: `6a0995b43a8d5549d4077a67eb886667c110c62261e92c66029627ab2a866e31`
- Summary SHA-256: `07f6960df020027be9ecd1b53d266d7c02736da6f51095185ace8645a38d687e`
- Equity curves SHA-256: `a13f3a216587deb39ce3d0c4c61ad8f5581f9fd37bb4814a3990a4d90e5d549e`
- Manifest SHA-256: `cd11e6c288addb385e5d684cf24f879272aef717ab6d54dbd5067aa662874c2a`

## Failed initial attempt
Workflow run ID `38120192425` failed because the dataset-generation step was missing; the runner did not have the required `data/research/*_daily.csv` files. The workflow was corrected to restore/build the historical dataset and apply the pinned endpoint patch before running. The successful run cited above includes that fix.


## Event-level attribution follow-up

Using the same frozen base weights, ETF returns, benchmark panel, and equity path, the six deepest completed/observed drawdown episodes show that losses are concentrated in a few family/market episodes:

| Base peak | Trough | Max DD | Equity drop | Largest family contributions to dollar loss |
|---|---|---:|---:|---|
| 2021-12-27 | 2023-03-13 | -67.40% | -$73,094 | SOXL family -$33,518; SPXL -$19,666; TQQQ -$9,268 |
| 2020-02-19 | 2020-03-12 | -65.48% | -$23,378 | SOXL -$12,719; TQQQ -$10,658 |
| 2024-07-10 | 2025-04-08 | -64.94% | -$103,339 | SOXL -$54,894; TNA -$17,672; TQQQ -$18,105 |
| 2015-03-02 | 2016-06-27 | -63.66% | -$8,923 | SOXL -$3,778; TQQQ -$2,727 |
| 2011-04-29 | 2011-12-28 | -59.23% | -$3,127 | TQQQ -$1,810; TNA -$593; UDOW -$309 |
| 2018-03-12 | 2019-06-03 | -50.00% | -$13,017 | UDOW -$3,972; SOXL -$3,303; TQQQ -$3,227 |

The family shock gate removed exposure on some very bad sessions (notably TQQQ/SOXL in the 2020 crash), but during the largest 2021-2023 and 2024-2025 drawdowns it removed SOXL exposure on only 11 and 13 days, respectively, while SOXL was responsible for roughly 46% and 53% of each episode's dollar loss. This is a selection/timing interaction: a gate can only help when its family is actually selected, and the base rotation's rebalance/ranking schedule can leave much of a prolonged family drawdown outside the gate's active overlap.

The next distinct hypothesis should therefore test **what happens to a gated family slot**, not tune the shock threshold: at the existing 5-session rebalance dates only, replace a gated top-2 family with the next-highest-ranked eligible, ungated family; keep the family-specific shock gate unchanged and leave the slot in cash if fewer than two families qualify. This preserves the base cadence and the no-same-family bull/inverse rule. Preregister this as a separate experiment before running it.
