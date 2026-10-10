# Active-Tightening Overlay: Leave-One-Episode-Out Attribution — 2026-10-10

**Status:** Diagnostic-only; no rule selected or changed  
**Branch:** `research/qqq-slow-bear-audit`  
**Source run:** [Active-tightening overlay run 37885966946](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946)  
**Source artifact:** [artifact 11595834480](https://github.com/eklu654/Trading-Bot/actions/runs/37885966946/artifacts/11595834480)  
**Frozen market window:** 2010-02-11–2026-10-07; 4,189 common QQQ/TQQQ sessions; $5,000 initial balance.

## Question

Is the active-Fed × below-200-DMA overlay's 2018–2019 opportunity cost concentrated in particular defense intervals, especially intervals that overlap the baseline's own shock/recovery defense?

## Reproduction and validation

The source artifact includes frozen QQQ/TQQQ inputs and the daily signal/equity ledger, but did **not** include the episode-contribution CSV. The source run was on main commit `e633377371fafe08af6510044bbefd8f9fba04ba`, whose script predates the leave-one-episode-out output now present on the research branch. I reconstructed the table from those frozen inputs and the checked-in `research/causal_execution.py` next-open execution convention.

Before interpreting counterfactuals, the reconstruction reproduced the source run's terminal balances:
- B0 baseline: $4,040,313.15 reconstructed versus $4,040,313.15 reported.
- Active-tightening overlay candidate: $3,674,919.00 reconstructed versus $3,674,919.00 reported.

Execution convention retained: close[t] signal becomes executable at the next open; the previously executed position earns the overnight leg, and the position executed at the open earns the intraday leg. The leave-one-out operation changes one contiguous overlay-signal episode back to fully exposed, then reruns the whole equity path from the same $5,000 starting balance.

## Main finding

The overlay's 2018–2019 defense transitions were choppy:

| Overlay interval | Signal sessions | Incremental defense sessions* | Baseline-defense overlap |
|---|---:|---:|---:|
| 2018-10-11 | 1 | 1 | 0 |
| 2018-10-24–2018-10-31 | 6 | 0 | 6 |
| 2018-11-02–2018-11-06 | 3 | 0 | 3 |
| 2018-11-09–2018-11-30 | 15 | 0 | 15 |
| 2018-12-04–2019-02-04 | 41 | 20 | 21 |
| 2019-02-06–2019-02-13 | 6 | 6 | 0 |
| 2019-03-07–2019-03-08 | 2 | 2 | 0 |

*Incremental defense means the overlay is defensive while B0 itself is not. During overlap sessions, the additional overlay has no effect on the combined candidate's exposure.

The three October/November 2018 intervals were entirely overlapped by B0's own defense, so removing any one of those intervals did not change the portfolio terminal balance. The large interval from December 2018 into February 2019 included both overlap and 20 incremental-defense sessions. Later February and March 2019 episodes also imposed incremental defense during the recovery/chop period.

## Leave-one-overlay-episode-out results

Each row removes only the named overlay episode, leaves every other episode unchanged, and recomputes the complete portfolio. Conditional effects are **not additive** because returns compound and episodes interact through the changing account balance.

| # | Overlay interval | Sessions | Incremental / overlap sessions | Final balance without this episode | Full candidate minus counterfactual |
|---:|---|---:|---:|---:|---:|
| 1 | 2016-01-06–2016-03-15 | 48 | 48 / 0 | $3,668,838 | +$6,081 |
| 2 | 2018-10-11 | 1 | 1 / 0 | $3,654,567 | +$20,352 |
| 3 | 2018-10-24–2018-10-31 | 6 | 0 / 6 | $3,674,919 | $0 |
| 4 | 2018-11-02–2018-11-06 | 3 | 0 / 3 | $3,674,919 | $0 |
| 5 | 2018-11-09–2018-11-30 | 15 | 0 / 15 | $3,674,919 | $0 |
| 6 | 2018-12-04–2019-02-04 | 41 | 20 / 21 | $4,468,788 | −$793,869 |
| 7 | 2019-02-06–2019-02-13 | 6 | 6 / 0 | $3,893,856 | −$218,937 |
| 8 | 2019-03-07–2019-03-08 | 2 | 2 / 0 | $4,051,341 | −$376,422 |
| 9 | 2022-03-18–2022-03-28 | 7 | 7 / 0 | $4,288,101 | −$613,182 |
| 10 | 2022-03-30–2022-04-01 | 3 | 3 / 0 | $3,685,827 | −$10,908 |
| 11 | 2022-04-05–2023-01-25 | 203 | 110 / 93 | $2,174,251 | +$1,500,668 |
| 12 | 2023-01-30 | 1 | 1 / 0 | $3,829,017 | −$154,098 |
| 13 | 2023-03-10 | 1 | 1 / 0 | $3,971,139 | −$296,220 |

A positive value in the last column means the full candidate finished higher than the version without that episode; a negative value means removing that episode improved final wealth.

## Period-level context

| Window | B0 return | Candidate return | B0 defensive sessions | Candidate defensive sessions |
|---|---:|---:|---:|---:|
| 2018–2019 | +135.18% | +66.49% | 49 | 78 |
| 2018-10-01–2019-03-31 | +0.04% | −29.18% | 49 | 78 |
| 2022–2023-03-31 | −50.42% | −36.41% | 93 | 215 |

This agrees with the existing stress-window report: the overlay helps substantially during the 2022 tightening bear, but its sticky 200-DMA defense can remain engaged during rebounds and repeated trend crossings. In the 2018 Q4 through March 2019 window, the candidate's inherited-account return was −29.18% versus approximately flat for B0.

## Decision

1. **Do not promote or retune the overlay from this attribution.** The same 2018–2019 dates have now been examined repeatedly and are development data.
2. The clearest cost concentration is the 2018-12-04–2019-02-04 interval, with additional conditional costs in the February and March 2019 episodes. This is evidence about *where* the opportunity cost arose, not proof that a revised exit rule can preserve 2022 protection.
3. The 2022-04-05–2023-01-25 episode is the largest positive conditional contribution in this leave-one-out analysis, showing the trade-off is real: removing that long defense would have reduced final wealth by about $1.501M, all else unchanged.
4. Do not add a new threshold or tune the 200-DMA based on these same intervals. Any new rule needs a newly frozen prospective/chronological validation and the existing synthetic-tail gates; no paper/live trading authorization follows.
5. Provenance note: the historical source artifact predates the leave-one-episode-out output added to the research-branch script. The current workflow already lists `canonical_active_tightening_overlay_episode_contributions.csv` among its artifact paths; no workflow packaging change was needed for this finding.
