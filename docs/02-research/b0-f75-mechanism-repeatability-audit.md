# B0 vs F75 Mechanism Repeatability Audit

Status: preregistered; implementation pending. Research branch: `research/qqq-slow-bear-audit`.

## Research question
Does frozen F75 repeatedly improve the balance between bear-market survival and recovery participation relative to canonical B0, or is the aggregate advantage concentrated in a single historical regime?

## Frozen comparators
- **B0:** canonical control artifact; immutable.
- **F75:** exact frozen implementation/signals; no threshold optimization or edits during this audit.
- **Starting equity:** $5,000 where replay convention requires an account seed.
- **Costs:** 0, 25, and 50 basis points only where equivalent canonical artifacts are available.
- **Execution:** existing causal close-to-next-open convention. No same-close lookahead.

## Fixed episode set
1. 2000–2002 (dot-com bear)
2. 2007–2009 (global financial crisis)
3. 2011 (debt-ceiling / euro-area stress)
4. 2015–2016 (China/oil and growth scare)
5. 2018 (Q4 selloff)
6. 2020 (COVID crash and rapid recovery; separate archetype)
7. 2022–2024 (inflation/Fed tightening and slow recovery)

Use documented, fixed episode boundaries from the existing data/episode definitions. Do not adjust boundaries after inspecting F75 outcomes. If data coverage does not support an episode or an ETF's inception, mark it unavailable; do not fabricate pre-inception leveraged ETF history.

## Required paired output per episode
- Explicit start/end and boundary convention
- B0/F75 start equity, end equity, return, and within-episode max drawdown
- Defensive-state sessions, average exposure, turnover, modeled costs
- Exit/re-entry dates and re-entry lag
- Equity change attributable to exposure avoided during declines versus gains missed during rebounds
- Exposure restored in the first 20 and 60 sessions after the episode low
- Incremental F75-minus-B0 P/L and drawdown change

## Aggregate repeatability summary
- Number of episodes F75 wins/loses on return and drawdown
- Median and range of paired return and drawdown differences
- Per-episode contribution to total incremental P/L
- Cost sensitivity at supported cost levels
- Separate fast-crash (COVID) versus prolonged-bear results

## Validity checks
- B0 signal and equity replay reconcile to the canonical artifact within the existing tolerance.
- F75 signal sequence hash/definition remains frozen.
- Execution timestamps are causal; a close-derived signal affects the next eligible open only.
- Episode windows and recovery windows are deterministic and tested, including overlapping event labels.
- Every reported difference reconciles to the daily equity ledger.
- Missing history, missing prices, and uncompleted recovery windows are explicitly flagged.

## Decision rule
This is an attribution/repeatability test, not a threshold search. Do not promote F75 because of aggregate terminal balance alone. A positive result must show repeated risk benefit across distinct stress episodes without a systematic recovery-participation penalty. If results are concentrated in 2022–2024, retain F75 for prospective shadow observation only.

## Current known context
At 25 bp, previously verified aggregate figures were B0 $3,852,657 / -73.80% max drawdown and F75 $3,898,853 / -67.99%. Excluding 2022–2024, the reported stitched values were approximately B0 $2.734M and F75 $2.528M. These are motivation and context, not the result of this preregistered episode audit.

## Audit trail
- 2026-10-11: User approved testing mechanism repeatability rather than optimizing thresholds; B0 remains control and F75 rules remain frozen.
- 2026-10-11: Protocol written before new episode-level results are inspected.

## Latest fixed-attribution run — 2026-10-16

Workflow [38851092843](https://github.com/eklu654/Trading-Bot/actions/runs/38851092843) completed successfully. The report covers the fixed 2010-02-11 through 2026-10-07 common period (4,189 sessions), with the canonical B0 artifact and F75 rules held fixed. Episode coverage: 5 of 7 defined episodes measured and accounting-validated; 2 marked unavailable. At 25 bp, F75 had higher terminal return in 3/5 measured episodes and improved episode max drawdown in 3/5. This is mixed, not universal, episode repeatability.

Full-period paired terminal equity from $5,000 initial equity:

| Modeled costs | B0 terminal equity | F75 terminal equity | F75 increment |
|---|---:|---:|---:|
| 0 bp | $4,040,315 | $4,124,681 | +$84,366 |
| 25 bp | $3,852,657 | $3,898,853 | +$46,195 |
| 50 bp | $3,673,277 | $3,684,972 | +$11,695 |

At 25 bp, full-period maximum drawdown was approximately -73.80% for B0 and -67.99% for F75, a 5.80 percentage-point improvement. At 50 bp, the terminal-equity advantage narrows to about $11.7k on a ~$3.67M ending balance, so the result is materially cost-sensitive.

**Decision remains unchanged:** do not promote F75 from this aggregate result. The fixed episode test has only 5 measurable episodes, and 2/5 measured episodes did not show both a return win and drawdown improvement. Inspect per-episode attribution, recovery participation, and concentration of incremental P/L before any promotion. Keep B0 frozen and F75 prospective-shadow-only. The report's own interpretation is attribution, not a promotion decision.

