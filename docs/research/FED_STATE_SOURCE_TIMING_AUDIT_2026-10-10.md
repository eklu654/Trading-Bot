# Fed-State Source and Timing Audit — 2026-10-10

## Purpose and scope

Code-level audit only. This note identifies distinct Federal Reserve inputs and timing conventions already present in the repository so future tests do not accidentally treat them as one interchangeable signal. It does not claim a full event-by-event reconciliation to official FOMC records, and it does not change any strategy.

## Findings

### 1. Two materially different Fed inputs exist

**Hand-maintained event table**
- Defined as `FED_EVENTS` in `research/tqqq_three_layer_event_attribution.py`.
- Includes explicit action dates, changes, and resulting target rates from 1999 through 2026.
- `fed_series()` maps the latest table row with event date <= each market date to the market calendar.
- This table is used by the three-layer / synthetic historical research family. Its dates and values must be independently reconciled before the synthetic results can be treated as a reliable test of Fed-aware protection.

**FRED daily target-rate series**
- `research/canonical_shock_recovery_fed_dma_overlay.py` downloads `DFEDTAR`, `DFEDTARU`, and `DFEDTARL`; when bounds are available, it uses the midpoint as the target rate.
- It maps the daily Fed-derived state backward to the QQQ calendar and then shifts the mapped state by one QQQ session before using it.
- This is a different source and state-construction path from the hand-maintained event table.

These implementations must not be pooled or compared as if they use an identical Fed state history. The FRED state also depends on the specific classifier (90-day hike/cut counts and 12-month net rate change), not merely the listed rate values.

### 2. Causality is explicitly lagged in the actual-TQQQ overlay

The FRED-backed overlay documents that the state derived from a Fed observation is not used for the same QQQ close signal; it is shifted one market session. This is a conservative timing choice, but it should be preserved in all comparisons unless a new preregistered test changes it.

### 3. The hand-maintained event table has a separate timing risk

The event table records one date per policy move. This code-level inspection does not establish whether every listed date corresponds to the FOMC announcement date, the effective date represented in the daily target-rate series, or the correct information-available timestamp for a close-based signal. A one-session difference can change state at a shock/recovery boundary. This is a verification item, not a confirmed error.

## Required follow-up before relying on synthetic Fed results

1. Build a reconciliation ledger for each hand-maintained event: event date, prior rate, new rate, official announcement date/time, effective date (where different), and source citation.
2. Compare the table-implied daily target series against FRED's target-rate series after explicitly choosing an alignment convention; report every mismatch and its duration.
3. Re-run the already-frozen synthetic Fed/200-DMA candidate only if a mismatch is found that changes the intended causal signal. Preserve the original run and label any corrected run as a new input version.
4. Keep the actual-TQQQ FRED-backed tests and hand-maintained synthetic tests separately labeled. A candidate that improves the modern sample but fails the synthetic gate remains rejected under the existing preregistration.

## Decision

No new strategy is promoted. This source/timing reconciliation is the next higher-value validation task because it can identify a data-definition defect without tuning a strategy to the already-inspected 2018 or 2022 episodes.
