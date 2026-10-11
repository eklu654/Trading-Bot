# Fixed Structural Risk-Budget Results — 2026-10-11

## Run status
- Workflow: [validated workflow run](https://github.com/eklu654/Trading-Bot/actions/runs/38119997272) — **success**.
- Tested commit: `52caf4852f5e48041b07f2d315bd0ca71e8ffd14`.
- Tests: 16 passed, including risk-budget cap rules and re-entry state transitions.
- Actual TQQQ, QQQ adjusted-close B0 signals, $5,000 initial capital.
- Frozen aligned input: 4,189 sessions, 2010-02-11 through 2026-10-07.
- The script independently verified B0's zero-cost equity identity before publishing results.

## Results

| Candidate | Final at 0 bps | Max DD | Worst rolling 252-session return | Final at 10 bps | Max DD at 10 bps |
|---|---:|---:|---:|---:|---:|
| B0 (100% target) | $4,040,315 | -73.53% | -72.64% | $3,964,236 | -73.64% |
| RB95 (95% cap) | $3,235,188 | -71.31% | -70.42% | $3,177,290 | -71.42% |
| RB90 (90% cap) | $2,559,710 | -68.94% | -68.07% | $2,516,292 | -69.05% |

RB95 reduces maximum drawdown by only about **2.23 percentage points** while sacrificing **19.93% of terminal wealth**. RB90 reduces maximum drawdown by about **4.59 points** but sacrifices **36.65% of terminal wealth**. Results retain the same trade-off across 10/25/50 bps; neither candidate meets the preregistered rule requiring at least 90% of B0 terminal wealth plus a material downside improvement.

**Decision: reject both fixed exposure caps.** Do not sweep 91%, 92%, 93%, etc. This does not mean structural risk budgeting is inherently wrong; it means simply scaling this single-TQQQ B0 exposure down is too costly relative to the modest drawdown improvement.

## Next direction
Move away from isolated TQQQ-only scaling. The next useful research question is whether **family-level allocation and rotation** among leveraged ETF families can reduce correlated downside without leaving the whole portfolio in cash or applying a blanket bull/bear switch. Preserve the project constraint that incompatible bull/bear pairs from the same family should not be held simultaneously. Any multi-family test must have:
- a same-date benchmark and explicit warm-up/data-availability policy;
- no synthetic TQQQ/SOXL/SPXL history mislabeled as actual;
- family-specific position rules and a fixed total exposure budget;
- predefined downside and terminal-wealth criteria, with no broad parameter sweep.

Keep B0 as the unchanged research control. None of the tested defenses is approved for paper/live trading. A pre-2010 stress test remains a separately labeled synthetic daily-reset simulation, not actual TQQQ history.

## Reproducibility
- QQQ frozen input SHA-256: `9effae302dbe8101888850e8cb952fd3f74a72d3e13b69c420a89552b6e1b2d1`
- TQQQ frozen input SHA-256: `56b9d8ca2eaa5c4a418e55c8ecbd9c44980484095c88043e0e14cd4647c08860`
- Summary SHA-256: `edc7804c2ff397d4a79cfeda84c1f876e39751e8e3bdf8a37ce8c8a30b827791`
- Equity curves SHA-256: `67de0b87ec10b56b63a9b01e17531c1b0864bd9af29e26979e1763887f49dc49`
- Manifest SHA-256: `13c68fc80e70ea838a9ebc11010cd20014f78c09e07f33ee7658ba810b51d148`


## Initial workflow failure
The first attempt, workflow run ID `38119950698`, passed all 16 tests but failed at script startup because direct execution could not resolve the `research` package import. The script now supports both package and direct-script imports; the corrected workflow run ID `38119997272` passed and produced the artifact cited above.
