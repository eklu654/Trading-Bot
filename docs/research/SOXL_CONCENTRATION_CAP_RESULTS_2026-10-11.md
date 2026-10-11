# SOXL Concentration Cap Results — 2026-10-11

## Run status
- Validated workflow run ID: `38120717873` — [success](https://github.com/eklu654/Trading-Bot/actions/runs/38120717873).
- Tested commit: `3562f60b6aeb6a398de602853b5eb4ef8dbc8df2`.
- Three unit tests passed; the full comparison completed and artifact uploaded.
- Artifact ID: `11694847527`, `soxl-concentration-cap-results`.
- Universe: SPXL/SPY, TQQQ/QQQ, SOXL/SOXX, UDOW/DIA, TNA/IWM; common aligned dates 2010-03-11 to 2026-10-02; $5,000 initial capital.
- Frozen base: DMA-250 eligible families, top two, rebalance every five sessions; costs 0/10/25/50 bps.

## Results

| Cost | Base final | SOXL cap final | Wealth change | Base max DD | Cap max DD | DD improvement |
|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | $378,052 | $271,522 | -28.18% | -67.40% | -62.64% | +4.75 pp |
| 10 bps | $320,190 | $232,263 | -27.46% | -67.85% | -63.12% | +4.74 pp |
| 25 bps | $249,490 | $183,713 | -26.37% | -68.53% | -63.92% | +4.61 pp |
| 50 bps | $164,471 | $124,203 | -24.48% | -69.63% | -65.22% | +4.41 pp |

At 25 bps, the worst rolling 252-session return improves from -63.77% to -58.17% (5.60 percentage points). The split results show why the cap is not a free improvement:
- Train: cap ending equity $21,580 vs base $21,323; max DD improves from -65.85% to -60.44%.
- Validation (2020-2022): cap ending equity $8,120 vs base $6,827; max DD improves from -65.48% to -59.04%.
- Holdout (2023-2026): cap ending equity $26,210 vs base $42,845; max DD improves from -66.50% to -59.49%.

The cap helps in train/validation and reduces drawdown in holdout, but loses substantial terminal wealth in the strong 2023-2026 period. Full-period terminal wealth retention at 25 bps is only 73.6%, below the preregistered 80% requirement; full-period max-drawdown improvement is 4.61 points, below the 5-point requirement.

## Decision
**Reject SOXL_CAP25_ROTATE under the preregistered decision rule.** This is the strongest result among the recent bounded defensive candidates in terms of preserving wealth while improving drawdown, but it still fails both full-period gates. Do not try 20%, 30%, or additional cap values.

This is useful evidence: the semiconductor concentration was a real source of historical downside, but a permanent cap sacrifices too much of the family's upside during strong markets. The next step should be event-level audit of *when* SOXL contributes to losses versus gains and whether a distinct, preregistered conditional allocation hypothesis is justified. Do not infer that a cap should be tuned to this holdout.

## Failed initial run
Workflow run ID `38120670456` failed only because synthetic test DataFrames had different column ordering; the test fixtures were corrected. The validated run above passed the tests and produced the authoritative artifact.

## Artifact hashes
- Summary SHA-256: `c27cf50a233e1db9829120f8c74f8f07a97c5edce5641020c12dab3bfcc762b8`
- Equity curves SHA-256: `76b42146470ec540063e3009a57b452d4f0e8e1b577f81ff620ca647ce5efd6c`
- Base weights SHA-256: `12931192a84ea1147e0c5346ee6509e38df158c4384067055202f5ea91014a41`
- Candidate weights SHA-256: `81a45de8909065597a7cf51942cfd3c24cfc81e513e6f7428b87cbe142a5fa5b`
- Bull-return panel SHA-256: `082e508cd2e60746a57224b14e57ad7d40a97320cfcc8b29d4f4a38ca8c83359`
- Manifest SHA-256: `e32c312888289a2afe50a6546f99e747a9eeb1c8ce48be59741619d07e04b092`
