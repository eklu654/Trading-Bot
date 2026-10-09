# Historical Real-Index Test Plan for the Active-Fed × 200-DMA Defensive Mechanic

**Created:** 2026-10-09 UTC  
**Status:** APPROVED NEXT EXPERIMENT DESIGN; not yet run  
**Parent question:** Does the defensive mechanic generalize beyond the 2022 episode without inventing pre-inception TQQQ returns?

## Decision

Yes. Test the *signal mechanic* on actual historical index observations and actual historical Fed-rate observations. Do not synthesize a leveraged ETF, do not report a pre-2010 TQQQ portfolio balance, and do not call index performance a TQQQ backtest.

## Frozen mechanic under test

Current modern candidate definition from `CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md`:

1. Calculate a 200-session simple moving average from the actual index close.
2. Define the Fed lifecycle state using only policy-rate observations available at the time. For the first test, preserve the repository's current `TIGHTENING_ACTIVE` state definition if its exact implementation can be reused without future information. Otherwise stop and document the missing state-builder rather than silently inventing a new equivalent.
3. Apply a one-session lag to the Fed state, matching the modern candidate.
4. Arm defense when the index closes below its 200-session SMA while the lagged Fed state is `TIGHTENING_ACTIVE`.
5. Keep the defense armed until the index closes at or above its 200-session SMA. This is a sticky state, not a fresh daily independent signal.
6. The existing shock/recovery mechanic is not required to assess the defensive overlay itself. First measure the overlay's signal timing and the index outcomes. A separate modern-only replication can test interaction with the baseline.

## Real historical datasets

### Primary long-history proxy: Nasdaq Composite

Use the actual daily Nasdaq Composite index (commonly distributed as `^IXIC`) from its available history beginning in 1971. This is a real index, not synthetic TQQQ. It is a more relevant growth/technology proxy than the S&P 500 for the QQQ/TQQQ research question, but it is not QQQ and has different composition, weighting, dividends, and investability. Label every result "Nasdaq Composite signal study", never "QQQ returns" or "TQQQ returns".

### Independent broad-market cross-check: S&P 500

Use actual daily S&P 500 index levels for periods where a trustworthy daily source is available. This checks whether the mechanic is a broad-market effect or mainly a Nasdaq/growth-index effect. The S&P 500 is not interchangeable with Nasdaq Composite or QQQ. Confirm the data vendor, adjusted/price-index nature, coverage, and licensing before running.

### Policy data: historical effective federal funds rate

Use the official FRED/Board of Governors daily DFF series from July 1954 onward. For pre-July-1954 context, the Federal Reserve/FRED historical daily federal-funds quotes begin in 1928, but these must be joined only if the source data and its exact rate construction are verified. The initial primary test can begin in 1971, so DFF should cover the entire period.

Source references:
- FRED DFF: https://fred.stlouisfed.org/series/DFF
- ALFRED DFF vintages (useful for revision/availability context): https://alfred.stlouisfed.org/series/DFF
- Federal Reserve paper describing daily federal-funds history back to 1928: https://www.federalreserve.gov/econres/feds/new-daily-federal-funds-rate-series-history-of-the-federal-funds-market-1928-1954.htm
- Nasdaq Composite historical data: https://finance.yahoo.com/quote/%5EIXIC/history/

## What to measure (no leverage assumptions)

For each index, report:
- Dates and count of defense entries/exits; duration distribution; percent of sessions defensive.
- For each defense entry, the index drawdown from its trailing 252-session high at entry, and the next 21/63/126/252-session index returns and maximum adverse excursion.
- Within each major historical bear (including 1973–74, 1980–82, 1987, 1990, 2000–02, 2007–09, 2011, 2015–16, 2018, 2020, 2022), whether defense entered before, during, or after the peak-to-trough decline; how long it remained active; whether it rearmed/re-entered repeatedly.
- False-defense costs: forward index returns while defensive and the rebound missed before the index closes back above its 200-DMA.
- Compare to 200-DMA-only and Fed-active-only ablations, plus a no-defense reference. These are signal-timing comparisons on the same real index, not leveraged portfolio results.
- Robustness across Nasdaq Composite and S&P 500; don't tune thresholds on the listed episodes.
- Data hashes, source URLs, download timestamps, missing-session counts, and exact state transition dates.

## Critical guardrails

- No synthetic daily-reset leverage, no reconstructed TQQQ, no assumed 3x returns, and no pre-inception TQQQ dollar balances.
- Do not use future policy rates to label a session's Fed state. Rate data must be lagged conservatively; the one-session lag is the minimum convention unless data timestamps justify a longer one.
- Avoid lookahead in the 200-DMA and sticky state logic. The close can determine the next session's defense state, not that same session's return.
- Do not declare success just because defense activates during known bears. Quantify how often it activates in ordinary corrections and how much index recovery it misses.
- This historical index study evaluates signal validity. It cannot prove that the rule improves TQQQ terminal wealth; actual TQQQ accounting remains limited to its real trading history from 2010 onward.
- First run should use the existing rule as-is, with no threshold optimization. Any new state definition is a separate candidate and must be named separately.

## Acceptance criteria

A useful first result must:
1. Reproduce the modern candidate's active-state dates on overlapping 2010+ observations, or explain every difference.
2. Cover at least the Nasdaq Composite history from 1971 through the latest available observation with verified daily data.
3. Report the named historical episodes, all defense entry/exit events, and forward outcome windows.
4. Include Fed-only, DMA-only, and combined-state ablations.
5. Explicitly separate historical signal evidence from portfolio-performance evidence.
6. Be saved as a machine-readable artifact plus a markdown result report, with code/tests and a SHA-256 manifest.

## Research question

Does active tightening plus below-200-DMA identify dangerous regimes across multiple distinct historical eras, or is its apparent value concentrated in the single 2022 episode? The study should let the data answer that without assuming any pre-TQQQ leveraged return path.


## Additional direct test of the mechanic using real index returns

In addition to event-level signal diagnostics, run a separate **index-only exposure backtest** using actual index returns. This directly tests whether the exposure-reduction mechanic helps on real historical market data without claiming to replicate TQQQ:

- Normal state: 100% invested in the selected real index.
- Defensive state: compare 0%, 25%, 50%, and 75% index exposure; remainder earns a documented cash proxy.
- Cash proxy: use actual 3-month Treasury-bill yield data where verified coverage is available (for example, FRED TB3MS); explicitly convert quoted annualized yield to a daily accrual convention and test a zero-cash-yield sensitivity. Never treat the quoted yield as a daily return.
- Compare combined Fed-active × below-200-DMA with Fed-active-only, below-200-DMA-only, and always-invested controls.
- Use the same position-state timing for all variants: a close-derived state affects the next session, not the same session's return.
- Report ending index-strategy wealth from a normalized 1.0 starting value, CAGR, maximum drawdown, worst rolling 252-session return, time defensive, turnover/state transitions, and results by named historical episode.
- Run price-index results as the primary consistently sourced series, and clearly disclose that Nasdaq Composite price returns exclude dividends. If a verified total-return index is available for the same dates, add it as a separate cross-check rather than mixing series.
- This is a genuine backtest of the defensive mechanic applied to an actual index. It is still **not a TQQQ backtest**: leveraged ETF daily reset, financing, tracking, fees, and path-dependent compounding are deliberately outside scope.

This two-part design answers two different questions without conflating them: (1) did the signal arrive in time across old market regimes? (2) did reducing exposure improve outcomes when applied to the real index itself?
