# Fed 2015/2016 Effective-Date Signal Diagnostic — 2026-10-10

## Question

Would moving the FRED target-rate observations for the December 2015 and December 2016 hikes from announcement dates to their documented effective dates change the existing lagged Fed-state labels or the sticky 200-DMA overlay position?

## Provenance and reproducibility

- Isolated branch: `research/qqq-slow-bear-audit`; no change to `main`.
- Workflow run: [38089561632](https://github.com/eklu654/Trading-Bot/actions/runs/38089561632), conclusion: success.
- Diagnostic commit: `26d3152fa3d52450e951883eb7d7ec0261731703`; workflow commit: `83566d885a8989020bd51d13fd90f2c100c35271`.
- Artifact: [fed-2015-2016-effective-date-signal-diagnostic](https://github.com/eklu654/Trading-Bot/actions/runs/38089561632/artifacts/11683576764), SHA-256 `6fa77fe89532728e90e502962ba00850727f324e9ecc6d440d432f41465daf85`.
- Market sample: 4,216 QQQ adjusted-close sessions, 2010-01-04 through 2026-10-07.
- Fed target source: FRED `DFEDTAR`, `DFEDTARL`, `DFEDTARU`; midpoint of lower/upper target range is used when available.
- Transformation: only announcement-date observations are changed; effective-date observations remain unchanged. Both changes were applied and verified.
- The classifier, backward date mapping, one-QQQ-session lag, 200-session DMA entry condition, and sticky exit-on-DMA-reclaim match the relevant logic in `canonical_shock_recovery_fed_dma_overlay.py`. The diagnostic does classify the full available FRED history before mapping, while the portfolio script clips the series to its configured start date; any initial-boundary differences are not material to the two 2015/2016 events or the reported difference dates.

## Exact transformations

| Announcement date | Effective date | Prior target | FRED announcement-date target | FRED effective-date target | Transformed announcement-date target |
|---|---|---:|---:|---:|---:|
| 2015-12-16 | 2015-12-17 | 0.125% | 0.375% | 0.375% | 0.125% |
| 2016-12-14 | 2016-12-15 | 0.375% | 0.625% | 0.625% | 0.375% |

## Results

- Fed-state labels differed on **4 QQQ sessions**: 2015-12-17, 2016-03-16, 2016-12-15, and 2017-03-15.
- The sticky 200-DMA overlay signal differed on **0 sessions**.
- Therefore, the baseline-plus-overlay portfolio signal is unchanged on every session in this sample.
- The workflow's preregistered gate correctly stopped at signal comparison: **no full portfolio backtest is warranted**, because the changed date convention never changes exposure.
- This diagnostic makes no claim about portfolio return or risk; no portfolio simulation was run for this question.

## Decision

Keep the hand-maintained event table and the existing conservative one-session lag unchanged. The source reconciliation flags are explained by announcement-versus-effective-date convention, and this targeted transformation changes some internal state labels but not any overlay position. Do not spend a portfolio backtest on this no-exposure-change scenario.

This is not evidence that the Fed overlay is profitable or safe. Prior whole-period testing still showed the Fed-paused/200-DMA candidate materially below B0 in terminal wealth and no max-drawdown improvement. B0 remains the working research control; no strategy is promoted, and no paper/live trading is authorized.
