# Trading-Bot Research — Current State

**Last updated:** 2026-10-09 UTC  
**Active investigation:** Determine whether the canonical QQQ shock/recovery strategy's slow-bear weakness justifies a structural overlay while protecting terminal wealth.  
**Starting capital:** $5,000.

## User's direction

Start from the reproducible ~$4.04M candidate and organically let evidence establish strengths, weaknesses, and whether any overlay is warranted. Do not block progress on reconstructing the separate historical ~$3.3M anti-fakeout strategy.

## Frozen baseline

**Rule ID:** `qqq_shock45_recovery10_actual_tqqq_v1`

- Signal: QQQ adjusted-close daily return <= -4.5%.
- Defense: target 0% TQQQ exposure from the next open after the trigger close.
- Recovery: track post-trigger adjusted-close low; re-enter at next open after a close is >=10% above that low.
- Otherwise hold 100% TQQQ.
- Accounting: overnight return belongs to the position held before open execution; intraday return belongs to the position after open execution.
- No DMA, Fed, MACD, golden-cross, macro, inverse ETF, or AI filter is part of the baseline.
- $5,000 initial equity; actual-TQQQ window 2010-02-11 through 2026-10-07.

Every candidate comparison keeps this baseline unchanged.

## Baseline verification and modern stress results

- Same-input daily curve reconciliation passed: [run 37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700). Shared and independent engines matched every daily return/equity value and all nine events.
- Frozen input SHA-256: `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.
- Same-input baseline: **$4,040,313.79**, CAGR 49.49%, max DD -73.53%; TQQQ buy-and-hold **$2,094,668.95**, CAGR 43.70%, max DD -81.66%.
- Reports: [first stress scorecard](CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md) and [stress windows / slow-bear audit](CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md).
- Period returns independently compounded within each window: 2010–14 baseline +895.0% vs buy-hold +865.3%; 2015–19 +569.6% vs +434.0%; 2020–21 +325.6% vs +284.4%; 2022–24 +42.3% vs -1.4%; 2025–2026-10-07 +100.2% vs +114.4%.
- Main weakness: QQQ fell -15.6% in 2010 and -16.1% in early 2016 without a -4.5% daily shock; in 2022 the first shock arrived 77 sessions after the -5% drawdown episode began.

## Candidate 1 — Fed-paused × below 200-DMA: REJECTED

- Workflow: [37885392208](https://github.com/eklu654/Trading-Bot/actions/runs/37885392208).
- Report: [Fed-paused/200-DMA result](CANONICAL_SHOCK_RECOVERY_FED_DMA_OVERLAY_RESULT_2026-10-09.md).
- Ending wealth fell ~28% versus baseline and max drawdown did not improve. It fired only during brief 2016/2019 corrections and missed 2022 entirely.

## Fed-state attribution

- Workflow: [37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208).
- Report: [Fed state attribution](CANONICAL_SHOCK_RECOVERY_FED_STATE_ATTRIBUTION_2026-10-09.md).
- 2022 drawdown began 2022-01-13 with Fed state NEUTRAL. TIGHTENING_ACTIVE began 2022-03-18; first shock was 2022-05-05. TIGHTENING_PAUSED began only 2023-10-26, after QQQ reclaimed the 200-DMA.

## Candidate 2 — Fed-active × below 200-DMA: PARTIAL-EXPOSURE TRADE-OFF

- Binary test: [run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946); [result report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md).
- Exposure sensitivity: [run 37886436961](https://github.com/eklu654/Trading-Bot/actions/runs/37886436961); [report](CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_EXPOSURE_SENSITIVITY_2026-10-09.md).
- Rule: enter when QQQ is below the existing 200-DMA and previous-session Fed state is TIGHTENING_ACTIVE; exit when QQQ closes at/above the 200-DMA. Baseline shock defense independently overrides to 0%.
- Same-run ending balances: baseline $4.040M; 0% overlay exposure $3.675M; 25% $3.933M; 50% $4.087M; 75% $4.125M; buy-and-hold $2.095M.
- 50% overlay exposure ends ~$47k above baseline while improving max DD from -73.53% to -61.19% and worst rolling 252-session return from -72.64% to -59.88%.
- 75% overlay exposure ends ~$84k above baseline while improving max DD to -67.65% and worst rolling-year return to -66.56%.
- 2022 calendar loss: -69.83% baseline, -57.21% at 50% overlay exposure, -63.73% at 75%.
- The main opportunity cost is 2018–2019 trend chop. Leave-one-episode-out counterfactuals show the 2018-12-04 to 2019-02-04 episode conditionally cost ~$794k at 0% overlay exposure because it stayed defensive after the baseline's 2019-01-07 recovery decision. The 2022-04-05 to 2023-01-25 episode conditionally contributed ~$1.50M at 0% overlay exposure. Conditional effects are not additive.
- 50% and 75% remain working comparison candidates, not selected or validated. This is in-sample development evidence.

## Candidate 3 — Existing macro-regime overlay: REJECTED for current slow-bear objective

- Workflow: [37886806226](https://github.com/eklu654/Trading-Bot/actions/runs/37886806226).
- Report: [actual-TQQQ macro overlay result](CANONICAL_SHOCK_RECOVERY_MACRO_OVERLAY_RESULT_2026-10-09.md).
- Existing frozen classifier applied to actual TQQQ with an additional conservative month-start availability lag. Ending balances: baseline $4.040M; macro-light $3.308M; macro-medium $2.706M; macro-hard $2.180M.
- All variants retained the baseline's -73.53% max drawdown and -72.64% worst rolling-year return. The classifier stayed STRUCTURAL_EXPANSION through 2022 and failed to detect the target bear. It reduced wealth without solving the main failure mode.

## Historical signal-only audit

- Workflow: [37887083424](https://github.com/eklu654/Trading-Bot/actions/runs/37887083424).
- Report: [historical signal-only stress audit](CANONICAL_SHOCK_RECOVERY_HISTORICAL_SIGNAL_AUDIT_2026-10-09.md).
- S&P 500 proxy: the 1973–1974 episode fell ~48.2% peak-to-trough without any -4.5% daily-shock trigger. The 1987 episode did trigger, eight sessions after the -5% episode start.
- QQQ signal-only: the 2000–2002 dot-com bear fell ~83.0% peak-to-trough. The daily shock/recovery rule fired repeatedly. The Fed-active × 200-DMA condition activated only intermittently early in the decline and did not remain defensive through the full bear as the Fed state shifted to EASING.
- These are signal/index diagnostics, not TQQQ returns. No actual TQQQ result is claimed before its inception.

## Next actions

1. Keep the compact actual-TQQQ comparison set: baseline, Candidate 2 at 50% overlay exposure, and Candidate 2 at 75% overlay exposure. Keep 0%/25% as sensitivity points.
2. Freeze the comparison and write down a chronological validation protocol. The entire modern sample has already been inspected; no historical slice can now be called an untouched holdout. Any future rule change becomes a development candidate and requires a future untouched holdout.
3. Use historical signal-only studies to understand whether these rules would have recognized prior regimes, but do not convert proxy signals into actual TQQQ performance.
4. Do not change the 200-DMA exit rule after seeing the 2018 result and then call it validated. The missed 2019 recovery is a known trade-off to assess, not an automatic reason to optimize.
5. No broad indicator fishing, DMA-length sweep, re-entry-delay search, AI layer, or paper trading yet.

## Result labels

- **SUPPORTED:** replicated on identified data/execution without a known material methodological defect.
- **WORKING:** comparison anchor or candidate, not proven robust/generalizable.
- **PROVISIONAL:** replicated with unresolved input or implementation differences.
- **REJECTED:** known defect or failed criterion invalidates the claimed result.
- **UNRESOLVED:** insufficient evidence.

Current baseline status: **WORKING**. Candidate 2 at 50%/75% overlay exposure is **WORKING TRADE-OFF, NOT SELECTED**. Numerical reproduction is supported; generalization across major downturn types remains unresolved.

## Validation protocol frozen — 2026-10-09

- Protocol: [canonical shock/recovery validation protocol](CANONICAL_SHOCK_RECOVERY_VALIDATION_PROTOCOL_2026-10-09.md), committed at `fa3e491cf973ca680ea869c4664cf63ef516fd28`.
- The protocol formalizes the unchanged B0 baseline, F50 and F75 development candidates, F00/F25 sensitivity controls, data/causality assertions, required cost and segment scorecards, candidate gates, and what does/does not count as out-of-sample evidence.
- Critical honesty rule: the full 2010–2026 sample has already been inspected. Historical subperiods are retrospective stability diagnostics, not untouched holdouts. Only a genuinely frozen prospective test can become new out-of-sample evidence.
- Candidate advancement gates: at least 95% of baseline ending wealth after 25 bp exposure-change costs; at least 5 percentage points improvement in max drawdown and worst rolling 252-session return; no material unaccounted deterioration in COVID/2018 windows; and evidence the benefit is not entirely one episode.
- No candidate selected. B0 remains WORKING CONTROL; F50/F75 remain WORKING DEVELOPMENT CANDIDATES; the existing macro classifier remains REJECTED for the current objective. AI and paper trading remain deferred.
- Next engineering task: a single workflow/run that freezes one aligned QQQ/TQQQ/Fed input set, runs B0/F50/F75 from it, independently checks causality/accounting, and emits one comparable artifact set. Existing sensitivity output is useful, but its market-input hash differs from the canonical baseline hash; do not describe its dollar figures as exact same-input comparisons until that is reconciled.

## Frozen-input overlay comparison implementation — 2026-10-09

- New script: [canonical_shock_recovery_frozen_overlay_comparison.py](../../research/canonical_shock_recovery_frozen_overlay_comparison.py), commit `1c71e82018d8f2001af0e1e9dbc6225cfbed3e74`.
- New workflow: [canonical-shock-recovery-frozen-overlay-comparison.yml](../../.github/workflows/canonical-shock-recovery-frozen-overlay-comparison.yml), commit `9459ba314a093cc56e19be32c80fcb0ab167682c`.
- Workflow run: [37888705794](https://github.com/eklu654/Trading-Bot/actions/runs/37888705794). At checkpoint it was in progress during dependency installation; no result is claimed yet.
- Intended behavior: freeze aligned QQQ/TQQQ market input once using the existing same-input reconciler; derive B0, F00/F25/F50/F75, and buy-and-hold from those exact rows; download/map the Fed state once with existing lag; independently reconcile B0 execution returns; emit daily equity/exposure, event ledger, Fed/DMA transitions, chronological subperiod scorecard, transaction-cost sensitivity, and a hash manifest.
- Important distinction: this is a same-run comparison on one frozen input. Its downloaded price snapshot may differ from earlier runs because vendor adjusted-price histories can be revised. Use its own manifest/hash for its conclusions; do not claim byte-identical inputs across separate workflow runs.
- No candidate selected. Inspect the actual workflow result and artifacts before interpreting the output. If it fails, preserve the failure, fix the code, and rerun rather than inferring results.

## Frozen-input comparison first pass and completeness correction

- First combined workflow [37888705794](https://github.com/eklu654/Trading-Bot/actions/runs/37888705794) passed and emitted a single-input comparison artifact (market SHA-256 `922ca85860b505a949ec4191a9ed016afe56f1963f87fa16a3aa3547a2c341d2`, 4,189 rows, 2010-02-11–2026-10-07).
- First-pass figures were inspected only as an implementation check. Before treating them as a complete protocol scorecard, I found the artifact omitted cost-adjusted worst rolling-year return and leave-one-overlay-episode-out diagnostics, both required by the frozen protocol.
- Added those diagnostics to the script and included the new episode-contribution CSV in the workflow artifact list. Code commit: `191490af99a1cefa1b46c0012b9b24c194b1e0b0`; workflow commit: `1083830aece25d82ed79ba7a1b19a258ef512617`.
- Corrected workflow run: [37888844274](https://github.com/eklu654/Trading-Bot/actions/runs/37888844274). It was pending at this checkpoint; do not treat the corrected artifact as available until the run completes successfully.
- First-pass data is development-only, because the same modern sample has been inspected. No winner is selected and no live/paper-trading approval follows from this work.

## Corrected frozen-input comparison completed — 2026-10-09

- Corrected workflow passed: [run 37888844274](https://github.com/eklu654/Trading-Bot/actions/runs/37888844274), artifact ID `11597820453`.
- Results and gate decision: [frozen-input overlay comparison report](CANONICAL_SHOCK_RECOVERY_FROZEN_OVERLAY_COMPARISON_RESULT_2026-10-09.md).
- Same run/hash used for all candidates: market input `e79530cf7bda1557adee2eacbdf9b8621f8cde16daf7c533a444be46c68ee2c0`; lagged Fed state `cb6d59cc792ceedfd561a4e64780b4807192a546f7fc9d0d38eb60b4d1de0ea1`; 4,189 rows from 2010-02-11 through 2026-10-07.
- At 25 bp per full exposure change: B0 $3.853M; F50 $3.830M; F75 $3.899M. F50/F75 both clear the protocol's numerical 95%-wealth and 5-percentage-point downside-improvement thresholds in this run.
- Remaining blocker is not numerical reproduction but concentration/generalization: F50's conditional terminal contribution for 2022-04-05–2023-01-25 was about +$1.066M and its 2018-12-04–2019-02-04 episode about -$410k; F75's corresponding effects were about +$613k and -$200k. These counterfactual effects are non-additive; the apparent advantage is highly episode-sensitive. Candidate selection remains open.
- B0 remains WORKING CONTROL. F50/F75 remain WORKING DEVELOPMENT CANDIDATES only. No live/paper-trading approval. The full modern sample has been inspected and is not an untouched holdout.

## Candidate concentration gate evaluated

- The 2022-04-05–2023-01-25 overlay episode is the dominant positive counterfactual for F50/F75. Removing it in the leave-one-overlay-episode-out diagnostic lowers F50 to about $3.022M and F75 to about $3.511M, both below B0's ~$4.040M on the same artifact path.
- Since episode counterfactual effects are non-additive, this is a sensitivity diagnostic rather than a causal profit decomposition. It is still sufficient to mark the protocol's episode-diversification gate **FAILED in this retrospective screen**.
- F50/F75 pass the numerical 25 bp wealth/downside screen but do not advance under the frozen multi-gate protocol. They remain documented diagnostic candidates, not recommended strategies. Do not optimize away the 2018–2019 losses using this same full-sample evidence and then call the revision validated.
- Updated report: [frozen-input overlay comparison result](CANONICAL_SHOCK_RECOVERY_FROZEN_OVERLAY_COMPARISON_RESULT_2026-10-09.md).

## Regression tests after comparison additions

- Added synthetic unit tests for episode-contribution counterfactual behavior and the summary metric calculation in `research/test_frozen_overlay_comparison.py`.
- Main research CI passed on commit `241131edd2cf7de64e3f543b4e7898227aed6233`: [research-tests run 37889166998](https://github.com/eklu654/Trading-Bot/actions/runs/37889166998). This includes `PYTHONPATH=. pytest -q` and the existing three-layer event-attribution script.
- The dedicated corrected comparison workflow also passed on code/workflow commit `1083830aece25d82ed79ba7a1b19a258ef512617`: [run 37888844274](https://github.com/eklu654/Trading-Bot/actions/runs/37888844274).

## Fed-versus-DMA ablation initiated

- Predeclared question and constraints: [Fed-vs-DMA ablation plan](CANONICAL_SHOCK_RECOVERY_FED_VS_DMA_ABLATION_PLAN_2026-10-09.md), committed at `a4d3eb4228747d83df310eb062593b3c4a79c628`.
- The same-input comparison script now adds D50/D75: 50%/75% TQQQ exposure below the existing 200-DMA without a Fed entry filter, compared against F50/F75 with the active-Fed gate. B0 and buy-and-hold remain controls. No new thresholds or DMA lengths.
- Added a synthetic test for the DMA-only entry state. Code commit: `72480d9356bc9258b6e583eb0d4f9320609c1039`; test commit: `9b29ba1eb3a6c7becee38437477fb6fd5582b266`.
- The new comparison and regression workflows are triggered by these commits. No ablation result is claimed yet; all data remains retrospective development data.

## Fed-versus-DMA ablation completed

- Same-frozen-input comparison passed: [workflow run 37889360594](https://github.com/eklu654/Trading-Bot/actions/runs/37889360594), artifact `11597189873`.
- Result report: [Fed filter vs. DMA-only overlay](CANONICAL_SHOCK_RECOVERY_FED_VS_DMA_ABLATION_RESULT_2026-10-09.md).
- On the same 4,189 market rows, the 50%/75% DMA-only variants ended at ~$1.988M / ~$2.940M, versus ~$4.087M / ~$4.125M for the active-Fed-gated F50/F75 variants. The DMA-only state was active for 600 sessions versus 337 sessions for the Fed-gated state. The resulting target exposure was below 100% for 701 sessions in D50/D75 versus 473 sessions in F50/F75, because the baseline's own 0% shock-defense state overlaps some overlay sessions.
- At 25 bp cost, D50/D75 ended ~$1.746M / ~$2.690M, so both fail the wealth-retention gate. The Fed condition adds meaningful selectivity in this sample; it is not redundant with the 200-DMA.
- Interpretation remains cautious: F50/F75 benefits are concentrated in the single modern 2022 tightening bear and fail the episode-diversification gate. D50/D75 fail the wealth-retention gate. No strategy selected; B0 remains the control.
- Regression CI passed after adding the DMA-only unit test: [research-tests run 37889389620](https://github.com/eklu654/Trading-Bot/actions/runs/37889389620).

## Final metadata cleanup

- Updated the comparison script's docstring and manifest candidate list to include the new D50/D75 ablation candidates. This is metadata-only; it does not alter signals, prices, execution, or results.
- Commit: `5b207d1681b08e6f9872af406110d467a7daa341`. The dedicated comparison workflow and regression tests are triggered again; prior ablation run [37889360594](https://github.com/eklu654/Trading-Bot/actions/runs/37889360594) remains the source for the reported numbers until the metadata-only rerun completes.

## Final checks for this work block

- Metadata-corrected same-input comparison workflow passed: [run 37889563456](https://github.com/eklu654/Trading-Bot/actions/runs/37889563456), code commit `5b207d1681b08e6f9872af406110d467a7daa341`.
- Full repository research-tests passed on the latest research code plus report updates: [run 37889605031](https://github.com/eklu654/Trading-Bot/actions/runs/37889605031), commit `32e250c8044efa00c65d780b4176e157cdcb19ca`. This includes pytest and the existing event-attribution script.
- The report's final quantitative conclusion remains: the Fed filter substantially outperforms the same-exposure DMA-only ablation on terminal wealth in this sample, but F50/F75 fail the episode-diversification gate and D50/D75 fail wealth retention. No strategy selected; no paper/live trading approved.


## Next experiment — historical real-index Fed/DMA defense test

- User asked whether the defensive mechanic can be tested in earlier periods without reconstructing TQQQ. Decision: yes; test signal timing against actual daily Nasdaq Composite index data (from its available 1971 history) plus actual historical Fed-rate observations, with no leverage simulation and no pre-2010 TQQQ wealth claims.
- Plan: [historical real-index Fed/DMA defense test](HISTORICAL_REAL_INDEX_FED_DMA_DEFENSE_TEST_PLAN_2026-10-09.md), committed 2026-10-09 (commit `a496a6d2bd583fa9bd5a3c92e9218c221e0650c5`).
- Frozen rule to test: index close below 200-session SMA AND one-session-lagged Fed state `TIGHTENING_ACTIVE`; sticky defense persists until index closes back at/above 200-DMA. Reuse the exact current Fed-state builder if available; do not silently invent a new definition if not.
- Primary real-price proxy: Nasdaq Composite, not QQQ and not TQQQ. Broad-market cross-check: S&P 500 where verified daily data are available. Policy source: FRED/Board of Governors daily DFF; source references and guardrails are in the plan.
- Required outputs: all defense entry/exit dates, duration, drawdown at entry, forward 21/63/126/252-session index outcomes, missed rebounds, and Fed-only / DMA-only / combined ablations. Also run an index-only exposure backtest on actual index returns: 100% normal exposure, 0/25/50/75% index exposure during defense, remainder in an explicitly documented actual Treasury-bill cash proxy plus zero-yield sensitivity. Hash inputs and preserve machine-readable artifacts.
- This experiment tests whether the signal generalizes across historical regimes. It cannot establish pre-inception TQQQ portfolio wealth or prove that the overlay improves TQQQ terminal wealth.

## First real-index historical Fed/DMA defense run completed

- Successful workflow: [run 37892712141](https://github.com/eklu654/Trading-Bot/actions/runs/37892712141), artifact ID `11599435954`, code commit `545213092ddf7ec00977b790ecdd7448daa62eed`.
- Result report: [historical real-index Fed/DMA defense results](HISTORICAL_REAL_INDEX_FED_DMA_DEFENSE_RESULT_2026-10-09.md). Full daily open/close inputs, state series, event transitions, episode returns, summary, and hashes are preserved in the workflow artifact.
- Tested actual Nasdaq Composite and S&P 500 price-index OHLC data from 1971 through 2026-10-08; 14,036 Nasdaq sessions and 14,060 S&P sessions. No synthetic leverage and no pre-inception TQQQ wealth claims.
- Causal timing was corrected to apply close-derived defense changes at the next session open: prior exposure applies to the overnight gap, new exposure applies intraday. The artifact contains open and close series.
- First-pass whole-history results with lagged TB3MS cash: Nasdaq combined defense at 0% exposure ended at 779.87x versus 271.93x unprotected, with max drawdown -51.26% versus -77.93%; S&P ended at 100.69x versus 85.19x, with max drawdown -27.07% versus -56.78%. Results are unleveraged price-index outcomes, exclude dividends, and are not TQQQ performance.
- Zero-yield cash sensitivity is material: Nasdaq combined 0% defense still beat unprotected terminal wealth (394.42x vs 271.93x), but S&P combined 0% defense did not (51.91x vs 85.19x), though drawdown was substantially lower. No universal terminal-wealth conclusion yet.
- Crucial limitation: the 1971+ run uses a historical DFF net-rate-change proxy (active if DFF is >1 bp above its 90-calendar-day prior value) because the modern target-range series does not cover the 1970s. This is not identical to the current target-rate lifecycle state builder. Next required work: improve the historical Fed proxy using explicit hike/cut events, compare state dates with the current target-rate builder over overlapping years, and test total-return index data/cost sensitivities.
- No defensive overlay selected and no paper/live trading approved. Treat this as encouraging signal-mechanic evidence, not proof of TQQQ strategy superiority.


## Fresh DMA-overlay discovery pass — 2026-10-09

- User explicitly instructed a zero-assumption restart of defensive-feature discovery, starting from the canonical QQQ **-4.5% daily shock / +10% from post-shock low recovery** rule and adding several DMA candidates, including 50/100/200 sessions. Correction: the trigger is **4.5%, not 45%**.
- Canonical baseline is specified in [FAILED_BOUNCE_CANONICAL_STRATEGY_SPEC.md](FAILED_BOUNCE_CANONICAL_STRATEGY_SPEC.md): $5,000 initial capital, actual TQQQ only for the live period, QQQ adjusted-close signals, close signal executes next open, no DMA/Fed layer in baseline. Recorded ~$4.04M is a working reference, not an independently certified guarantee.
- Created [EXPLORATORY_DMA_OVERLAY_SWEEP_2026-10-09.md](EXPLORATORY_DMA_OVERLAY_SWEEP_2026-10-09.md) (commit `d40e254b0bc6c7afbc7fd887ca4442ce492b3f25`). It freezes an exploratory grid of 20/30/40/50/60/75/100/125/150/175/200/250 sessions and separates below/above state, cross-down/up, slope, and price-distance diagnostics. All candidates must be reported to expose multiple-comparison bias; no winner is selected yet.
- Repository search also found pre-existing `research/tqqq_structural_shock_defense_matrix.py`. Its current design tests structural DMA relationships (100/150/200; fast DMA 50/100) plus 63-session return, 252-session drawdown, and VIX thresholds. This is a prior experiment, not assumed to be the desired final mechanic. Audit its outputs and provenance separately; do not conflate it with the newly frozen simple DMA sweep.
- The new plan is committed, but its sweep has **not yet been executed**. Next action: implement/run a reproducible baseline-matched sweep with machine-readable results and hashes, then record all outcomes and CI status here. Prior DMA rejection and Fed/DMA results remain preserved; no candidate promoted and no paper/live trading approved.


## Structural shock defense matrix rerun results — 2026-10-09

- GitHub Actions run [37904930480](https://github.com/eklu654/Trading-Bot/actions/runs/37904930480) completed successfully; job `study` passed and uploaded artifact `tqqq-structural-shock-defense` (artifact ID 11604405340; SHA-256 reported by GitHub: `83a8c6ca5e98b2430313cf2a713295dd4b1435a19ae0ac2c2668e26b7fec1316`). The CSV contains 288 rows: 144 parameter combinations for actual TQQQ and 144 for synthetic QQQ 3x.
- Top actual TQQQ row: ending balance **$426,534.09** from $5,000, CAGR 30.62%, max drawdown -65.18%; structural DMA 100, fast DMA 50, 63-session return trigger -20%, 252-session drawdown trigger -25%, VIX trigger 30, structural exposure 25%.
- Top synthetic QQQ 3x row: ending balance **$2,377,711.47** from $5,000, CAGR 25.05%, max drawdown -91.21%; structural DMA 100, fast DMA 50, 63-session return trigger -20%, 252-session drawdown trigger -20%, VIX trigger 30, structural exposure 25%. This is a synthetic series, not actual TQQQ and its extreme drawdown illustrates the model risk.
- Both figures are best-in-grid exploratory results selected across 144 combinations per source on the same evaluation history; they are subject to multiple-comparison/selection bias and are not independently validated. The CSV reports empty dot-com/GFC fields for actual TQQQ because TQQQ did not exist then. Do not present these as proof the matrix beats the canonical 4.5%/10% shock-recovery baseline; the strategy and benchmark differ.
- Repository visibility checked via GitHub API at 2026-10-09: `private=false`, `visibility=public`, repository created 2026-09-27T11:20:05Z. Creation time does not reveal when visibility was changed; available metadata does not establish who changed it or when. User should review repository history for committed secrets/data before deciding privacy.


## Combined canonical + structural matrix — 2026-10-09

- Implemented `research/canonical_plus_structural_matrix.py` and workflow `.github/workflows/canonical-plus-structural-matrix.yml`.
- Combined exposure is explicitly `min(B0 shock/recovery signal, overlay signal)`; the matrix cannot add exposure or cancel B0's defensive state.
- Compared structural+fast-shock matrix and fast-shock-only ablation over the previous 144-configuration grid, with B0 controls, actual TQQQ on the aligned live-fund window, and a separately labeled hypothetical 3x QQQ proxy for pre-TQQQ history.
- Experiment note: [CANONICAL_PLUS_STRUCTURAL_MATRIX_EXPERIMENT_2026-10-09.md](CANONICAL_PLUS_STRUCTURAL_MATRIX_EXPERIMENT_2026-10-09.md).
- Workflow run: https://github.com/eklu654/Trading-Bot/actions/runs/37912413316. At checkpoint, run was in progress during dependency installation; no combined performance results are claimed yet. Inspect the completed artifact and update the experiment note before interpreting any winner.


### Combined canonical + structural matrix results — 2026-10-09

- Completed successfully: [workflow run 37912413316](https://github.com/eklu654/Trading-Bot/actions/runs/37912413316), artifact ID `11607472004`, SHA-256 `8714513d2f7390f562cdddfcaf6e228ef0e187bfcc5ac4bd5dabe805afef3afd`.
- Full report: [combined matrix results](CANONICAL_PLUS_STRUCTURAL_MATRIX_RESULTS_2026-10-09.md).
- Actual TQQQ baseline $4.040M. Best matrix-overlay row by terminal balance: $727,050 (structural DMA 150, fast DMA 100, return -20%, drawdown -20%, VIX 30, 25% structural exposure); max drawdown improved to -59.47%, but COVID crash/rebound window returned -8.63% versus B0 +24.58%. The best drawdown row ended $579,625 with max drawdown -57.24%. Fast-only variants were worse for ending balance.
- Decision: reject this sticky matrix family as a production candidate; no more parameter sweeping of the same rule. It improves drawdown by sacrificing far too much compounding and COVID rebound capture.
- Historical 1999+ outputs remain a hypothetical 3x QQQ proxy, not actual TQQQ returns. Proxy B0 drawdown approached -99.4%, so do not interpret it as calibrated fund simulation.
- Root cause hypothesis to test next: the fast-shock override remains hard-defensive until QQQ closes above the structural DMA, even after the shock condition fades. A recovery-aware/non-sticky ablation is more useful than more threshold tuning.


### Next diagnostic experiment — sticky-state ablation — 2026-10-09

- Frozen representative parameters; no new grid search: structural DMA 150, fast DMA 100, 63-session return -20%, 252-session drawdown -20%, VIX 30, structural exposure 25%.
- Compared B0 with (1) original sticky hard defense, (2) hard 0% only while the fast-shock condition is currently true while structural 25% defense remains sticky, and (3) fully daily/non-sticky structural and fast-shock conditions.
- All candidates remain `min(B0, overlay)`; none can increase exposure above B0.
- Experiment plan and audit trail: [CANONICAL_STRUCTURAL_STATE_ABLATION_2026-10-09.md](CANONICAL_STRUCTURAL_STATE_ABLATION_2026-10-09.md). Workflow will record results before interpretation.


### Structural state ablation results — 2026-10-09

- Workflow passed: [run 37912719777](https://github.com/eklu654/Trading-Bot/actions/runs/37912719777); artifact ID `11606304467`, SHA-256 `0bf75ad8bf27a72d004b0700cd298cecf49b274de65d907f746c28f30de4ee12`.
- Full result table: [state ablation results](CANONICAL_STRUCTURAL_STATE_ABLATION_RESULTS_2026-10-09.md).
- Actual-TQQQ results at the fixed representative setting: B0 $4.040M; original sticky overlay $727k; hard-nonsticky $892k; fully daily/non-sticky $1.355M. Max drawdown improves from -73.53% to between -57.81% and -60.49%, but all three overlays turn B0's +24.58% COVID window into roughly -8.6% to -9.9% and materially reduce long-run wealth.
- Decision: sticky hard defense is not the only problem. Reject this structural matrix family and stop tuning its thresholds. Next step is episode attribution around B0 recovery decisions, especially COVID and 2022, before considering any narrowly scoped recovery-aware candidate.


### Next step: interval attribution — 2026-10-09

- Added a no-search attribution run to identify contiguous dates when the matrix overlay cuts exposure after B0 has returned to 100%, with leave-one-interval-out terminal-wealth counterfactuals.
- Frozen representative settings; no threshold tuning. Report/plan: [CANONICAL_STRUCTURAL_OVERLAY_ATTRIBUTION_2026-10-09.md](CANONICAL_STRUCTURAL_OVERLAY_ATTRIBUTION_2026-10-09.md).
- Workflow: `.github/workflows/canonical-structural-overlay-attribution.yml`; awaiting run artifact before adding conclusions.


### Recovery-event quality audit — 2026-10-09

- Added a QQQ-only event study to test whether the matrix's structural/fast-shock conditions are present at canonical +10% recovery decisions and whether those recoveries later fail over 20/60/120/252 sessions.
- This is signal diagnostics only; it does not claim pre-inception TQQQ returns or constitute a trading backtest. No thresholds are being searched.
- Frozen audit plan: [CANONICAL_RECOVERY_EVENT_QUALITY_2026-10-09.md](CANONICAL_RECOVERY_EVENT_QUALITY_2026-10-09.md). Workflow artifact to be reviewed before interpreting results.


### Structural overlay attribution result — 2026-10-09

- Corrected successful run: [37913116036](https://github.com/eklu654/Trading-Bot/actions/runs/37913116036), artifact ID `11606389641`, digest `1f78aae47b60f8a4983208b6dd845cfb3058299ac3844797096dd205952480a7`. Detailed intervals and caveats are in [the attribution report](CANONICAL_STRUCTURAL_OVERLAY_ATTRIBUTION_2026-10-09.md).
- Main opportunity cost: the matrix is defensive on the same close that B0 triggers re-entry. It blocks B0 re-entry on 2019-01-07 and 2020-03-26 (COVID), with conditional leave-one-interval-out costs of roughly $140k–$213k for the 2019 interval and $230k–$454k for the COVID interval, depending on state variant. These conditional effects are non-additive.
- The overlay also helps in selected 2022 intervals, confirming a context-classification problem rather than a simple sticky-state bug. Do not sum interval contributions or promote this overlay.


### Recovery-event quality results — 2026-10-09

- Workflow passed: [run 37913220046](https://github.com/eklu654/Trading-Bot/actions/runs/37913220046), artifact ID `11607980290`, digest `47ca48336513770609e4c38fe860e095db71a7c7ae145d55fd260253f9761fd2`.
- Report: [canonical recovery event quality](CANONICAL_RECOVERY_EVENT_QUALITY_2026-10-09.md). QQQ/VIX event-only sample: 38 canonical shock/recovery events, 1999-03-10 through 2026-10-07.
- At the +10% recovery decision, structural condition flagged 23/38 events; fast-shock flagged 27/38. Against a new-low-within-60-session target, precision was 60.9%/59.3% and specificity only 47.1%/35.3%, respectively. By 120 sessions precision rose to ~74%, but specificity remained ~42–50%. This is suggestive, not enough to override B0.
- Counterexamples: 2019-01-07 structural true but QQQ +16.5% over next 60 sessions without a new low; 2020-03-26 fast-shock true but QQQ +28.8% over next 60 sessions without a new low; 2022-07-19 both flags true and QQQ made a new low within 60 sessions.
- Decision: current structural/fast-shock flags are too nonspecific to safely gate B0 recovery. If proceeding, test an explicit recovery-confirmation rule with a fast-rebound exception; keep B0 unchanged as control.


### Recovery-gated structural confirmation experiment — 2026-10-09

- The continuous matrix overlay was rejected because it blocks successful B0 recovery decisions. New candidate applies the matrix only at the canonical +10% recovery decision; it never reduces exposure during ordinary B0-held periods.
- When a recovery is flagged, the strategy vetoes it only if the rebound took longer than a fixed N sessions from the running low. A veto keeps the strategy defensive, updates any new low, and reassesses at the next +10% recovery. Fast-recovery exception sensitivity: N=5/8/10 sessions.
- This is a small, exploratory, in-sample sensitivity test, not a production selection. Frozen plan: [CANONICAL_RECOVERY_GATE_2026-10-09.md](CANONICAL_RECOVERY_GATE_2026-10-09.md).
- Workflow: `.github/workflows/canonical-recovery-gate.yml`; results to be recorded after artifact inspection.


### Recovery-gated structural confirmation results — 2026-10-09

- Workflow passed: [run 37913598899](https://github.com/eklu654/Trading-Bot/actions/runs/37913598899); artifact ID `11607946132`, digest `0e9e84b2492c26692a3c0f7194e8ae0cdb8d71f41f5bca5448e945de942d916a`.
- Report: [recovery gate results](CANONICAL_RECOVERY_GATE_RESULTS_2026-10-09.md).
- Actual TQQQ: B0 $4.040M; N=5 $1.724M, N=8 $3.102M, N=10 $3.102M. N=8/10 preserve COVID's +24.58% window, but worsen max DD (-79.68% vs B0 -73.53%), worsen 2022 (-76.83% vs -69.83%), and finish ~23.2% below B0. N=5 also blocks COVID and is worse.
- Decision: reject this recovery gate in its tested form; do not choose a speed threshold. The 2022 veto kept the strategy out until the matrix cleared on 2022-08-10, with opportunity cost outweighing avoided weakness.
- Next hypothesis, if pursued: test a bounded short delay rather than waiting for DMA clearance. Keep it explicitly exploratory; modern data has already been inspected.


- Audit detail: artifact manifest reports actual aligned input 2010-02-11 through 2026-10-07 (4,189 rows), SHA-256 `1b4993c21e5dd211a71d0bda23934e07ade383d00eeb17f24645f9c03f8095b1`. Synthetic 1999+ output is an uncalibrated hypothetical 3x QQQ proxy, not actual TQQQ.
- Full event-level review: 2019-01-07 and 2020-03-26 recovery attempts were vetoed at N=5 but released at N=8/10; the 2022-07-19 recovery was vetoed through 2022-08-10. Vetoed checks repeat daily and are not independent events.
- No more threshold tuning of this design. If testing a bounded delay next, predeclare it separately and compare against B0 on the same frozen input.


### Bounded recovery-delay follow-up — 2026-10-09

- The prior recovery-gated test kept exposure at 0% until the matrix cleared after a slow flagged recovery; this lost too much upside in 2022. The next experiment caps that wait at 3/5/10 sessions, with an 8-session fast-recovery exception held fixed.
- Reentry still requires QQQ to be at least 10% above the current running low; any new low resets the pending wait.
- Frozen plan: [CANONICAL_BOUNDED_RECOVERY_DELAY_2026-10-09.md](CANONICAL_BOUNDED_RECOVERY_DELAY_2026-10-09.md). Workflow: `.github/workflows/canonical-bounded-recovery-delay.yml`. Results pending.


### Long-history drawdown/recovery-rally diagnostic — 2026-10-09

- Workflow passed: [run 37913801136](https://github.com/eklu654/Trading-Bot/actions/runs/37913801136); artifact ID `11607489248`, digest `e3433b3d57435e4c99ec16ecbdd845db6c7b298b201ef4418b1ada3aa0efd0b0`.
- Report: [long-history diagnostic results](LONG_HISTORY_DRAWDOWN_RALLY_DIAGNOSTIC_RESULTS_2026-10-09.md).
- S&P 500 signal-only sample, 1970-01-02 to 2026-10-07: 24 drawdown/recovery events, 12 failed, 9 successful, 3 censored. Failed events averaged 38.5 sessions low-to-recovery (median 31.5) versus 20.8 (median 16) for successful events.
- 1987 is a clear counterexample to speed-only logic: recovery threshold occurred two sessions after the low, yet another -10% decline followed within three sessions. 2000–2002 produced two failed events with slow average recovery (34.5 sessions).
- This is not the canonical QQQ event set, no TQQQ balance is computed, and the small retrospective sample cannot validate a trading rule. Use speed only as one hypothesis; any next test needs a causal confirmation signal and fast-rebound exception.


### Bounded-delay result and same-input audit — 2026-10-09

- Run 37913900764 passed; artifact 11608910752 (SHA-256 `d1a171fd62d0a578ecbf79993e7ec52f8ee889b4809b06fc3977396e8ad74db4`). Report: [bounded recovery delay](CANONICAL_BOUNDED_RECOVERY_DELAY_2026-10-09.md).
- Actual TQQQ B0 ended $4.040M; bounded wait 3/5/10 sessions ended $3.921M/$3.774M/$3.451M. None beat B0; all preserve COVID but worsen drawdown and 2022.
- Audit caveat: actual overlay indicators were calculated from a separate QQQ download, not recomputed from frozen `x.qqq_adj_close`. Correct actual feature construction and rerun before treating these as exact same-input comparisons.


### Long-history bear-rally signal audit — 2026-10-09

- Workflow passed: [run 37913829220](https://github.com/eklu654/Trading-Bot/actions/runs/37913829220), artifact ID `11607543639`, digest `864433f76e885fe5e5717dac38aca7fd72b0d62507034d0592674e2f0489118e`.
- Report: [long-history bear-rally signal audit](LONG_HISTORY_BEAR_RALLY_SIGNAL_AUDIT_RESULTS_2026-10-09.md).
- S&P 500 signal-only sample: 18 events (10 failed, 6 successful, 2 censored). Failed versus successful events had weaker 60-session returns at recovery (mean -14.4% vs -4.6%) and price farther below the 100/200-DMA. Recovery speed did not separate overall: mean 17.6 sessions for failed vs 20.3 for successful; the 1987 fast failures break a speed-only rule.
- Treat this as a small descriptive clue, not a validated rule or TQQQ backtest. Next review the actual-TQQQ feature and three-layer validation/attribution artifacts before deciding whether any next candidate merits implementation.
