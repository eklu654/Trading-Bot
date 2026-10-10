# Hand-Maintained Fed Event Table vs FRED — Reconciliation Result — 2026-10-10

## Status

The reproducible FRED reconciliation workflow completed successfully. This is a diagnostic comparison, not a finding that the event table is definitively wrong or right. No event dates were automatically changed and no strategy was promoted.

- Workflow run: [38042891664](https://github.com/eklu654/Trading-Bot/actions/runs/38042891664)
- Branch: `research/qqq-slow-bear-audit`
- Workflow head SHA: `f7a26ce78d7b93da94057d7f1535cb64a1a607fe`
- Artifact: [fed-event-table-fred-reconciliation](https://github.com/eklu654/Trading-Bot/actions/runs/38042891664/artifacts/11666478522)
- Artifact digest: `sha256:d00952feeef13b61db50d1a2bed4dfb9731193bc20bf88e67a40c064ce49379e`
- Event-table source SHA-256: `3ba404301c69b486596bfa1588bf59ec7e7811a94eb99ad76bc3b09e5d38b042`
- FRED series input SHA-256: `cdce0c94ad53cf95e9b443e29318ea622573f9cffd23192bc8f233dde96cff6d`

## Measured results

The ledger covers 78 hand-maintained events dated 1999–2026 and 16,084 FRED observations from 1982-09-27 through 2026-10-09.

- Listed new rate appears on or after every listed event date: **78/78**.
- Listed new rate is seen within seven calendar days for every event: **78/78**.
- New-rate mismatches on or after the listed event date: **0**.
- Prior-rate mismatches: **3**, of which one is an omitted prior-rate field rather than a contradictory numeric value.

The three prior-rate flags are:

| Listed event date | Listed prior → new rate | FRED last rate before event | FRED first rate on/after event | Diagnostic |
|---|---:|---:|---:|---|
| 1999-06-30 | blank → 5.00% | 4.75% | 5.00% | Prior rate is blank in the table; the observed +0.25pp change matches the listed move. |
| 2015-12-17 | 0.125% → 0.375% | 0.375% | 0.375% | FRED already shows the new rate on 2015-12-16, one calendar day before the table date. |
| 2016-12-15 | 0.375% → 0.625% | 0.625% | 0.625% | FRED already shows the new rate on 2016-12-14, one calendar day before the table date. |

## Interpretation and limits

The 2015 and 2016 flags suggest a date-convention/alignment question: the hand-maintained table may use an announcement/action date while the daily FRED target series reflects the new rate on the preceding observation date. These flags alone do **not** establish that the table dates are wrong; announcement timestamps, effective dates, and FRED's daily observation convention must be checked against official Federal Reserve records before changing anything.

The current script checks nearby rate values, not whether every event has the correct official announcement timestamp or whether the difference changes a causal strategy signal. It also does not yet report the full duration of every discrepancy between a table-implied daily series and FRED. That is the next validation step if the official date convention confirms a meaningful difference.

## Decision / next step

1. Keep the hand-maintained event table unchanged for now.
2. Manually verify the 2015-12-16/17 and 2016-12-14/15 cases against official FOMC statements and implementation notes, including release time and effective date.
3. Establish and document one explicit convention for when a rate change becomes usable by a close-based signal.
4. Only if that convention changes the causal Fed-state series, create a separately versioned input and rerun the frozen Fed validation. Do not retune on the already-inspected 2018/2022 episodes.

This check found **two one-day alignment flags plus one missing prior-rate annotation**, not a demonstrated strategy defect. B0 and all promotion gates remain unchanged.
