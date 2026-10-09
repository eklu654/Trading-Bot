# Structural matrix investigation — consolidated checkpoint

Date: 2026-10-09  
Status: **No structural-matrix candidate selected. B0 remains the working control.**

## Question investigated
The prior structural matrix was probably intended to work in tandem with the canonical QQQ -4.5% daily shock / +10% rebound-from-running-low strategy, not replace it. We implemented that combination and tested state behavior, recovery-point signal quality, and bounded recovery delays.

## Main findings

### 1. Continuous matrix overlay — rejected
- Corrected run: [37914258527](https://github.com/eklu654/Trading-Bot/actions/runs/37914258527), artifact ID `11609270400`.
- B0 actual TQQQ ending balance: ~$4.040M.
- Best structural+fast overlay row: ~$727k, max drawdown -59.47%, but COVID window -8.63% versus B0 +24.58%.
- The overlay reduces drawdown by sacrificing too much compounding and blocks successful recovery decisions.

### 2. Sticky-state ablation — rejected
- Corrected run: [37914285510](https://github.com/eklu654/Trading-Bot/actions/runs/37914285510), artifact ID `11608731601`.
- Actual TQQQ: original sticky $727k; hard-nonsticky $892k; daily-nonsticky $1.355M, versus B0 $4.040M.
- All variants turn the COVID window negative; making the hard override non-sticky does not solve the core problem.

### 3. Interval attribution — explains major opportunity costs
- Corrected run: [37914289809](https://github.com/eklu654/Trading-Bot/actions/runs/37914289809), artifact ID `11609275446`.
- The matrix is defensive on the same close as B0's 2019-01-07 and 2020-03-26 recovery decisions, blocking the next-open re-entry. Conditional leave-one-interval-out costs for those intervals are large (roughly -$140k to -$213k for 2019, -$230k to -$454k for COVID depending on mode).
- Some 2022 intervals help and others hurt. These counterfactual contributions are non-additive; do not sum them.

### 4. Recovery-point event quality — weak specificity
- Run: [37913220046](https://github.com/eklu654/Trading-Bot/actions/runs/37913220046), artifact ID `11607980290`.
- QQQ-only, 1999–2026 event diagnostic: 38 canonical shock/recovery events.
- For predicting a new low within 60 sessions, structural flag precision/specificity were 60.9%/47.1%; fast-shock flag 59.3%/35.3%. This is descriptive in-sample evidence, not statistical validation.
- 2019 and COVID are false-positive examples; July 2022 is a true-positive example.

### 5. Recovery-gated matrix — rejected
- Corrected run: [37914294832](https://github.com/eklu654/Trading-Bot/actions/runs/37914294832), artifact ID `11608866543`.
- Matrix only vetoed B0 recovery when the recovery was slower than an 5/8/10-session exception threshold and a matrix flag was present.
- Actual TQQQ: N=5 $1.724M; N=8 $3.102M; N=10 $3.102M versus B0 $4.040M. N=8/10 preserved COVID but worsened drawdown and 2022.

### 6. Bounded delay — rejected
- Corrected run: [37914300654](https://github.com/eklu654/Trading-Bot/actions/runs/37914300654), artifact ID `11609410614`.
- Fixed 8-session fast-recovery exception and capped a slow flagged recovery delay at 3/5/10 sessions.
- Actual TQQQ: $3.921M / $3.774M / $3.451M versus B0 $4.040M. The 3-session cap was closest but still lowered terminal wealth and worsened drawdown; longer waits worsened the result.

## Frozen-input methodology correction
The actual-period QQQ indicators were initially calculated from a separate QQQ download before alignment. The code now retains historical QQQ lookback, overwrites all live-TQQQ dates with the frozen B0 QQQ adjusted-close series, and recomputes the rolling indicators. Corrected runs were successful and match prior results to displayed precision. Use corrected artifact/run links above.

## Synthetic history caution
All 1999-onward “3x QQQ” results are hypothetical diagnostics, not actual TQQQ performance. The proxy is not fully calibrated for financing, fees, distributions, tracking, and real fund mechanics; its extreme drawdowns preclude treating its ending balances as realized strategy results.

## Decision and next step
- Keep canonical B0 unchanged as the working benchmark.
- Reject the tested matrix families; stop threshold tuning on this same modern sample.
- No strategy has been promoted to paper trading from these results.
- If the research continues, use the false-positive/true-positive contrast to formulate a materially different feature that can distinguish slow failed rallies from rapid recoveries, then freeze it before testing any future untouched data. Avoid further variants that simply keep the strategy defensive until a long DMA is reclaimed.
