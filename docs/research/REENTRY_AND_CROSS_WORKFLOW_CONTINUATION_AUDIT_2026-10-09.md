# Trading-Bot Continuation Audit — Re-entry and Cross-Workflow Results (2026-10-09)

## Scope and reproducibility

This note records completed GitHub Actions runs inspected during the 2026-10-09 continuation. The current re-entry run uses commit `31d7bfdb54ba558d241b95d35772175e021378df`; workflow [run 37922295072](https://github.com/eklu654/Trading-Bot/actions/runs/37922295072) completed successfully. Its artifact is `reentry-isolation-results`, ID `11612253006`, with frozen aligned QQQ/TQQQ inputs, equity curves, and summary CSV. The workflow's state-transition tests, backtest, and artifact upload all succeeded.

The script now distinguishes **R2** (guarded exploratory variant) from **R2P** (the originally preregistered staged-recovery behavior). R2P preserves its 50% position after that tranche has activated, even if a later QQQ decline resets the running-low reference. This resolves the previously documented specification mismatch without overwriting the original run or its audit.

## Re-entry experiment — actual TQQQ era

Start: $5,000. Aligned observations: 2010-02-11 through 2026-10-07 (4,189 sessions). Signals use QQQ adjusted-close information and execute at the next TQQQ open. The metrics below are zero-cost; cost-stress rows follow.

| Candidate | Ending balance | CAGR | Max drawdown | Worst rolling 252-session return | Avg target exposure |
|---|---:|---:|---:|---:|---:|
| B0 control | $4,040,316 | 49.49% | -73.53% | -72.64% | 93.46% |
| R1 immediate re-entry with renewed-shock guard | $3,661,415 | 48.61% | -81.15% | -80.51% | 99.57% |
| R2 guarded staged +5%/+10% | $3,039,513 | 46.95% | -77.14% | -76.37% | 95.57% |
| R2P preregistered staged +5%/+10% | $3,197,013 | 47.40% | -73.44% | -72.54% | 95.82% |

R2P modestly improves maximum drawdown by about 0.10 percentage points and the worst rolling 252-session return by about 0.10 points, but ends **$843,303 (20.9%) below B0**. This does not pass the wealth-retention gate and is not a replacement for B0. R1 and R2 remain worse than B0 on both terminal wealth and maximum drawdown.

### Cost sensitivity — ending balance

| Candidate | 0 bps | 10 bps | 25 bps | 50 bps |
|---|---:|---:|---:|---:|
| B0 | $4,040,316 | $3,964,237 | $3,852,659 | $3,673,279 |
| R1 | $3,661,415 | $3,535,420 | $3,354,290 | $3,072,252 |
| R2 | $3,039,513 | $2,964,441 | $2,855,202 | $2,681,772 |
| R2P | $3,197,013 | $3,136,820 | $3,048,567 | $2,906,749 |

The ranking is unchanged at every tested cost. These are one-way exposure-change cost assumptions, not a broker-specific fill model.

### Episode-level diagnostic

The B0 control has nine defensive spells in the aligned sample, covering 274 target-exposure-zero sessions. R1's compounded strategy return over those B0 cash spells was negative in eight of nine episodes (median -28.56%; mean -20.75%). This is a diagnostic on the same historical sample, not a causal decomposition or an out-of-sample estimate. R2P's partial exposure reduced some of the losses versus R1, but its whole-sample terminal wealth still fell well short of B0.

## Cross-workflow findings inspected

- [Long-history drawdown/rally audit, run 37922294953](https://github.com/eklu654/Trading-Bot/actions/runs/37922294953), artifact `11612661497`, succeeded. It is explicitly a **signal-only S&P 500 index diagnostic**, not a QQQ/TQQQ portfolio test: 24 labeled events, 12 failed, 9 successful, and 3 censored. Event count is too small to support a predictive model or select thresholds. In the dot-com period it labeled two events as failed; this does not by itself measure a portfolio's survivability.
- [Partial-DMA matrix, run 37922294954](https://github.com/eklu654/Trading-Bot/actions/runs/37922294954), artifact `11611889008`, succeeded. In its synthetic 3x QQQ model, the best-ending row was 150-DMA with 25% exposure below the DMA: about $824,367 ending and -98.24% max drawdown. Its synthetic buy-and-hold row ended about $58,703 and had -99.9618% max drawdown. This buy-and-hold result **must not be confused with B0**; it uses a different strategy and execution/model implementation.
- [Actual-TQQQ three-layer validation, run 37922295113](https://github.com/eklu654/Trading-Bot/actions/runs/37922295113), artifact `11612147868`, succeeded. Ending balances were about $84,635 for the base 100-DMA signal, $106,888 for the Fed-conditioned variant, $91,785 for the three-layer variant, versus $2.029M for actual TQQQ buy-and-hold. The lower-ending strategy rows had -61.36% max drawdown versus -81.66% for buy-and-hold. This is a distinct architecture and does not supersede the B0 control comparison.
- [Canonical same-input reconciliation, run 37922295017](https://github.com/eklu654/Trading-Bot/actions/runs/37922295017), artifact `11612063143`, succeeded. Shared and independent implementations matched: ending balance $4,040,316.96, CAGR 49.4874%, max drawdown -73.5343%. The independent event file records nine actual-TQQQ shock/recovery episodes.
- [Failed-bounce independent audit, run 37922295011](https://github.com/eklu654/Trading-Bot/actions/runs/37922295011), artifact `11611594406`, succeeded and independently reported B0 ending $4,040,313.91 / max drawdown -73.5343%, with actual TQQQ buy-and-hold ending $2,094,669.10 / max drawdown -81.6598%. The few-dollar terminal difference from other B0 runs is a small input/version precision discrepancy and should be reconciled before demanding exact cent-level parity across separately downloaded market snapshots.
- [Failed-bounce structural matrix, run 37922295014](https://github.com/eklu654/Trading-Bot/actions/runs/37922295014), artifact `11612646617`, succeeded. The canonical B0 row was $4.040M / -73.53% max drawdown. The tested structural variants did not improve terminal wealth; the top listed `repair_and_damage7` variant ended about $3.763M with -70.23% max drawdown. This is a trade-off, not a wealth win.
- The research test suite also completed successfully in [run 37922294843](https://github.com/eklu654/Trading-Bot/actions/runs/37922294843) on the same code SHA used for the R2P experiment.

## Important 2000–2002 interpretation boundary

The existing [Near-Ruin Defense Gate Continuation](NEAR_RUIN_DEFENSE_GATE_CONTINUATION_2026-10-09.md) documents a separate synthetic daily-reset 3x QQQ B0 replay with approximately $836,044 ending, -99.3720% full-period max drawdown, and -99.1484% local max drawdown in 2000–2002; in that specific replay it did not cross -99.9% or zero. That is not the same path as synthetic buy-and-hold in the partial-DMA matrix, which did cross -99.9% drawdown. Neither is actual TQQQ history. Because the scripts use different signal rules, return construction, and execution implementations, these figures are not directly interchangeable; a future unified synthetic replay should run B0 and all benchmarks on one frozen input and one shared execution engine before any definitive near-ruin claim.

## Decision and next actions

1. Keep B0 as the control. No re-entry variant is promoted; R2P is closest on drawdown but fails the terminal-wealth gate.
2. Do not tune the +4.5%, +5%, or +10% thresholds based on the event P/L already inspected.
3. The unresolved research priority is a **unified synthetic 1999–present B0 vs buy-and-hold survivability replay**, sharing frozen adjusted QQQ inputs and one causal execution engine, with first-crossing dates for -99%, -99.9%, and zero, plus the 2000–2002 local trough/recovery metrics. Keep it clearly labeled synthetic, not actual TQQQ.
4. After that unified run, use chronological holdout/walk-forward validation for any candidate. No paper/live approval follows from these exploratory results.
