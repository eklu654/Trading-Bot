# Shock-Cluster R4 Results and Decision — 2026-10-11

## Run status and implementation audit
- Validated workflow: [run #34](https://github.com/eklu654/Trading-Bot/actions/runs/38119818755) — **success**.
- Tested commit: `e66f74d240aadd1f4b4a2c76635399b39fd2f322`.
- Unit tests passed, including isolated-shock control equivalence and staged clustered recovery. Backtest and artifact upload succeeded.
- Artifact ID: `11694724448`, name `reentry-isolation-results`.
- Evaluation: 4,189 aligned sessions, 2010-02-11 through 2026-10-07; actual TQQQ, QQQ adjusted-close signals; $5,000 initial capital.
- Important audit note: earlier run [#31](https://github.com/eklu654/Trading-Bot/actions/runs/38119708845) used a faulty R4 implementation that re-entered isolated shocks before B0's +10% threshold. Its R4 performance numbers are invalid and must not be used. The corrected logic is covered by the final run's tests.

## Fixed R4 rule
- Keep B0's -4.5% QQQ daily-shock exit and +10% running-low recovery unchanged for isolated shocks.
- Treat an episode as clustered when at least two -4.5% shock days occur in a trailing 20-session window by the recovery trigger.
- For a clustered episode, enter 50% at the +10% rebound trigger; retain 50% through renewed shocks and reset the running low; restore 100% only on a later close above QQQ's 20-session SMA while still at least 10% above the running low.
- Signal at close, execute at next TQQQ open. Costs tested at 0/10/25/50 bps per exposure change.
- No thresholds were tuned.

## Results

| Candidate | Final at 0 bps | Max DD | Worst rolling 252-session return | Final at 10 bps | Max DD at 10 bps |
|---|---:|---:|---:|---:|---:|
| B0 | $4,040,314 | -73.53% | -72.64% | $3,964,235 | -73.64% |
| R3 SMA-confirmed staging | $3,752,189 | -73.93% | -73.05% | $3,681,543 | -74.03% |
| R4 shock-cluster gate | $3,690,487 | -74.13% | -73.26% | $3,621,000 | -74.23% |

R4 ends **8.66% below B0** at zero cost. Maximum drawdown is about 0.60 percentage points worse, and the worst rolling 252-session return is about 0.62 points worse. The trade-off persists at 10/25/50 bps. R4 has the same 274 fully-cash target sessions as B0, plus 23 half-exposure sessions; that modest exposure reduction did not protect the downside enough to compensate for the terminal-wealth loss.

**Decision: reject R4.** It does not meet the preregistered criterion of preserving most B0 wealth while materially improving downside metrics. Do not tune the 20-session cluster window, shock count, or SMA length. Together with R3, this is evidence against adding these particular re-entry gates—not proof that all defense is futile.

## Research direction after R4
The bounded re-entry family has now failed: R1/R2/R2P were inferior, R3 did not improve downside, and corrected R4 slightly worsened both downside metrics and ending wealth. Stop adding more re-entry variants. Next compare a separately preregistered **structural risk-budget** approach against B0, such as a small fixed reserve or a bounded cap on total leveraged-ETF exposure. The comparison must include the opportunity cost during strong bull/recovery periods and use a small number of predeclared alternatives. Separately, retain prolonged-bear detection as a research question, but do not add another signal until the portfolio-level risk-budget test has a clear hypothesis.

This run uses actual TQQQ history only; it is not a test of the 2000 bear market. Any pre-inception test must be a clearly labeled daily-reset simulation on underlying index data.

## Artifact hashes
- QQQ frozen input SHA-256: `83b3d00cba15397c88338a0ebf9a0295b93ad3556fbf0c02834ed75fce4c9c45`
- TQQQ frozen input SHA-256: `7f778f6dcd15db47c931392ee2fff20020d33efe70391aa3a88480943d6b8335`
- Summary SHA-256: `55be410551a307d553fcb31482352cbdbaecba3e9ed26cafb3dbf33d6414c196`
- Equity curves SHA-256: `7bca455170174533ebddab6f338c7e6cc9af13a580681113d9ded310f0fb0114`
