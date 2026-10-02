# ETF-exit switcher overlap correction — 2026-10-01

The ETF-exit options switcher is intended to choose between ETF exposure and a
capital-feasible defined-risk options position. It must not hold both at the
same time.

## Correction

The prior evaluator only required the option entry date to occur while all
ETF sleeves were flat. It then continued to apply ETF daily returns whenever
active_sleeves > 0, even if an accepted options trade was still open.

That could create simultaneous ETF + options exposure after an ETF re-entry
that occurred before the option trade's exit date.

The evaluator now:

1. marks each accepted option trade as active from entry through exit;
2. suppresses ETF returns for every session while that option trade is open;
3. records the option P&L on the exit session;
4. resumes ETF exposure on the following session.

This keeps the switcher semantics mutually exclusive.

## Validation

tests/test_etf_exit_switcher.py now covers:

- suppression of ETF returns throughout an open option lifecycle; and
- prevention of double-counting ETF return on an option exit session.

Because this changes the economic path of the switcher, prior ETF-exit
switcher results should be treated as superseded. The historical research
workflow is configured to run on pushes affecting research/, so the corrected
evaluator is intended to regenerate the switcher artifacts before any further
interpretation.
