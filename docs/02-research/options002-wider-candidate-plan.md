# OPTIONS-002 Wider-Wing Candidate Research

**Status:** Manual research workflow prepared — 2026-09-29

## Purpose

The original 16-delta / 2-point iron condor is retained as a capital-feasibility probe. It is not treated as the final methodology-aligned candidate.

This branch adds a separate manual GitHub Actions workflow for three frozen development candidates:

1. **20-delta shorts / $5 fixed wings**
2. **20-delta shorts / $10 fixed wings**
3. **20-delta shorts / 10-delta long wings**

Each candidate is tested across ALL_DAYS, BROAD_SIDEWAYS, and TURBULENT_ONLY under conservative and midpoint execution assumptions.

## Common rules

- SPY
- 45 DTE target
- 30–60 DTE eligible
- one position at a time
- 50% profit target
- 21-DTE time exit
- defined risk; no undefined-risk 2x-credit stop
- $5,000 account feasibility
- 50% aggregate BPR ceiling
- 3%, 5%, and 7% maximum defined-risk sensitivity bands
- $0.65 per-contract fee model
- candidate rejections are retained rather than silently discarded

## Why these three candidates

The fixed-width tests isolate the effect of materially wider wings while keeping the rest of the structure stable.

The 20/10-delta construction tests a different, delta-defined wing methodology. It avoids assuming that a fixed dollar wing has the same economic meaning across different SPY price levels.

## Interpretation rules

These are development candidates, not deployment recommendations.

A candidate must survive:

1. account-feasibility screening;
2. realistic conservative fills;
3. common-date comparison with ETF-001;
4. regime analysis;
5. chronological development/validation;
6. an untouched final holdout.

No candidate is promoted because it has the highest historical return in the development sample.

## Execution

The workflow is intentionally `workflow_dispatch` only. It does not automatically trigger on research-file pushes, avoiding another expensive full historical run merely because this research branch is being developed.

The resulting artifacts should be reviewed before any candidate is incorporated into the main historical workflow.