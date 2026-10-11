# Stress-Conditioned SOXL Cap Results — 2026-10-11

## Run status
- Validated workflow run ID: `38120873209` — [success](https://github.com/eklu654/Trading-Bot/actions/runs/38120873209).
- Tested commit: `227774fd451182975dadaacb19875f24b813310a`.
- Stress-state and concentration-cap tests passed; full backtest and artifact upload succeeded.
- Artifact ID: `11695881143`, `soxl-stress-conditioned-cap-results`.
- Actual family ETF history, 4,166 performance sessions from 2010-03-12 through 2026-10-02; $5,000 initial capital.
- Frozen base: DMA-250/top-2/5-session family rotation. Candidate uses the fixed SOXL 25% cap only when SOXX is at least 15% below its prior-close 60-session high; stress clears at -10% drawdown. State updates only at the existing 5-session rebalance dates. Costs: 0/10/25/50 bps.

## Full-period results

| Cost | Base final | Permanent 25% cap | Stress-conditioned cap | Conditional wealth change vs base | Base max DD | Conditional max DD | DD improvement |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | $378,052 | $271,522 | $360,481 | -4.12% | -67.40% | -66.57% | +0.83 pp |
| 10 bps | $320,190 | $232,263 | $305,010 | -4.74% | -67.85% | -67.02% | +0.83 pp |
| 25 bps | $249,490 | $183,713 | $237,314 | -4.88% | -68.53% | -67.69% | +0.84 pp |
| 50 bps | $164,471 | $124,203 | $156,067 | -5.11% | -69.63% | -68.77% | +0.86 pp |

At 25 bps, the worst rolling 252-session return improves from -63.77% to -62.80%, less than a one-point improvement. Split behavior is modest: at 25 bps the candidate's train max drawdown is unchanged from base, validation improves by about 2.68 points but ending equity is lower ($6,700 vs $6,827), and holdout ends nearly equal to base ($42,582 vs $42,845) with only about a 1.03-point drawdown improvement.

The conditional cap preserves about 95% of base terminal wealth, unlike the permanent cap, but does not materially reduce drawdown. It therefore fails the preregistered requirement of at least a 5-point drawdown improvement.

## Decision
**Reject SOXL_CAP25_STRESS60_DD15_10 under the preregistered rule.** Do not tune the 60-session window or the -15%/-10% hysteresis levels.

The results now clarify the trade-off:
- Permanent SOXL concentration cap: meaningful drawdown reduction, but about 26% terminal-wealth loss at 25 bps.
- Stress-conditioned SOXL cap: preserves about 95% of wealth, but reduces full-period max drawdown by less than one percentage point.
- Family-specific shock gate and replacement rotation: reduce some event-level losses but sacrifice too much terminal wealth.
- TQQQ-only re-entry variants and fixed exposure caps also failed their predeclared criteria.

This is the end of the current bounded defensive-rule family. Do not add another indicator or parameter sweep. Next, audit the frozen family-rotation selector and consider only a genuinely distinct portfolio architecture if it has a specific, testable mechanism. Keep 2000 as a stress-test case, not the design target; any pre-2010 leveraged ETF series must be a clearly labeled synthetic daily-reset simulation.

## Failed initial implementation note
No failure occurred in this validated run. Both tests and the backtest passed before artifact publication.

## Artifact hashes
- Summary SHA-256: `899061ff1892eb78d44905139c2a8be1d47a7a56c5c4ec767bd6cf0484d2efb5`
- Equity curves SHA-256: `981af39655e61fec22e7b144d977312e7329e164c6dddd463c3013e232e4a55b`
- Base weights SHA-256: `12931192a84ea1147e0c5346ee6509e38df158c4384067055202f5ea91014a41`
- Permanent cap weights SHA-256: `81a45de8909065597a7cf51942cfd3c24cfc81e513e6f7428b87cbe142a5fa5b`
- Conditional cap weights SHA-256: `7f059799a76c55c1c466a035a1341f3bd074e3567b816874c7f7f62059849713`
- Stress state SHA-256: `b242485b38383af82bf39e4d3ae16db52a73f9ded8d225fb038e26d7390bfe7a`
- Drawdown signal SHA-256: `fdec489db54e4692e5122dd0ab64007c26c435231bbaaa47163dff8ea50a94d9`
- Bull-return panel SHA-256: `082e508cd2e60746a57224b14e57ad7d40a97320cfcc8b29d4f4a38ca8c83359`
- Manifest SHA-256: `d76d21d35d7e42175e723fa572526785feec6b137cffeea5b442024184601c7f`
