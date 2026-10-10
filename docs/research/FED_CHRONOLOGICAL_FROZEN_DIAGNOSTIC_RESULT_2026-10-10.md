# Frozen Fed Chronological Diagnostic — Corrected Run Result

**Date:** 2026-10-10  
**Classification:** Retrospective episode diagnostic only; not a trading signal or TQQQ backtest.  
**Workflow run:** [38093382374](https://github.com/eklu654/Trading-Bot/actions/runs/38093382374)  
**Artifact:** [fed-chronological-frozen-validation](https://github.com/eklu654/Trading-Bot/actions/runs/38093382374/artifacts/11684624083)  
**Code commit:** `dbd6807e2eac500e44e425ce0051b8d52cd5f77b`

## Measurement corrections

- Completed episodes now require a full 60/120/252-session forward horizon; otherwise the field is `NaN`.
- A terminal shock still in progress is emitted as an explicit right-censored episode rather than silently omitted.
- Output names explicitly call the combined Fed/duration condition a **retrospective label**, not a live warning.
- A JSON manifest records normalized NDX/Fed input hashes, date coverage, row counts, package versions, censoring counts, complete-horizon counts, and output hashes.
- The workflow now uploads the JSON manifest alongside CSV outputs.

## Run facts

- Status: PASS; 10,335 NDX daily rows from 1985-10-01 through 2026-10-08; requested end is exclusive 2026-10-09.
- Fed series: 16,085 observations from 1982-09-27 through 2026-10-10. Calculations use only observations on or before each episode date, so the later last observation is not used for earlier event labels.
- NDX input SHA-256 (normalized series): `467190acbe30c52fc7da07dbdecd0675d4b544e14b1bbb9ba1967f17297b23e1`.
- Fed input SHA-256 (normalized series): `4c3d89f130b7a4f16945e882983b8625aa0c4e234326c17212cbdf324c97f522`.
- 51 shock-to-recovery episodes were detected; this particular sample ended with no active/censored episode. One episode lacked each full 60-, 120-, and 252-session post-recovery horizon and was excluded from the respective horizon summaries.
- The run is reproducible relative to the recorded normalized data hashes, but the workflow still downloads vendor data at runtime; it does not yet replay from a committed frozen raw input file.

## Results — descriptive, not predictive

Frozen retrospective label: Fed target rose at least 50 bp over the prior 63 calendar days **measured at recovery**, and recovery took more than 30 NDX sessions from the shock.

Only two completed episodes received this label, both in 2022:
- Shock 2022-05-05; recovery 2022-07-19 after 50 sessions. Following 120-session NDX return: **-9.31%**.
- Shock 2022-09-13; recovery 2022-11-11 after 43 sessions. Following 120-session NDX return: **+12.48%**.

Thus one of the two labeled episodes had a negative 120-session post-recovery return and one had a positive return. The label does not consistently identify subsequent weakness even in the two 2022 episodes. The 120-session return begins after recovery; it is not a portfolio result or a test of an exit made at the shock.

An exploratory **recovery-time** persistent-tightening label identified four episodes (two in 2000 and two in 2022); three had negative 120-session post-recovery returns. This is tiny-sample, outcome-conditioned description, not evidence for a causal signal. In particular, it cannot tell a live strategy when to exit.

## Decision

- The code/accounting corrections run successfully.
- The original hypothesis is **not validated as a tradable defense rule**: both duration and the Fed-change label are determined at/after recovery, too late to define an early defense decision.
- Do not promote or backtest the retrospective label as though it were causal. The next research candidate, if any, must be separately specified using only data available at a concrete decision timestamp, then tested as a portfolio rule with next-open execution and actual TQQQ data for its available period.
- No strategy thresholds were changed; no TQQQ portfolio backtest or paper/live trade was run. B0 remains the working control.
