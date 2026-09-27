# VIX and Buying-Power Allocation Research

**Status:** Documented historical tastytrade/tastylive framework; current production status still requires validation  
**Last reviewed:** 2026-09-27

## Important correction

The project now has direct screenshot evidence from the **Trade Talk by tastytrade** presentation *How to Build a Portfolio Using Complex Options Strategies* showing the following VIX/account-allocation table:

| VIX | Maximum account allocation |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| Greater than 40 | 50% |

The screenshot is preserved in the user's Library as **Screenshot_20210413-175727.png**. fileciteturn2file0

This supersedes our previous conclusion that there was no evidence for a numerical schedule.

tastylive identifies *How to Build a Portfolio Using Complex Options Strategies* as a Trade Talk presentation by Tom Sosnoff and describes it as a detailed portfolio-building presentation. citeturn3search0 A contemporaneous community discussion independently identifies the same video and reports the same 25/30/35/40/50 progression, although it reports the highest band as VIX >50 rather than the >40 shown in the screenshot. citeturn3reddit16

For this project, the **screenshot controls the exact table we record**, so the research specification uses **VIX >40 → 50%**.

## What this evidence means

The table is now classified as:

**Documented historical tastytrade/tastylive portfolio-allocation guidance.**

It should **not yet** be classified as a universally current 2026 tastytrade rule.

That distinction matters because the presentation is from 2020, while newer tastylive material uses different framing. A 2024 tastylive portfolio-risk article describes prudent capital allocation as a **25%–50% range with a 75% maximum cap**, rather than reproducing this exact VIX table. citeturn0search1

Therefore we preserve the historical table rather than silently treating it as today's universal requirement.

## Working project baseline

The exact historical table is now a first-class research candidate:

- VIX 10–15 → maximum 25% account allocation
- VIX 15–20 → maximum 30%
- VIX 20–30 → maximum 35%
- VIX 30–40 → maximum 40%
- VIX >40 → maximum 50%

The table controls the **maximum aggregate account allocation to the options portfolio**, not the size of an individual position.

It does not mean the bot must automatically deploy the maximum.

## Interaction with position sizing

At our $2,000 test account, the allocation ceiling and individual position sizing are separate constraints.

The bot must enforce:

1. VIX-derived aggregate allocation ceiling.
2. Per-position sizing ceiling.
3. Portfolio beta-weighted Delta constraint.
4. Concentration/correlation constraints.
5. Remaining liquidity buffer.
6. Assignment/expiration safeguards.
7. Account-level loss controls.

The most restrictive applicable rule wins.

## Small-account implications

At $2,000:

- 25% = $500
- 30% = $600
- 35% = $700
- 40% = $800
- 50% = $1,000

These are portfolio-level maximums, not required deployment.

Whole-contract option sizing can make the 1–3% preferred per-position target impossible to satisfy precisely. The system must calculate actual contract-level BPR and reject trades that violate hard constraints rather than forcing percentage compliance.

Current tastylive small-account research specifically warns that naked-option BPR can expand substantially after adverse price moves and IV increases. citeturn0search2

## What remains unresolved

1. Whether this historical table should be used unchanged for the project's $2,000 account.
2. Whether "account allocation" maps directly to the BPR definition supplied by our execution broker.
3. Whether the table applies specifically to undefined-risk strategies, all options strategies, or a broader portfolio framework.
4. Whether current tastylive guidance has replaced or refined the historical table.
5. How the ceiling interacts with defined-risk spreads whose BPR behaves differently.
6. Whether the regime-switching layer should use the VIX ceiling directly or as one input among several.
7. Whether a 50% maximum is appropriate after realistic BPR-expansion and stress testing.

## Additional primary-source context

An earlier tastylive piece on reserve capital states that its primary portfolio-allocation rule was to allocate more buying power when VIX is higher. It also distinguishes undefined-risk and defined-risk allocation, discussing 75% of buying power for undefined-risk strategies and 25% for defined-risk strategies, alongside separate per-trade limits. citeturn0search0

This suggests the VIX table may be part of a broader capital-allocation framework rather than a standalone rule.

We therefore need to reconcile:

- VIX allocation,
- undefined vs. defined risk,
- per-trade BPR,
- portfolio Delta,
- diversification/correlation,
- and reserve capital

before freezing the options strategy.

## Research matrix

Compare:

### Historical VIX schedule

10–15: 25%  
15–20: 30%  
20–30: 35%  
30–40: 40%  
>40: 50%

### Fixed controls

- 25% fixed maximum
- 35% fixed maximum
- 50% fixed maximum

### Stress-aware alternatives

VIX schedule plus:

- portfolio drawdown
- realized volatility
- beta-weighted Delta
- current BPR utilization
- correlation concentration
- BPR expansion stress

Required outputs:

- annualized return
- maximum drawdown
- volatility
- Sharpe / Sortino
- worst daily loss
- worst trade
- BPR utilization
- BPR expansion frequency
- rejected-entry frequency
- time without eligible trades
- turnover
- exposure by VIX regime
- tail-loss behavior

## Current decision

The historical 25/30/35/40/50 VIX allocation schedule is now **documented evidence and a first-class research candidate**.

It is no longer correct to describe the schedule as unsupported.

It is also premature to describe it as a universally current 2026 tastytrade requirement.

### Next research task

Reconstruct the **full portfolio methodology surrounding this table**, especially:

- undefined-risk vs. defined-risk allocation,
- per-trade BPR,
- aggregate BPR,
- reserve capital,
- beta-weighted Delta,
- diversification/correlation,
- and how these constraints interact.

Only after that reconciliation should we freeze the options strategy specification.

## References

- tastylive — *Watch These Top 10 YouTube Videos to Master Options Trading*: https://www.tastylive.com/news-insights/watch-these-top-10-youtube-videos-to-master-options-trading
- tastylive — *Reserve Capital*: https://www.tastylive.com/shows/best-practices/episodes/reserve-capital-06-03-2019
- tastylive — *How to Manage the 5 Biggest Risks to Your Portfolio*: https://www.tastylive.com/news-insights/most-important-risks-portfolio-management
- tastylive — *How to Manage Buying Power Risk in Small Option Accounts*: https://www.tastylive.com/news-insights/how-manage-buying-power-risk-small-option-accounts
- User Library evidence: **Screenshot_20210413-175727.png**. fileciteturn2file0
