# Bounded recovery delay — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; Actions result pending.**

## Motivation
The recovery-gated structural confirmation candidate preserved COVID at an 8-session exception but lost terminal wealth and worsened max drawdown because it waited for the structural matrix to clear after the 2022-07 recovery attempt. Test whether a hard maximum wait limits this opportunity cost.

## Frozen rule
- Base: canonical QQQ -4.5% shock / +10% from running low recovery, $5,000, close-to-next-open.
- Structural/fast flag parameters unchanged: 150-DMA, 100-DMA, 63-session return <= -20%, 252-session drawdown <= -20%, VIX >= 30; structural flag = QQQ below 150-DMA and 100-DMA below 150-DMA; fast flag = QQQ below 100-DMA and any shock criterion true.
- Fast-recovery exception fixed at 8 sessions from running low.
- When recovery takes more than 8 sessions and either matrix flag is true, delay re-entry until the matrix clears or the maximum wait expires, whichever comes first. Sensitivity caps: 3/5/10 sessions.
- Re-entry still requires QQQ to be >=10% above the current running low. A new low resets the pending wait and requires a fresh recovery attempt.
- This is a small exploratory sensitivity set, not an optimized threshold.

## Evaluation
B0 unchanged; actual TQQQ live-fund history and a separately labeled synthetic 3x QQQ diagnostic from 1999. Compare ending balance, CAGR, max drawdown, worst rolling year, COVID/2022 windows, and every recovery attempt/release. Synthetic returns are not actual TQQQ history.

## Audit
- Code: `research/canonical_bounded_recovery_delay.py`
- Workflow: `.github/workflows/canonical-bounded-recovery-delay.yml`
- Code commit: `5e4a159685c7dba9075d4cfd01b124890db9802a`
- Workflow commit: `d23f20b42e2fcec4dae39d51a9485520b5f6a746`
- Add run/artifact/result metadata after completion.


## Results

- Workflow passed: [run 37913900764](https://github.com/eklu654/Trading-Bot/actions/runs/37913900764).
- Artifact ID `11608910752`; SHA-256 `d1a171fd62d0a578ecbf79993e7ec52f8ee889b4809b06fc3977396e8ad74db4`.
- Actual TQQQ dates: 2010-02-11 through 2026-10-07, 4,189 observations; synthetic diagnostic 6,938 observations from 1999-03-10 through 2026-10-07.

### Actual TQQQ results

| Rule | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return | COVID window | 2022 window |
|---|---:|---:|---:|---:|---:|---:|
| B0 canonical | $4,040,314 | 49.49% | -73.53% | -72.64% | +24.58% | -69.83% |
| Bounded wait 3 sessions | $3,921,280 | 49.22% | -74.31% | -73.45% | +24.58% | -70.71% |
| Bounded wait 5 sessions | $3,774,295 | 48.88% | -75.28% | -74.44% | +24.58% | -71.81% |
| Bounded wait 10 sessions | $3,451,428 | 48.08% | -77.39% | -76.63% | +24.58% | -74.22% |

All use the fixed 8-session fast-recovery exception. A 3-session cap is closest to B0, but still reduces ending wealth by about 2.95% and worsens max drawdown by 0.78 percentage points. Longer waits are progressively worse. The vetoed July 2022 recovery was released on July 22 / July 27 / August 2 for caps 3 / 5 / 10; waiting for matrix clearance was worse still.

### Synthetic 3x QQQ diagnostic

| Rule | Ending balance | CAGR | Max drawdown | COVID window | 2022 window |
|---|---:|---:|---:|---:|---:|
| B0 canonical | $836,043 | 20.40% | -99.37% | +26.34% | -68.81% |
| Bounded wait 3 sessions | $1,174,860 | 21.89% | -99.10% | +26.34% | -69.77% |
| Bounded wait 5 sessions | $764,318 | 20.01% | -99.39% | +26.34% | -71.00% |
| Bounded wait 10 sessions | $1,133,867 | 21.73% | -99.01% | +26.34% | -73.49% |

Synthetic output is not actual TQQQ performance and remains uncalibrated; it is not a basis for selecting a rule.

## Decision
The 3-session cap is close to B0 but does not improve the stated objective; 5/10 sessions are worse. Reject this bounded-delay family on the current actual-TQQQ sample. Do not continue sweeping delay caps against this same inspected period.

## Methodology audit follow-up
The actual-TQQQ scripts aligned feature dates to the frozen QQQ/TQQQ frame, but the overlay indicators were originally calculated from a separate QQQ download before alignment. This means the overlay's adjusted-close-derived indicators were not literally calculated from the same frozen QQQ series as B0. Differences appear small in the reported summaries, but exact same-input comparisons require recalculating the actual overlay indicators from `x.qqq_adj_close` after alignment. Treat the above result as provisional until that causal input alignment is corrected and rerun.


## Same-input correction rerun
- Corrected run: [37914300654](https://github.com/eklu654/Trading-Bot/actions/runs/37914300654); artifact ID `11609410614`, SHA-256 `ceae85991294ac293ae869f7e9c64d25b1bedf362064872f36615813d7424c48`.
- Actual-period indicators now use B0's frozen QQQ closes with pre-inception lookback retained. Results match to displayed precision: B0 $4.040M; 3/5/10-session caps $3.921M/$3.774M/$3.451M. Rejection remains.
