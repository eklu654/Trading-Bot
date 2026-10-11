# F75 Prospective Shadow Evaluation — Preregistration — 2026-10-11

## Purpose and decision status

The canonical-input Fed-DMA robustness replay completed in Actions run #15 and reproduced B0. F75 passed the historical screening gates, but its modest terminal-wealth edge disappears when 2022-2024 returns are excluded. This plan tests whether the frozen rule's drawdown benefit appears prospectively, without selecting new parameters from future results.

**This is shadow research only. It places no orders and does not authorize paper or live trading.**

## Frozen strategies

- **B0 control:** canonical QQQ adjusted-close daily shock threshold of -4.5%, exit until QQQ closes at least 10% above the running low; signal at close executes next open.
- **F75 candidate:** B0 plus a 75% TQQQ target while the existing sticky overlay is armed: QQQ below its 200-session SMA and one-session-lagged Fed state TIGHTENING_ACTIVE; overlay remains armed until QQQ closes at/above the 200-DMA. B0 defense always overrides.
- Starting shadow equity: $5,000 per strategy at the close of the first registered session, 2026-10-12. First return-bearing session is the next market session after initialization.
- Fixed cost assumption: 25 bps per full exposure change; also report 0 and 50 bps as sensitivities.
- Data: use the immutable canonical QQQ/TQQQ input through 2026-10-07 (SHA-256 6aa4088b7210a139da84553933778847cdffb4356c7751e7aa6fae2065214f55) and append new observations only after the frozen cutoff. Never rewrite historical frozen rows.
- Causal execution: close[t] signal is executed at open[t+1]; overnight return is earned by the previously held exposure and intraday return by the newly executed exposure.
- FRED state must be based only on observations available by the signal time and conservatively lagged one market session. Preserve raw observation dates and the computed state in the daily ledger.

## Observation horizon and outputs

- Collect 252 forward return-bearing market sessions from the registered start. No interim performance-driven changes.
- Each observation records source dates/hashes, QQQ close and 200-DMA, lagged Fed state, B0 signal, overlay state, F75 target, next-open exposure, daily strategy returns, transaction costs, and shadow equity.
- Publish cumulative equity, maximum drawdown and its dates, worst rolling 63-session return, turnover/exposure changes, and B0-relative wealth and drawdown differences at 0/25/50 bps.
- If data is missing, stale, duplicated, or fails canonical B0 reconciliation, mark that session invalid and do not silently forward-fill market prices or produce a new signal.
- Retain the daily ledger and workflow artifacts as the audit trail. No tuning of shock/recovery thresholds, DMA, Fed-state definition, exposure fraction, costs, or decision criteria during the observation window.

## Interpretation rules

- This is prospective after the registration date, but only one strategy was carried forward after reviewing historical results; it is not a randomized comparison and does not erase selection bias.
- Report the full observed path, not only terminal equity. A one-year result is descriptive and cannot establish a reliable estimate of rare-crash protection.
- At 252 sessions, review results against B0 and publish a decision memo. Do not automatically promote F75 even if metrics look favorable; require a separate operational, fill/reconciliation, and risk review before any paper-trading proposal.
- If the strategy materially underperforms B0 without the predeclared drawdown improvement, reject F75 and preserve B0. Do not repair it by searching nearby parameter values on the same forward period.

## Prerequisite

Before starting the ledger, implement and test a shadow-only scheduled workflow that:
1. downloads and verifies the canonical frozen input artifact,
2. appends new market observations without modifying the frozen history,
3. computes B0 and F75 signals using causal timing,
4. reconciles B0 against the canonical historical signal and equity,
5. stores the daily ledger persistently on the research branch, and
6. fails closed on missing data or reconciliation errors.

No broker API, order submission, account credentials, or live trading is part of this workflow.
