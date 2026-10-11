# B0 Canonical Reconciliation + Bounded Defense Decision — 2026-10-11

## Status
- Matrix workflow: PASS, run [#29](https://github.com/eklu654/Trading-Bot/actions/runs/38117700318).
- Branch: `research/qqq-slow-bear-audit`.
- Commit: `959c860656d4523afd54e02b6ce8fee5fc2b95ba`.
- No defense candidate promoted. Do not expand the parameter search based on these results.

## Canonical baseline verification
- Evaluation dates: 2010-02-11 through 2026-10-07, aligned to the canonical B0 replay.
- Initial capital: $5,000.
- B0 signal: QQQ adjusted close, -4.5% daily shock and +10% recovery from the running low.
- Execution: close signal executes next open; prior exposure earns overnight return, new exposure earns intraday return.
- Independent same-input B0 signal match: `true`.
- Matrix B0 final balance: $4,040,314.66761454.
- Independent canonical-equity final: $4,040,314.667614526.
- Absolute terminal-equity difference: $0.000000012 (floating-point noise).
- B0 max drawdown: -73.5343%, peak 2021-11-19, trough 2022-12-28.
- Buy-and-hold on the same snapshot: $2,094,668.65 final, -81.6598% max drawdown.
- The script now fails if canonical signal/equity reconciliation or the 24 B0 identity rows fail.

Note: an earlier canonical workflow download ended about $0.60 higher despite the same date span. Separate Yahoo Finance downloads can produce slightly different snapshots. The authoritative comparison above uses the *same frozen inputs within run #29*, and independently matches to effectively zero error.

## Bounded defense results
All figures below use actual TQQQ, QQQ adjusted-close DMA signals, $5,000 initial capital, the same date window, and 10 bps per exposure change unless stated otherwise.

| Strategy | Final balance | Max drawdown | Versus B0 final | Drawdown improvement |
|---|---:|---:|---:|---:|
| B0 baseline | $4,040,315 | -73.53% | — | — |
| B0 + 175-DMA, 50% below DMA | $1,959,798 | -53.20% | -51.5% | +20.3 pp |
| B0 + 150-DMA, 50% below DMA | $2,257,669 | -57.23% | -44.1% | +16.3 pp |
| B0 + 175-DMA, 25% below DMA | $1,197,706 | -47.34% | -70.4% | +26.2 pp |
| B0 + 150-DMA, 25% below DMA | $1,467,885 | -48.03% | -63.7% | +25.5 pp |

At zero cost, the best drawdown rows are 175-DMA/25% exposure below DMA (-46.82%, final $1.287M) and 150-DMA/25% exposure (-47.62%, final $1.591M). The 175-DMA/50% row ends at $2.069M with -53.04% drawdown.

## Decision
Reject these DMA overlays as current strategy candidates. They do reduce maximum drawdown, but even the more balanced 175-DMA/50% variant cuts terminal wealth by roughly half and the 25% variants sacrifice substantially more. The COVID-period return is also lower than B0, consistent with a recovery-participation cost. The result is a real risk/wealth trade-off, not a dominant improvement.

Per the predeclared stopping rule, do not add more DMA periods or exposure levels. Preserve B0 unchanged. Any next experiment must be a separately preregistered, bounded idea with an explicit re-entry/recovery-cost hypothesis, not a finer search of this rejected family.

## Reproducibility
- Frozen input SHA-256: `6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55`
- Matrix SHA-256: `a6d392c60363c79223b5adc67fa8034a67b2dac28b8d3dc427098655ba85561a`
- Periods SHA-256: `e83ab787966e2869611ea1efd6a9ea966229a52c803d4a26bca9d36a7b432b1c`
- Artifact: `tqqq-actual-partial-dma-matrix`, attached to [run #29](https://github.com/eklu654/Trading-Bot/actions/runs/38117700318).
