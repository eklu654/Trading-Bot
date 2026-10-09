# Canonical recovery event quality audit — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; workflow pending.**

## Question
At the exact close where the canonical QQQ shock/recovery rule would re-enter after a 10% rebound from the post-shock low, do the matrix's structural and fast-shock conditions distinguish recoveries that fail from those that continue?

## Frozen definitions
- Signal: QQQ adjusted close; shock <= -4.5% daily, recovery >= +10% from running low after shock.
- Structural flag at recovery decision: QQQ below 150-DMA and 100-DMA below 150-DMA.
- Fast-shock flag at recovery decision: QQQ below 100-DMA and at least one of 63-session return <= -20%, 252-session drawdown <= -20%, or VIX >= 30.
- Outcome labels: whether QQQ later closes below the recovery trigger level or below the event's low within 20/60/120/252 sessions; forward returns and minimum forward returns also recorded.
- Data is QQQ/VIX from 1999 onward. No TQQQ performance is calculated.

## Limitations
This is a small, event-level descriptive audit. Forward windows can overlap; the same event may count in multiple horizons; the modern sample has already been examined. Precision/recall are diagnostic summaries, not significance tests, not proof of generalization, and not a strategy backtest.

## Audit
- Code: `research/canonical_recovery_event_quality.py`
- Workflow: `.github/workflows/canonical-recovery-event-quality.yml`
- Code commit: `91874185a73d23359ed1dd9bc37a3174dacf66ec`
- Workflow commit: `b9aba2f56d0de48b6520217ea07b43ad06e1c50f`
- Results and run metadata will be appended after inspecting the artifact.


## Results

- Workflow: [run 37913220046](https://github.com/eklu654/Trading-Bot/actions/runs/37913220046), job completed successfully.
- Artifact ID `11607980290`, SHA-256 `47ca48336513770609e4c38fe860e095db71a7c7ae145d55fd260253f9761fd2`.
- Data: 6,938 QQQ/VIX observations from 1999-03-10 through 2026-10-07; 38 completed QQQ -4.5% / +10% events.
- At the exact B0 recovery decision close, the structural flag was active in 23/38 events and the fast-shock flag in 27/38. The sample is small, overlapping, and already examined.

### Descriptive event classification

Target = whether QQQ closes below the event's prior low within the following horizon:

| Horizon | Signal at recovery | Events flagged | Precision | Recall | Specificity |
|---|---|---:|---:|---:|---:|
| 60 sessions | Structural condition | 23/38 | 60.9% | 66.7% | 47.1% |
| 60 sessions | Fast-shock condition | 27/38 | 59.3% | 76.2% | 35.3% |
| 120 sessions | Structural condition | 23/38 | 73.9% | 65.4% | 50.0% |
| 120 sessions | Fast-shock condition | 27/38 | 74.1% | 76.9% | 41.7% |

The base rate for a new low was 21/38 by 60 sessions and 26/38 by 120 sessions. Specificity remains poor: the flags frequently activate on recoveries that do not make a new low. A different outcome—falling below the +10%-above-low recovery threshold—occurred in 33/38 events by 60 sessions, making that target too common to be a useful discriminator by itself.

### Illustrative counterexamples
- **2019-01-07:** structural condition true, fast-shock false; QQQ gained about 16.5% over the next 60 sessions and did not make a new low within 60 sessions. A structural gate would have blocked a successful recovery.
- **2020-03-26:** structural condition false, fast-shock true; QQQ gained about 28.8% over the next 60 sessions and did not make a new low within 60 sessions. A sticky fast-shock gate would have blocked the COVID rebound despite the sharp recovery.
- **2022-07-19:** both conditions true; QQQ lost about 11.8% over the next 60 sessions and made a new low. This is a valid example of the detector catching a failed recovery, but not enough to outweigh the false positives.

## Decision
The current structural/fast-shock conditions show some signal about future weakness but are too nonspecific at recovery points to safely override B0. Do not turn these descriptive metrics into a new production rule. A next experiment, if continued, should focus on a recovery-confirmation rule with an explicit fast-rebound exception, then compare against the same B0 control. The 38-event results are exploratory and not independent validation.
