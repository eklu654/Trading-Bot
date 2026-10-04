# Current Research Gate — 2026-10-03

## Purpose

This document records the current evidence state after the corrected bull/cash/bear DMA switching research completed on 2026-10-03. It is a research-status record, not a trading recommendation.

## Verified pipeline state

The latest corrected Dynamic ETF Research workflow completed successfully as GitHub Actions run **#59**, run ID `37094091267`, on commit `1ce2c7444c2fef7b8fd41e192bfb752a226679a9`.

The latest corrected Historical Research workflow completed successfully as GitHub Actions run **#242**, run ID `37094091225`, on the same commit.

The research-test workflow also passed on the corrected implementation.

## Bull/Cash/Bear switching implementation

The paired ETF experiment now enforces **family-level** exclusivity:

- SPXL and SPXS cannot coexist.
- TQQQ and SQQQ cannot coexist.
- SOXL and SOXS cannot coexist.
- UDOW and SDOW cannot coexist.
- TNA and TZA cannot coexist.
- Opposite directions across different families are explicitly allowed.
- Bear exposure may be partial at 25%, 50%, 75%, or 100%, with the remainder in cash.

The combined experiment uses an equal 20% sleeve weight for each of the five families as a research control. This is not a production allocation.

## Latest combined holdout observations

The combined chronological holdout covers 2023-01-03 through 2026-09-25 (936 observations).

Selected tested configurations produced the following observed results:

| Bull DMA | Bear DMA | Confirmation | Bear weight | Total return | CAGR | Sharpe | Max drawdown |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 200 | 1 | 100% | +74.05% | 16.04% | 0.557 | -54.99% |
| 200 | 100 | 1 | 100% | +15.49% | 3.94% | 0.334 | -55.41% |
| 200 | 75 | 1 | 100% | -8.10% | -2.24% | 0.206 | -58.32% |
| 200 | 50 | 1 | 100% | +27.79% | 6.80% | 0.388 | -50.05% |
| 200 | 50 | 5 | 100% | +56.77% | 12.82% | 0.500 | -43.43% |
| 200 | 75 | 5 | 100% | +4.89% | 1.29% | 0.283 | -56.33% |

These are holdout observations across a research matrix. They are not a production selection, and no configuration is promoted by this document.

The corrected combined reporting also confirms that cross-family opposite exposure actually occurs: the tested configurations include nonzero `mixed_direction_days`. The combined experiment therefore exercises the intended family-level constraint rather than imposing global bull/bear exclusivity.

## Important interpretation

The new experiment does not establish a universal replacement for cash during every DMA-triggered drawdown.

The results vary materially with:

- bull-side DMA;
- bear-side DMA;
- confirmation length;
- bear allocation;
- benchmark family;
- and the interaction of independent family states.

Individual-family holdout results also show large dispersion. For example, the tested semiconductor family can experience extremely large drawdowns even when its inverse-state logic is enabled. Therefore the research must continue to evaluate portfolio-level risk rather than assuming that inverse ETFs are automatically safer than cash.

## Stress-period observations

The dynamic research artifact includes fixed stress windows.

Examples from the current run:

- **February 2018 volatility shock:** SPXL 3x returned -15.01%, while the tested dynamic family-leverage configuration returned -1.26%.
- **October–December 2018:** SPXL 3x returned -39.03%; the tested volatility-sized dynamic configuration returned -13.52%.
- **COVID crash:** SPXL 3x returned -52.14%; the tested volatility-sized dynamic configuration returned -14.81%.
- **2022 rate-hike bear:** SPXL 3x returned -56.55%; the tested volatility-sized dynamic configuration returned -12.47%.

These are historical stress-window observations, not forecasts or guarantees. They also do not establish that the dynamic configuration is production-ready.

## Options status

The existing $5,000 account-feasibility research remains controlling for small-account options decisions. The current evidence does not establish that the options sleeve improves the ETF portfolio at the $5,000 account size.

0DTE remains research-only and is not being treated as a production component.

## Paper-trading gate

Paper trading is an explicit required stage **after a strategy contract has been frozen and before any live autonomous deployment**.

The intended progression is:

1. Complete historical research and chronological holdout validation.
2. Freeze the exact strategy rules and portfolio constraints.
3. Implement the exact production decision/risk/execution logic.
4. Run automated unit, integration, and fault-injection tests.
5. Start an unattended **paper soak test** using the same decision engine intended for live trading.
6. Monitor paper results and operational behavior for a meaningful live period.
7. Reconcile paper decisions against expected signals and simulated execution.
8. Only after the paper/operational gates are satisfied should live deployment be considered.

The paper system must record at minimum:

- every strategy decision and its reason;
- market-data timestamps and freshness;
- desired portfolio state;
- risk approvals/rejections;
- submitted/canceled/rejected orders;
- simulated fills and partial fills;
- broker/account state where available;
- reconciliation results;
- restarts and reconnects;
- stale-data incidents;
- state divergences;
- realized/unrealized P&L;
- drawdown and exposure;
- emergency-stop events;
- and an auditable event timeline.

Paper trading is an **operational validation stage**, not proof that future live returns will match historical backtests.

## Live-deployment gate

No live autonomous trading is authorized by this document.

Before live deployment, the project must satisfy both economic and operational gates, including:

- positive net expectancy after realistic execution assumptions;
- adequate chronological holdout evidence;
- account-level feasibility at the intended NLV;
- robustness to reasonable parameter/fill assumptions;
- acceptable drawdown and tail-loss behavior;
- no material look-ahead or survivorship bias;
- startup/restart reconciliation;
- duplicate-order protection;
- uncertain-order handling;
- partial-fill handling;
- stale-data fail-closed behavior;
- broker-state divergence handling;
- idempotent recovery;
- emergency-stop behavior;
- and successful paper-soak operation.

## Methodology correction — return-first re-audit

A recurring interpretation error has been identified: large historical drawdown was sometimes treated as an implicit rejection criterion even when no explicit drawdown constraint had been established. That is corrected going forward.

The project objective includes substantial absolute wealth creation. Drawdown, tail loss, recovery time, execution feasibility, and operational survivability remain important measurements, but none is an automatic veto. Defensive controls must be evaluated as explicit tradeoffs against terminal wealth rather than assumed to be improvements.

The previously developed high-return leveraged strategies must therefore remain first-class research candidates. In particular, the DMA250/top-2/5-session family rotation and other earlier leveraged-ETF controls must be re-audited for terminal wealth, account survival, recovery behavior, execution sensitivity, cost sensitivity, chronological robustness, and parameter robustness before a lower-return risk overlay is allowed to replace them.

See docs/02-research/return-first-strategy-re-audit-2026-10-03.md for the full corrected framework.

## Current research priorities

1. Preserve the chronological holdout and do not tune against it.
2. Continue analyzing the bull/cash/bear matrix and family-level portfolio behavior.
3. Compare inverse exposure against cash under common stress periods and across families.
4. Do not force options into the portfolio unless account-feasible, out-of-sample evidence supports doing so.
5. Freeze a production candidate only after the research matrix is sufficiently narrowed without holdout optimization.
6. Build the strategy-specific paper-trading implementation only after that freeze.
7. Run the paper soak before considering any live autonomous deployment.

No candidate is promoted by this document.


## 2026-10-04 — Tier-A path-survivability analysis completed

The Tier-A rolling survivability workflow completed successfully as GitHub Actions run **37182850500**. The frozen control set was evaluated over **2010-03-11 → 2026-10-02** using overlapping 1-, 3-, 5-, and 10-year windows.

The results materially sharpen the current control comparison:

- **TQQQ buy-and-hold:** 41.44% full-period CAGR, $1,558,429 from $5,000, -81.66% max DD; worst rolling CAGR was -81.15% over 1 year, -11.25% over 3 years, +5.66% over 5 years.
- **SOXL buy-and-hold:** 40.30% CAGR, $1,363,182, -90.46% max DD; worst 5-year rolling CAGR was -3.76%.
- **SPXL buy-and-hold:** 29.01% CAGR, $339,693, -76.86% max DD; worst 5-year rolling CAGR was -4.54%.
- **TQQQ 200-DMA/next-open:** 32.12% CAGR, $504,212, -48.14% max DD; worst rolling CAGR was -39.03% over 1 year, -5.48% over 3 years, and +12.96% over 5 years. No observed 1-, 3-, 5-, or 10-year window breached a 50% drawdown in this artifact.
- **DMA250/top-2/5 family rotation:** 29.85% direct-control CAGR, $378,052, -67.40% max DD; 80.13% of observed 3-year windows breached 50% drawdown.

These statistics are overlapping-window path diagnostics, not independent statistical samples. They do not select a production strategy.

The dedicated rolling artifact therefore changes the immediate research question from "does drawdown matter?" to "which return-preserving control provides the best survivability under explicitly defined operational constraints?"

## 2026-10-04 — Causal TQQQ DMA/re-entry follow-up launched

The prior TQQQ DMA/re-entry grid was deliberately based on a simplified prior-session/next-session return convention. Because **TQQQ 200-DMA/next-open** is now a major control, a second frozen experiment has been added: the same 8 DMA windows × 7 re-entry confirmations, but with state changes executed at the next session's open.

The new matrix tests **0/1/3/5/10/15/20-session re-entry confirmation** across **100/125/150/175/200/225/250/300 DMA**, with **0/10/25/50 bps** turnover-cost stress. This prevents either the 5-session rule or the prior-close execution convention from becoming an untested assumption.

The workflow is currently running as GitHub Actions run **37184126854**. Its results must be compared directly with the prior-close grid before any DMA/re-entry configuration is treated as a leading candidate.

A dedicated reproducible workflow now evaluates the frozen Tier-A controls on the same empirical period using overlapping 1-, 3-, 5-, and 10-year rolling windows. It reports worst/best rolling CAGR, worst/best internal drawdown, and rolling-window breach incidence at 50%, 60%, 70%, and 80% drawdown thresholds, plus negative-CAGR and sub-10%-CAGR incidence.

The control set is:
- TQQQ buy-and-hold
- SOXL buy-and-hold
- SPXL buy-and-hold
- TQQQ 200-DMA/next-open
- frozen DMA250/top-2/cadence-5 family rotation

This is a descriptive robustness gate, not a parameter optimization. Rolling windows overlap and therefore are not independent statistical samples.

## 2026-10-04 — Return-first unified control gate

ETF-031 and the $5,000 family-rotation account replay are now the controlling offensive-ETF evidence through **2026-10-02**. The research-tests suite remains green after the endpoint/data-integrity corrections.

The authoritative direct-control comparison is now:

- TQQQ buy-and-hold: **$1,558,429**, 41.44% CAGR, -81.66% max DD.
- SOXL buy-and-hold: **$1,363,182**, 40.30% CAGR, -90.46% max DD.
- TQQQ 200-DMA/next-open: **$504,212**, 32.12% CAGR, -48.14% max DD.
- Frozen DMA250/top-2/5 family rotation: **$378,052**, 29.85% CAGR, -67.40% max DD.
- SPXL buy-and-hold: **$339,693**, 29.01% CAGR, -76.86% max DD.
- TQQQ 200-DMA/cash: **$329,962**, 28.78% CAGR, -50.01% max DD.

At 25 bps in the whole-share $5,000 family replay, the raw family rotation ends at **$228,285 prior-close / $176,531 next-open**, while DD20/DD25/DD30 overlays finish approximately $23k–$34k. This confirms a large wealth-versus-drawdown tradeoff rather than an automatic case for the defensive overlays.

The previous 2026-09-25 offensive dollar figures are superseded. See docs/02-research/unified-offensive-control-comparison-2026-10-04.md for the single current comparison and docs/02-research/dma-family-rotation-5000-account-replay.md for account-level execution details.

### Current gate

Do not select a production strategy yet. The next gate is **path survivability + chronological robustness + execution realism + operational paper-readiness** for the Tier-A offensive controls. The project should maximize robust wealth subject to predeclared survivability and operational constraints, rather than minimizing drawdown or maximizing historical CAGR without constraints.
