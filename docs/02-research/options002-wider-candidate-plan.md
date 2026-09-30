# OPTIONS-002 Wider-Wing Candidate Research

**Status:** Manual research workflow prepared on 2026-09-30.

## Purpose

The original 16-delta / 2-point iron condor remains a capital-feasibility probe. It is not treated as the mature methodology-aligned options candidate.

This manual workflow evaluates three frozen development candidates:

1. 20-delta shorts with $5 fixed wings.
2. 20-delta shorts with $10 fixed wings.
3. 20-delta shorts with 10-delta long wings.

Each candidate is evaluated across ALL_DAYS, BROAD_SIDEWAYS, and TURBULENT_ONLY, with conservative and midpoint fills.

## Common controls

- SPY.
- 45 DTE target with 30–60 DTE eligibility.
- One contract and one concurrent position.
- 50% profit target.
- 21-DTE time exit.
- Defined risk; no undefined-risk 2x-credit stop.
- $2,000, $5,000, and $10,000 account-feasibility checkpoints.
- 50% modeled aggregate BPR ceiling.
- 3%, 5%, and 7% maximum defined-risk sensitivity bands.
- $0.65 per-contract fee model.
- Candidate rejections are retained rather than silently discarded.

## Why these candidates

The fixed-width candidates isolate wider wings while holding the rest of the structure constant. The 20/10-delta candidate tests delta-defined protective wings rather than assuming a fixed dollar width has the same meaning at every SPY price.

## Interpretation

These are research candidates, not deployment recommendations.

A candidate must survive account-feasibility screening, conservative fills, common-date comparison with ETF-001, regime analysis, chronological development/validation, and an untouched final holdout before it can be considered for a later promotion gate.

The highest development-sample return is not itself a selection rule.

## Execution

The workflow is deliberately `workflow_dispatch` only. It does not trigger the full historical workflow automatically when research code changes.

After execution, review the uploaded artifact bundle before incorporating any candidate into the main historical research workflow.
