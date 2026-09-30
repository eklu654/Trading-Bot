# ETF-001 Trend/Hysteresis Matrix Validation

**Status:** Active research — 2026-09-30

## Purpose

The ETF-001 trend matrix tests a small, predeclared set of moving-average and
hysteresis controls without selecting on the final holdout.

### Candidate grid

- MA window: 100, 125, 150, 175, 200, 225, 250 sessions
- Exit buffer: 0%, 1%, 2%
- Re-entry buffer: 0%, 1%, 2%
- Consecutive re-entry sessions: 1, 3, 5
- Cash allocation: 25%
- ETF sleeves: TQQQ, SPXL, SOXL

This produces 189 deterministic candidates.

## Chronological split

- **Train:** 2010-03-01 through 2019-12-31
- **Validation:** 2020-01-01 through 2022-12-31
- **Holdout:** 2023-01-01 onward

The matrix is ranked only on the training-period return/drawdown ratio, with
training Sharpe as the secondary tie-breaker.

The validation evaluator then reports fixed top-1, top-5, top-10, and top-25
training cohorts plus the existing 200-DMA/5-session baseline. Validation and
holdout results are reporting outputs, not selection inputs.

## Execution convention

Signals are generated from the close of session *t* and shifted one session
before they affect portfolio returns. This prevents same-close signal/return
look-ahead in the daily model.

The matrix uses adjusted closes for return accounting and unadjusted closes for
the moving-average signal.

## Interpretation gate

A candidate does not become an authoritative ETF-001 rule merely because it
ranks highly in the training sample. Promotion requires:

1. validation stability;
2. untouched holdout confirmation;
3. robustness across nearby parameter choices;
4. realistic cost and execution assumptions;
5. compatibility with the portfolio's hard risk limits; and
6. comparison against the existing ETF baseline and the options component.

The 2026 holdout is therefore protected from optimization.


## Local parameter robustness

After generating the 189 candidates, `research/analyze_etf001_robustness.py`
examines each candidate's immediate parameter neighborhood. A neighbor changes
exactly one parameter by one step in the declared grid while keeping the other
parameters fixed.

The robustness analysis uses training-period results to characterize whether a
candidate sits inside a reasonably stable region rather than on an isolated peak.
It reports neighbor return/drawdown-ratio mean, dispersion, positive fraction, and
neighbor Sharpe statistics.

Validation and holdout results are carried alongside the robustness report for
inspection only. They are not inputs to the training robustness score.

This is a diagnostic, not a new optimized trading rule. A robust candidate still
has to pass the chronological validation, untouched holdout, execution, and risk
gates.
