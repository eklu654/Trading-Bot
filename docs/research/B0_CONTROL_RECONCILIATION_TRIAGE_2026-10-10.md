# B0 Control Reconciliation — Triage Notes (2026-10-10)

## Purpose
Continue the control discrepancy audit before any further candidate selection. This is a source-code/documentation comparison, not a new backtest. Do not treat the different headline balances as a like-for-like contradiction until their evaluation windows, costs, and initialization are aligned.

## Confirmed code paths and mismatched settings

### Canonical same-input reconciliation
- Script: `research/tqqq_canonical_same_input_reconciliation.py`
- Download window: QQQ/TQQQ from 2010-01-01 to exclusive end 2026-10-08.
- Aligns QQQ and TQQQ sessions, freezes one CSV, calculates the B0 signal on the aligned QQQ adjusted-close history, builds adjusted TQQQ open/close return legs, and checks a separate daily execution loop against the shared causal engine.
- It starts the equity curve on the first aligned TQQQ observation and reports no transaction-cost stress in its headline summary.
- It emits an event ledger, daily equity path, summary, and manifest. Its manifest/hash must be retained when comparing a rerun.

### Structural matrix
- Script: `research/canonical_plus_structural_matrix.py`
- Actual TQQQ uses the same-input helper above and reports B0 at about $4.040M over 2010-02-11 through 2026-10-07. The metric path uses the no-cost `next_open_daily_returns` engine.
- Corrected overlay rerun preserved the exact frozen QQQ closes for B0 dates; the $4.040M B0 result was unchanged to displayed precision.

### 250-DMA / Fed-200 / VIX-30 hybrids
- Scripts: `research/b0_250dma_hybrid_validation.py`, `research/b0_fed200_hybrid_validation.py`, and `research/b0_vix30_hybrid_validation.py`.
- These use the shared causal *cost* engine and report costs of 0/10/25/50 bps.
- They intentionally start actual-TQQQ evaluation on 2011-02-07 after the 250-session warm-up, rather than at TQQQ inception. At 10 bps, their B0 control is $1,782,472; at 0 bps it is $1,816,680.
- Therefore $4.040M and $1.782M are **not a like-for-like comparison**: they differ in evaluation start and transaction-cost assumptions, as well as input end dates by a few sessions. The gap is not yet explained quantitatively by a same-window replay. Do not describe it as a confirmed calculation error, and do not claim it is fully reconciled.

## VIX-30 experiment result recovered from the successful workflow log
- Workflow: [run 37925744760](https://github.com/eklu654/Trading-Bot/actions/runs/37925744760), successful; artifact ID `11613702733`, ZIP digest `sha256:49ad6a14dcf69b3126a99382105468690eec2d5f2af8b45885726d6107efd0f8`.
- At 10 bps, actual TQQQ (2011-02-07–2026-10-02): B0 $1,782,472, max DD -73.64%; VIX>=30 / 75% exposure $1,187,182, max DD -75.39%; VIX>=30 / 50% exposure $765,714, max DD -77.19%.
- Synthetic proxy (2000-03-03–2026-10-02): B0 $236,501, max DD -99.376%; VIX/75% $150,705, max DD -99.245%; VIX/50% $84,958, max DD -99.177%.
- Both VIX candidates failed all four preregistered gates: 90% actual wealth retention, 3pp actual drawdown improvement, 90% synthetic wealth retention, and 3pp synthetic drawdown improvement. The VIX overlay reduced wealth and worsened actual-TQQQ drawdown. Reject this family without retuning.

## Required next reconciliation — do not skip
1. Use a single frozen input CSV and a single B0 signal/event ledger.
2. Compute B0 equity from TQQQ inception to the common end at 0/10/25/50 bps.
3. On that exact same frozen series, compute the same B0 equity after the 250-session warm-up, resetting the starting balance to $5,000 at the warm-up date, at the same costs.
4. Also calculate a continuation curve that carries the inception-grown equity forward (do not reset it to $5,000) so the effect of warm-up truncation is explicitly measured.
5. Assert event dates/signals are identical across all views on overlapping dates; assert the 0-bps cost engine matches the ordinary causal return engine; record SHA-256 for frozen inputs and output.
6. Compare output to the matrix's $4.040M, hybrid's $1.8167M at 0 bps and $1.7825M at 10 bps. Only after this do we decide whether a code/data defect remains.
7. Keep actual TQQQ and synthetic proxy separate; no paper/live approval follows from this reconciliation.

## Audit caution
The code inspection establishes different windows and costs. It does **not** yet establish how much of the balance gap each factor explains, whether there is any additional input/logic discrepancy, or whether the original $4.040M value can be exactly reproduced from the current vendor download. This requires the same-frozen-input rerun above.


## New controlled reconciliation run — 2026-10-10

- Workflow: [TQQQ Dot-Com Survivability run 38030782533](https://github.com/eklu654/Trading-Bot/actions/runs/38030782533), success; artifact ID `11661993293`, ZIP digest `sha256:173c3ea552d977006f949f8c2120a57286578378dc323f7d1b4179a3a2fcd52c`.
- Frozen input hash: `7d9190d22433351845a7e8a07252c135f07a5a95201eaf848d9dd9e3f0b2b51d`.
- This run confirms the current canonical same-input calculation again: $4,040,314 at 0 bps, with the shared execution engine and independently coded loop agreeing exactly (maximum absolute daily-return and equity differences both 0).
- On the *same newly frozen data and B0 signal*, 250-session warm-up reset produced:
  - $1,875,211 at 0 bps;
  - $1,839,900 at 10 bps;
  - $1,788,114 at 25 bps;
  - $1,704,859 at 50 bps.
- The warm-up begins 2011-02-07, while inception starts 2010-02-11. The carried-equity view retains $4.040M / $3.964M / $3.853M / $3.673M through 2026-10-07 at 0/10/25/50 bps respectively; it starts that post-warm-up view with the equity accumulated since inception rather than resetting capital.
- These outputs show that changing the evaluation start and resetting capital explains a large share of the apparent $4.04M versus ~$1.8M difference. The exact hybrid comparisons still require a common end date: the hybrid runs end 2026-10-02, whereas this reconciliation run ends 2026-10-07. A follow-up was added to report both end cutoffs from the same frozen input without redownloading.
- Initial pytest collection failed because the canonical reconciliation module imported `causal_execution` only as a top-level script. Fixed that import to support package imports. The subsequent test run and same-input cutoff rerun are pending/under verification as of this note; do not mark the full audit complete until they finish.

## Implementation commits
- Audit note initially committed as `12ae0bc658b502881626f829b5af26eb3f3a2917`.
- Reconciliation script `research/b0_control_window_cost_reconciliation.py` and tests `tests/test_b0_control_window_cost_reconciliation.py` added.
- Workflow `.github/workflows/tqqq-dotcom-survivability.yml` updated to run the reconciliation and archive its input, summary, paths, event ledger, and manifest.
- Package-import compatibility fixed in `research/tqqq_canonical_same_input_reconciliation.py`.
- The common 2026-10-02 cutoff view was added so cost and date-window effects can be compared on identical frozen inputs.


## Same-end-date reconciliation result — 2026-10-10

- Successful full experiment workflow: [run 38030890249](https://github.com/eklu654/Trading-Bot/actions/runs/38030890249), success; it ran the cutoff-capable reconciliation script and uploaded artifact `11661993293`. The frozen input hash for this run was `a1c07e6cc3696a5b0f293a39ba73a42ee8e4412d0b1156d6715ca74a5cd12885`.
- Test suite: [run 38030952802](https://github.com/eklu654/Trading-Bot/actions/runs/38030952802), **142 passed, 1 warning**. The first cutoff-view test had a fixture/path-set assertion error; that assertion was corrected. The manifest was subsequently updated to enumerate the six summary views, and its final syntax/test rerun is tracked separately.
- On the identical frozen input, with the identical B0 signal and identical last observation date of 2026-10-02:
  - At 0 bps, inception-start B0 ends at **$3,914,205**; resetting $5,000 at the 250-session warm-up date ends at **$1,816,680**.
  - At 10 bps, inception-start B0 ends at **$3,840,500**; resetting $5,000 at the warm-up date ends at **$1,782,472**.
  - The warm-up-carried-equity view ends at the same amount as inception-start B0, because it preserves the equity accumulated before the warm-up date rather than resetting capital.
- The warm-up date is 2011-02-07. At that date, the no-cost inception-grown equity is already **$10,769**, compared with a newly reset $5,000. This is why the warm-up-reset run ends at roughly half the inception-start run: it discards the growth accumulated during the first year.
- On the 2026-10-02 window, the $1,782,472 at 10 bps exactly matches the hybrid scripts' B0 control. This materially resolves the apparent $4.04M-versus-$1.78M mismatch: the headline numbers used different starting dates/capital initialization, costs, and end dates. It is not evidence of a B0 signal/execution code defect.
- The latest canonical same-input run independently reproduced $4,040,316 from inception through 2026-10-07, with shared and independent execution engines agreeing exactly (zero max absolute daily-return and equity differences). The $4.04M result is reproducible under its stated no-cost, inception-start assumptions.

## Decision
The balance gap is now explained on a controlled same-input basis. Keep the evaluation basis explicit in every future table: (a) inception-start equity, or (b) fresh $5,000 at 250-session warm-up; state cost assumption and last observation date. Do not compare those terminal balances without this metadata. This reconciliation does not validate the strategy for live trading; it only resolves the accounting/window comparison.
