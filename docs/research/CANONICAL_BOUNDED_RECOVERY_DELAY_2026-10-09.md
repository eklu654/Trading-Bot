# Bounded recovery delay — experiment plan

Date: 2026-10-09  
Status: **CODE COMMITTED; Actions result pending.**

## Motivation
The recovery-gated structural confirmation candidate preserved COVID at an 8-session exception but lost terminal wealth and worsened max drawdown because it waited for the structural matrix to clear after the 2022-07 recovery attempt. Test whether a hard maximum wait limits this opportunity cost.

## Frozen rule
- Base: canonical QQQ -4.5% shock / +10% from running low recovery, $5,000, close-to-next-open.
- Structural/fast flag parameters unchanged: 150-DMA, 100-DMA, 63-session return <= -20%, 252-session drawdown <= -20%, VIX >= 30; structural flag = QQQ below 150-DMA and 100-DMA below 150-DMA; fast flag = QQQ below 100-DMA and any shock criterion true.
- Fast-recovery exception fixed at 8 sessions from running low.
- When recovery takes more than 8 sessions and either matrix flag is true, delay re-entry until the matrix clears or the maximum wait expires, whichever comes first. Sensitivity caps: 3/5/10 sessions.
- Re-entry still requires QQQ to be >=10% above the current running low. A new low resets the pending wait and requires a fresh recovery attempt.
- This is a small exploratory sensitivity set, not an optimized threshold.

## Evaluation
B0 unchanged; actual TQQQ live-fund history and a separately labeled synthetic 3x QQQ diagnostic from 1999. Compare ending balance, CAGR, max drawdown, worst rolling year, COVID/2022 windows, and every recovery attempt/release. Synthetic returns are not actual TQQQ history.

## Audit
- Code: `research/canonical_bounded_recovery_delay.py`
- Workflow: `.github/workflows/canonical-bounded-recovery-delay.yml`
- Code commit: `5e4a159685c7dba9075d4cfd01b124890db9802a`
- Workflow commit: `d23f20b42e2fcec4dae39d51a9485520b5f6a746`
- Add run/artifact/result metadata after completion.
