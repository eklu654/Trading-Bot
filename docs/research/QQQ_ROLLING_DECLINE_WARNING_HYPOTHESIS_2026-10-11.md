# QQQ Rolling-Decline Warning Hypothesis — 2026-10-11

## Status
Pre-registered research proposal only. No backtest result yet; no strategy change. B0 remains frozen.

## Hypothesis
A causal warning based on the magnitude of QQQ's peak-to-close decline over a rolling window may detect accelerating and gradual bear regimes that a one-day -4.5% shock trigger misses.

## Exact signal definition
At each close t, for window Y trading sessions:
- prior_peak_Y(t) = maximum QQQ close over the trailing Y sessions ending at t (including t).
- drawdown_Y(t) = QQQ_close(t) / prior_peak_Y(t) - 1.
- trigger when drawdown_Y(t) <= -X%.
The signal is evaluated at close t and may only affect exposure starting the next trading session. Use adjusted close consistently for signal construction; align the price field with the frozen B0 benchmark conventions before any direct performance comparison. A signal that fires only after the event's trough is not counted as useful early detection.

## Small, predeclared screening matrix
- X = 5%, 7.5%, 10%, 12.5%, 15%.
- Y = 10, 20, 40, 60 trading sessions.
- 20 combinations; no finer optimization until out-of-sample behavior is known.
- Compare against B0 unchanged, plus signal-only event diagnostics. Do not tune X/Y separately on each historical crisis.

## Evaluation protocol
1. Freeze and hash QQQ/TQQQ daily data; record provider, symbols, fields, date range, retrieval time, missing sessions, and corporate-action adjustment convention.
2. Evaluate QQQ index/proxy event coverage from 1999 onward and broad-index historical event coverage only where the chosen source has verified data. Do not represent QQQ data as existing before its actual history.
3. Predefine major events independently of candidate signals, using a peak-to-trough index decline threshold (proposed >=20%) plus event merging rules; report sudden shocks and slow declines separately. Also include named stress windows (2000–02, 2007–09, 2020, 2022) as diagnostic checks, not the only evaluation set.
4. For each event report: trigger before trough (yes/no), sessions from event peak to first warning, drawdown already incurred at signal, share of peak-to-trough loss remaining after signal, false-warning count, warning-days/defensive-days, and recovery delay / V-shaped recovery opportunity cost.
5. Simulate any exposure overlay only after defining an explicit, causal re-entry rule. Compare ending equity, max drawdown, worst event loss, time in cash, and recovery participation against frozen B0 on identical actual-TQQQ-era dates. A detection score alone does not prove portfolio survivability.
6. Use chronological development/validation splits and a final untouched holdout. If thresholds are selected on the same historical events used for reporting, label those results exploratory. Purge overlapping forward outcome windows when training any classifier.
7. Include one-day -4.5% shock trigger, 100-DMA, and buy-and-hold as diagnostic baselines; do not alter B0.

## Principal risks / failure modes
- Rolling high is a local peak; a short Y can trigger on ordinary corrections, while long Y can be slow and remain armed through recoveries.
- A trigger can be technically early but occur after most of the loss is already incurred.
- Repeated trigger/reset logic can whipsaw; re-entry design can dominate results.
- Overlapping X/Y variants create multiple-testing risk.
- Daily-close signals must not receive same-close fills.
- A QQQ rule evaluated on TQQQ outcomes is only validated for the tested sample/regime; it cannot guarantee future survival or be assumed to generalize to pre-inception periods.

## Decision gate
Do not promote any X/Y setting unless it improves tail-risk measures versus B0 on identical data without an unacceptable ending-wealth/recovery penalty, and remains useful on untouched chronological data. Report every tested variant, not just the winner.

## Next action
Implement a short, deterministic research script and manually dispatched workflow that runs the fixed 20-cell matrix, emits event-level CSV + summary Markdown, and records data hashes. Review artifacts before considering any further tuning.
