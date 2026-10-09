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
