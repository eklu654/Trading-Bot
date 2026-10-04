# Return-First Strategy Re-Audit — 2026-10-04

## Purpose

This document corrects a recurring interpretation error in the ETF research: large historical drawdown was sometimes treated as an implicit rejection criterion even when no explicit drawdown constraint had been established.

The research objective is primarily substantial absolute wealth creation from the available capital. Drawdown remains an important descriptive and operational metric, but it is not an automatic veto.

## Corrected decision framework

For every serious candidate, report and preserve:

1. Starting capital.
2. Ending capital.
3. Total return and CAGR.
4. Maximum percentage drawdown.
5. Maximum dollar drawdown.
6. Lowest account equity.
7. Recovery time and time under water.
8. Frequency of 25%, 50%, 60%, and 70%+ drawdowns.
9. Calendar-year and major-regime returns.
10. Train / validation / untouched holdout performance.
11. Execution-delay and transaction-cost sensitivity.
12. Account-level whole-share feasibility.
13. Parameter-neighborhood robustness.

A strategy is **not rejected solely because its maximum drawdown is large**.

A drawdown-based rejection requires an explicit reason, such as:
- a hard account-survival constraint;
- a broker/margin constraint;
- a predefined maximum-loss constraint;
- an operational requirement;
- or a demonstrated risk-adjusted objective that was explicitly selected before evaluating the result.

## Offense-as-defense hypothesis

The project should explicitly test the hypothesis that, for a highly leveraged portfolio, retaining more upside and recovering faster through strong offensive exposure can produce better long-run capital growth than aggressively de-risking.

This is a hypothesis to test, not an assumption that high drawdown is harmless.

The comparison should therefore measure the wealth sacrificed by each defensive mechanism rather than assuming the defensive mechanism is beneficial.

## Candidates requiring re-audit

### Tier A — direct return controls

- TQQQ buy-and-hold.
- SOXL buy-and-hold.
- SPXL buy-and-hold.
- Equal-weight leveraged-family always-bull control.
- Original ETF-001 25%-cash 200-DMA strategy.
- ETF-001 cash-allocation variants: 0%, 10%, 25%, 50%.
- Fixed 200-DMA fallback controls.

### Tier B — dynamic offensive strategies

- ETF-015 bull-family rotation.
- ETF-016 consistency-gated bull selection.
- DMA250/top-2/5-session family rotation.
- DMA200/top-2/5-session family rotation.
- Other family-rotation candidates that were deprioritized primarily because of drawdown.

### Tier C — defensive challengers

- Bull/cash/bear switching.
- Multi-signal inverse transitions.
- Volatility/drawdown risk overlays.
- Options defensive sleeves.

These remain valid research branches, but their purpose is now explicit: determine whether the capital sacrificed by defense buys enough improvement in survivability or operational reliability to justify itself.

## Known evidence already recovered

The 2018–2025 controls show:

- TQQQ buy-and-hold: 32.62% CAGR, -81.66% max drawdown.
- TQQQ 200-DMA + cash: 34.42% CAGR, -50.01% max drawdown.
- SOXL buy-and-hold: 21.65% CAGR, -90.46% max drawdown.
- SOXL 200-DMA + cash: 8.44% CAGR, -69.63% max drawdown.

These results demonstrate why return and drawdown must be evaluated together rather than allowing either metric to dominate automatically.

The five-family always-bull benchmark also produced substantially higher historical terminal wealth than the later risk-overlay candidates, while experiencing a much larger drawdown. That tradeoff is a research result, not an automatic rejection.

The current $5,000 DMA250/top-2/5-session family rotation account replay is especially important:

- 25 bps, prior-close execution: approximately $228,285 ending equity from $5,000, 25.96% CAGR, -68.62% max drawdown.
- 25 bps, next-open execution: approximately $176,531 ending equity, 24.02% CAGR, -69.91% max drawdown.
- V30/L20/DD20 overlay, 25 bps: approximately $23,294 prior-close and $24,622 next-open.
- V30/L20/DD25 overlay, 25 bps: approximately $29,187 prior-close and $33,039 next-open.
- V30/L20/DD30 overlay, 25 bps: approximately $33,781 prior-close and $29,642 next-open.

The overlays therefore demonstrate a large historical reduction in drawdown, but also a very large reduction in terminal wealth. Neither outcome should be dismissed.
## Current validated common-period evidence

ETF-031 now provides the authoritative direct-control endpoint of **2010-03-11 through 2026-10-02**, with a $5,000 starting balance:

| Strategy | Ending balance | CAGR | Max DD |
|---|---:|---:|---:|
| TQQQ buy-and-hold | $1,558,429 | 41.44% | -81.66% |
| SOXL buy-and-hold | $1,363,181 | 40.30% | -90.46% |
| Frozen family rotation | $378,052 | 29.85% | -67.40% |
| SPXL buy-and-hold | $339,693 | 29.01% | -76.86% |
| TQQQ 200-DMA/cash | $329,962 | 28.78% | -50.01% |
| TQQQ 200-DMA/next-open | $504,211 | 32.12% | -48.14% |
| QQQ buy-and-hold | $91,390 | 19.18% | -35.12% |

These are the current common-period benchmark figures. The earlier 2018–2025 figures remain useful as historical research context, but they must not be mixed with the 2010–2026 headline comparison.

The evidence materially reinforces the return-first correction: the highest historical terminal-wealth controls also carry very large drawdowns, while the next-open TQQQ 200-DMA control demonstrates that a materially lower drawdown can coexist with substantially lower terminal wealth. Neither dimension is sufficient by itself.

The **$5,000 whole-share family-rotation account replay** has now been corrected in the repository to use the updated **2010-03-12 → 2026-10-02** endpoint and to report dollar drawdown, minimum equity, recovery duration, current underwater duration, execution sensitivity, and cost stress. The regenerated CI artifact is now authoritative. At 25 bps over the 2010-03-12 → 2026-10-02 account-replay period, the raw family rotation ends at $228,285 under prior-close execution and $176,531 under next-open execution. Its maximum drawdown is -68.62% / -69.91%, maximum dollar drawdown is approximately -$143,072 / -$101,452, and minimum equity is approximately $2,032 / $2,374. The DD20/DD25/DD30 overlays finish at approximately $23.3k/$29.2k/$33.8k prior-close and $24.6k/$33.0k/$29.6k next-open. These are now the current account-replay headline figures.

The overlays therefore remain a separate explicit tradeoff study: they may materially reduce drawdown, but any wealth sacrificed must be measured against a concrete survival or operational benefit rather than assumed to be beneficial.


## What the re-audit must answer

For every candidate that was previously deprioritized:

1. Did it actually produce more terminal wealth?
2. Did it survive all chronological splits?
3. Was the high return dependent on one historical era?
4. Did it approach account ruin or merely experience a large temporary drawdown?
5. How long did recovery take?
6. What was the maximum dollar loss at a $5,000 starting balance?
7. Does next-open execution materially change the result?
8. Does 10/25/50 bps cost stress materially change the result?
9. Does modest parameter perturbation preserve the behavior?
10. What is the exact wealth cost of each defensive overlay?

## Important distinction

Historical survival through a large drawdown is evidence that the strategy path was survivable in the historical sample. It does not guarantee future survival.

Conversely, a strategy ending with substantially more capital is evidence that its offensive exposure produced substantially more historical wealth. It should not be dismissed merely because its path was uncomfortable.

The research must preserve both facts.

## Revised promotion philosophy

The project should not optimize for minimum drawdown.

It should first identify strategies capable of producing substantial, robust absolute returns. Risk controls should then be tested as explicit tradeoffs:

> How much historical wealth does this control save, and what risk does it remove?

A control that cuts terminal wealth by 80–90% should require correspondingly strong evidence that the removed tail risk creates a meaningful benefit for the actual account and deployment objective.

## Next research stage

The next research pass should build a return-first re-audit table across the historical strategy branches, using common:

- starting balance;
- dates;
- adjusted-return conventions;
- transaction costs;
- execution assumptions;
- train/validation/holdout splits;
- and account-level replay where feasible.

The raw high-return candidates should be preserved as first-class controls rather than replaced by risk overlays before this comparison is complete.

This document does not select a production strategy. It corrects the interpretation framework so that future research does not repeat the same mistake.## 2026-10-04 TQQQ DMA-grid update

The corrected TQQQ DMA × re-entry experiment tested 56 combinations rather than assuming the earlier 5-session rule. The current authoritative grid uses the common TQQQ period **2010-03-11 → 2026-10-02**.

| Strategy | Ending $5k | CAGR | Max DD |
|---|---:|---:|---:|
| TQQQ buy-and-hold | **$1,558,429** | **41.44%** | -81.66% |
| TQQQ 250-DMA + 10-session | **$400,921** | **30.31%** | -48.70% |
| TQQQ 250-DMA + 5-session | **$368,356** | **29.64%** | -49.73% |
| TQQQ 225-DMA + immediate | **$357,051** | **29.40%** | -49.96% |
| TQQQ 200-DMA + 3-session | **$329,908** | **28.78%** | -48.14% |
| TQQQ 200-DMA + immediate | **$329,963** | **28.78%** | -50.01% |
| TQQQ 200-DMA + 5-session | **$278,890** | **27.48%** | -48.14% |

This is the authoritative return-first comparison for the grid. The earlier 5-session rule is not a universal optimum: within the 200-DMA family, 3-session confirmation produces materially more terminal wealth than 5-session confirmation at the same measured maximum drawdown. The grid leader is 250-DMA + 10-session under the prior-close research convention, but that result now requires causal next-open validation.


