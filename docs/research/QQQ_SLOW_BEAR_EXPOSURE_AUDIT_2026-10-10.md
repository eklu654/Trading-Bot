# QQQ Slow-Bear Exposure Audit — 2026-10-10

## Status

**Diagnostic only; no rule promoted.** Corrected GitHub Actions run: https://github.com/eklu654/Trading-Bot/actions/runs/38040543637  
Branch: `research/qqq-slow-bear-audit`  
Code commit tested: `2d4413155bf442a91327f9b4ef64677ee2236b47`

## Question

Does the canonical B0 rule (QQQ adjusted-close daily return <= -4.5%, exit TQQQ at the next open) sometimes allow a substantial gradual decline before its shock trigger fires?

## Method

- Data window returned by yfinance: 2010-01-04 through 2026-10-07.
- Signal series: QQQ adjusted close and daily adjusted return.
- Drawdown: QQQ adjusted close versus its rolling 252-session adjusted-close high.
- Trigger thresholds: first crossing below -10%, -15%, and -20%; re-arm only after the drawdown recovers above the given threshold.
- Endpoint: first *later* QQQ daily return <= -4.5%, with TQQQ exit measured at that session's adjusted open; if the threshold and shock occur on the same day, classify it separately rather than treating it as a warning period.
- TQQQ return from trigger close to exit open is calculated as adjusted TQQQ open / trigger adjusted close - 1, capturing all intervening daily moves and the final overnight gap.

The first run had a return-measurement defect (overnight segments only) and is superseded. The corrected run is the source for the numbers below.

## Results

| QQQ drawdown threshold | Episodes | Same-day shock (not a warning) | Later shock exit | Median sessions to later shock | Median TQQQ return from threshold close to exit open | Worst such return |
|---|---:|---:|---:|---:|---:|---:|
| -10% | 8 | 4 | 4 | 4 | -20.70% | -29.54% |
| -15% | 5 | 3 | 2 | 6 | -17.58% | -19.72% |
| -20% | 5 | 4 | 1 | 15 | -13.29% | -13.29% |

All episodes in this sample ultimately had a shock exit; none remained untriggered through the data end.

### The four gradual -10% threshold episodes

| Threshold date | First later shock / exit date | Sessions elapsed | QQQ return through shock close | TQQQ return through next-open exit |
|---|---|---:|---:|---:|
| 2011-08-17 | 2011-08-18 | 1 | -4.91% | -8.15% |
| 2020-03-05 | 2020-03-09 | 2 | -8.52% | -24.12% |
| 2022-04-05 | 2022-05-05 | 21 | -13.32% | -29.54% |
| 2025-03-26 | 2025-04-03 | 6 | -6.96% | -17.28% |

At the -10% threshold, the clearest slow-bear example is 2022: the drawdown threshold was crossed on April 5, but the daily shock exit did not occur until May 5. TQQQ lost about 29.5% from the threshold close through the next-open exit. This is an asset-return interval, not a claim that a strategy-level exit at April 5 would have improved final wealth.

The -15% later-shock cases were 2020-03-11 to 2020-03-12 (-19.72% TQQQ) and 2022-04-20 to 2022-05-05 (-15.45%). The one -20% later-shock case was 2022-08-22 to 2022-09-13 (-13.29%).

## Interpretation / next test

1. **Evidence of a real failure mode:** the daily -4.5% shock rule is reactive, not a gradual-bear exit. In the 2022 episode it allowed another 21 sessions and a severe TQQQ loss after QQQ was already 10% below its trailing high.
2. **Not yet evidence that a threshold exit improves the strategy.** The audit does not calculate what happens after an earlier exit, including missed rebounds, re-entry timing, turnover/costs, or final compounded wealth.
3. Counts across thresholds overlap and are not independent episodes; the sample is small and concentrated in a few bear markets.
4. Next experiment should be a full B0 portfolio counterfactual using the same frozen inputs and next-open execution: add a QQQ trailing-252 drawdown warning at -10% (then test -15% only as a separate candidate), define explicit re-entry behavior, and report terminal balance, max drawdown, event-level missed rebound costs, and costs against the unchanged B0 control. Do not promote a threshold from this event audit alone.

## Provenance

Corrected run log reports the manifest and episode ledger. Machine-readable artifact is attached to the Actions run above. The audit remains on the isolated research branch; nothing was merged into `main`.
