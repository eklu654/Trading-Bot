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

Official-source review confirms the distinction for both flagged hikes:

- **2015:** The FOMC statement was released on December 16, 2015 at 2:00 p.m.; the new target range was effective December 17. The official implementation note explicitly states the December 17 effective date. [FOMC statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20151216a.htm) · [Implementation note](https://www.federalreserve.gov/newsevents/pressreleases/20151216a1.htm)
- **2016:** The FOMC statement was released on December 14, 2016 at 2:00 p.m.; the new target range was effective December 15. The official implementation note explicitly states the December 15 effective date. [FOMC statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20161214a.htm) · [Implementation note](https://www.federalreserve.gov/newsevents/pressreleases/20161214a1.htm)

Therefore, the two one-day flags are consistent with the event table using **effective dates** while the FRED daily target-rate observation reflects the newly announced target on the **announcement date**. This is a real difference in timestamp convention, but not evidence that either source is inherently incorrect. Because the statements were released at 2:00 p.m. ET, whether the new state can be used for a close-based signal depends on the strategy's explicit information-availability and execution convention. The current audit has not established that these two rows alter any strategy result.

The current script checks nearby rate values, not every official announcement timestamp or the portfolio impact of different timing conventions. It also does not report the full duration of every discrepancy between a table-implied daily series and FRED.

## Decision / next step

1. Keep the hand-maintained event table unchanged; it records effective dates for these two moves.
2. Preserve the distinction between announcement-date information and effective-date state in future Fed-state construction.
3. Before changing any strategy inputs, define whether the close signal may use an announcement released at 2:00 p.m. ET that same trading day, and test that convention causally (signal at close, execution no earlier than next open).
4. Only if a separately specified timing test changes the causal Fed-state series, create a versioned input and rerun frozen validation. Do not retune on the already-inspected 2018/2022 episodes.

This check found **two explained announcement/effective-date convention differences plus one missing prior-rate annotation**, not a demonstrated strategy defect. B0 and all promotion gates remain unchanged.
