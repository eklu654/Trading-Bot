# Canonical QQQ Shock/Recovery Baseline — First Stress Scorecard

**Date:** 2026-10-09 UTC  
**Status:** WORKING BASELINE; historical performance is not a guarantee  
**Capital:** $5,000  
**Instrument traded:** actual TQQQ over the available aligned QQQ/TQQQ history  
**Rule:** QQQ adjusted-close daily return <= -4.5% activates defense; exposure is zero beginning at the next open. Remain defensive until QQQ adjusted close is at least 10% above the post-shock running low; re-enter at the next open. Otherwise hold 100% TQQQ. No DMA, Fed, MACD, golden-cross, macro, inverse-ETF, or AI filter is part of this baseline.

## Why this is the baseline

The user has directed research to start from the reproducible ~$4.04M shock/recovery candidate and organically discover whether it can weather acute crashes and prolonged bears. Do not block progress trying to reconstruct a different historical ~$3.3M variant. Keep historical work as context only; do not silently substitute its rules.

## Whole-period result (latest robustness artifact)

Source workflow: [TQQQ failed-bounce robustness](https://github.com/eklu654/Trading-Bot/actions/runs/37884245678), artifact ID 11596300026, commit `207213dea6e4dde44a89f68daa044e7f213fe202`.

| Metric | Shock/recovery | TQQQ buy-and-hold |
|---|---:|---:|
| Ending balance | $4,040,311.91 | $2,094,668.80 |
| CAGR reported by this run | 49.49% | 43.70% |
| Maximum drawdown | -73.53% | -81.66% |

The earlier same-input reconciliation workflow passed with identical daily equity curves and a ~$4.04M ending value. This robustness run downloads its own current market data, so use the separate same-input workflow for the strict exact-reconciliation claim; do not treat distinct downloads as byte-identical inputs.

## Period scorecard

The period return below is calculated independently within each named date window (equity resets to 1 at that window's start). Max drawdown is likewise measured within that period, not inherited from prior years. This is a regime diagnostic, not a continuous account ledger.

| Window | Shock/recovery return | Buy-and-hold return | Strategy max DD | Buy-and-hold max DD |
|---|---:|---:|---:|---:|
| 2010–2014 | +895.0% | +865.3% | -43.1% | -43.9% |
| 2015–2019 | +569.6% | +434.0% | -44.5% | -58.1% |
| 2020–2021 (includes COVID crash/rebound) | +325.6% | +284.4% | -47.0% | -69.9% |
| 2022–2024 (includes tightening-driven bear) | +42.3% | -1.4% | -72.6% | -81.0% |
| 2025–2026-10-07 | +100.2% | +114.4% | -56.1% | -56.8% |

Interpretation: the baseline beat buy-and-hold in the first four windows, including the COVID and 2022–24 windows, but it still experienced a roughly 73.5% whole-period maximum drawdown. It lagged buy-and-hold in 2025–current. That is promising enough to investigate, not proof of robustness across all future or historical regimes.

## Event-level contribution audit

The artifact's leave-one-defense-event-out counterfactual shows that the rule's nine exits are not uniformly helpful:

| Shock date | Recovery decision close | Defensive sessions | Estimated terminal contribution of defense |
|---|---|---:|---:|
| 2011-08-04 | 2011-08-31 | 19 | +$120,614 |
| 2018-10-24 | 2019-01-07 | 49 | +$818,108 |
| 2020-02-27 | 2020-03-26 | 20 | +$1,345,392 |
| 2020-06-11 | 2020-07-06 | 16 | -$1,018,658 |
| 2020-09-03 | 2020-10-12 | 26 | -$328,495 |
| 2022-05-05 | 2022-07-19 | 50 | +$740,359 |
| 2022-09-13 | 2022-11-11 | 43 | +$612,309 |
| 2025-04-03 | 2025-04-09 | 4 | -$236,322 |
| 2026-06-05 | 2026-08-13 | 47 | -$46,711 |

These are terminal counterfactual differences under the script's one-event-at-a-time removal procedure, not independent additive contributions. Interactions between events mean they must not be summed as though each event were isolated.

## Transaction-cost sensitivity

The robustness script charges a cost per exposure change. Under that model:

| Cost assumption | Ending balance |
|---|---:|
| 0 bp | $4,040,312 |
| 5 bp | $4,001,812 |
| 10 bp | $3,963,659 |
| 25 bp | $3,851,257 |
| 50 bp | $3,670,604 |

This simple sensitivity remains favorable versus the run's buy-and-hold ending balance, but it is not a complete live execution model. It does not establish real spreads, slippage, taxes, funding, market impact, or broker-specific fills.

## Conclusions supported so far

1. **Supported as a reproducible historical candidate:** the simple shock/recovery rule ended above TQQQ buy-and-hold in the recorded period.
2. **Not established:** survival through every major drawdown. Its -73.5% maximum drawdown is severe, and it can remain fully exposed during a slow bear until a single-day QQQ loss crosses -4.5%.
3. **Not established:** that any additional filter improves long-run wealth. The event audit shows both large benefits and large opportunity costs.
4. **Not approved for live trading:** further stress testing, execution-cost realism, and causal/out-of-sample validation remain necessary.

## Next work, in order

1. Keep the baseline unchanged and produce a continuous equity/drawdown and exposure timeline around COVID (2020-02 to 2020-07), the 2022 tightening bear, 2018 Q4, and false-positive exits in 2020 June/September and 2025 April. Include actual starting/ending equity, peak-to-trough drawdown, time defensive, exit/re-entry timing, and rebound missed.
2. Mechanically identify slow-bear periods where QQQ suffers a sustained peak-to-trough decline without a timely -4.5% daily shock. Measure the baseline's exposure and losses before its first trigger. Do not use the future event label to decide whether a signal trades.
3. Only after those diagnostics, test one frozen structural overlay at a time (existing 200-DMA/Fed state, then the existing macro state) against the unchanged baseline. No broad indicator fishing, no new DMA-length sweep, and no AI layer yet.
4. Evaluate on identical dates, price fields, execution convention, costs, and $5,000 capital. Freeze candidate definitions before chronological holdout; any rule changed after seeing holdout becomes a development candidate.
5. For pre-2010 episodes such as 1970s, 1987, and 2000–2002, report signal-only index diagnostics or explicitly labeled synthetic daily-reset leveraged proxies—not actual TQQQ returns.

## Reproducibility pointers

- Robustness run: https://github.com/eklu654/Trading-Bot/actions/runs/37884245678
- Same-input reconciliation: https://github.com/eklu654/Trading-Bot/actions/runs/37884245700
- Structural diagnostics: https://github.com/eklu654/Trading-Bot/actions/runs/37884245716
- Long-history signal-only audit: https://github.com/eklu654/Trading-Bot/actions/runs/37884245625
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
