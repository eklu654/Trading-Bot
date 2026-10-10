# Actual-TQQQ Partial-DMA Matrix Audit — 2026-10-10

## Question and frozen setup

This report records the already-completed GitHub Actions run testing whether adding partial exposure below a QQQ moving average improves the B0 shock/recovery strategy's wealth/drawdown trade-off.

- Workflow run: [38089556724](https://github.com/eklu654/Trading-Bot/actions/runs/38089556724), success.
- Tested source commit: `26d3152fa3d52450e951883eb7d7ec0261731703`.
- Artifact: [tqqq-actual-partial-dma-matrix](https://github.com/eklu654/Trading-Bot/actions/runs/38089556724/artifacts/11682898823).
- Artifact digest: `sha256:50a9c2db3b04b6140bd2dc6b7818ef5e62b13ca4c38222883a32c0a02def52e8`.
- Frozen input SHA-256: `8b2b45074b9608ecd08ee2bb2242d4f8ebd61480ac2bf00c653cf2d29c1bd35d`.
- Actual TQQQ, QQQ adjusted-close signal, $5,000 reset at 250-session warmup date 2011-02-07; evaluation ends 2026-10-02.
- 4,186 frozen input rows; DMA lengths 100, 125, 150, 175, 200, 250; below-DMA exposure 100%, 75%, 50%, 25%, 0%; costs 0, 10, 25, 50 bp per exposure change.
- Close signal executes at next open. B0's defensive state overrides DMA exposure. DMA-only rows are diagnostics, not candidates.

## Results against B0

B0 ending equity was $1,816,681 at 0 bp, $1,782,473 at 10 bp, $1,732,303 at 25 bp, and $1,651,646 at 50 bp. Maximum drawdown was -73.53% at 0 bp and -73.80% at 25 bp.

Selected candidates (all on the same window):

| Candidate | Cost | Ending equity | Max drawdown | Ending equity vs B0 | Max-DD improvement vs B0 |
|---|---:|---:|---:|---:|---:|
| 150-DMA / 75% below | 0 bp | $1,517,184 | -65.71% | 83.5% | 7.83 pp |
| 175-DMA / 75% below | 0 bp | $1,485,549 | -64.17% | 81.8% | 9.36 pp |
| 150-DMA / 75% below | 25 bp | $1,374,436 | -66.16% | 79.3% | 7.64 pp |
| 175-DMA / 75% below | 25 bp | $1,355,909 | -64.51% | 78.3% | 9.29 pp |
| 150-DMA / 50% below | 25 bp | $1,001,730 | -57.64% | 57.8% | 16.14 pp |
| 175-DMA / 25% below | 25 bp | $658,111 | -48.11% | 38.0% | 25.69 pp |

The wealth-retaining end of this matrix improves drawdown by less than 10 percentage points but loses about 17–22% of ending equity. Larger drawdown reductions require substantially more terminal-wealth sacrifice. No tested partial-DMA candidate satisfies the existing 95%-of-B0 terminal-wealth gate at 25 bp.

## Chronological diagnostics

The segment ledger confirms the trade-off is not confined to one aggregate metric: reducing below-DMA exposure also materially reduces participation in strong periods, including the 2011–2015, 2016–2019, and 2020–2021 growth segments. The 2022–2024 segment is better protected by several reduced-exposure variants, but that benefit does not offset the full-period opportunity cost under the existing gates.

Segment rows use inherited continuous equity rescaled to $5,000 at the start of each reported period; they are not independent fresh-start portfolio simulations. These are retrospective stability diagnostics, not untouched holdouts.

## Data and code audit notes

- The script calculates moving averages on full QQQ history before slicing the evaluation window, preserving warmup.
- The manifest hashes the frozen input, matrix, and period CSVs and records common dates, costs, exposure levels, and execution convention.
- For below-DMA exposure of 100%, combined exposure equals B0 by construction; matching results are an internal consistency check, not an independent strategy.
- This matrix is a historical research diagnostic; it does not include funding costs, taxes, market impact, or broker-specific fill effects.

## Decision

Reject the simple partial-DMA overlay family for promotion under the current multi-objective gates. Do not tune further DMA lengths or exposure percentages from this same matrix. Keep B0 as the working control and pursue a causally justified state variable that can discriminate prolonged tightening-driven bears from rapid crash/recovery regimes. No strategy is promoted and no paper/live trading is authorized.
