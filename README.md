# Trading Bot

Research and development repository for a regime-switching automated trading system.

## Strategy instances

1. **ETF-001** — leveraged ETF trend-following strategy
2. **OPTIONS-001** — rules-based short-premium strategy informed by documented tastytrade/tastylive methodology
3. **SWITCH-001** — regime-switching strategy controlling eligibility for new risk

The three portfolios use one codebase and shared market data while maintaining independent cash, positions, trades, and performance records.

## Development principle

Research and documentation come before implementation. No trading rule becomes authoritative merely because it appears in an internet discussion or because an AI system proposes it.

**Source evidence → reconciled specification → deterministic strategy/risk rules → execution**

AI may assist with research and regime classification, but it may not override hard risk controls or strategy exit rules.

## Current research gate — 2026-09-28

The first corrected $5,000 account-feasibility replay completed successfully.

The current OPTIONS-001 configuration uses one-contract SPY short strangles. Under the current modeled 50%-of-NLV BPR ceiling, **capital feasibility remains a separate gate; the $5,000 starting account is now the canonical baseline for research.** The dominant rejection was buying-power capacity.

This is a strategy/account feasibility result, not an execution failure. The unconstrained options replay remains useful for studying trade economics, but its historical P/L cannot be treated as realizable by the $5,000 account.

The next research stage is therefore to test:

- an unconditional/all-market OPTIONS-001 baseline, so the options portfolio is measured independently across the full historical sample;
- turbulent-only and broad-sideways options eligibility;
- capital-feasibility sensitivity at $5,000 and $10,000;
- defined-risk options structures that can actually fit small accounts;
- 0DTE structures using timestamped intraday data when the data-quality gate is satisfied;
- validation of the research BPR model against broker behavior;
- combined ETF + options regime-switching economics.

ETF-001 currently has a complete historical replay from 2010-03-11 through 2026-09-25. The plain 200-day trend version produced a 19.53% annualized return in that historical model versus 13.05% for the DMA+VIX variant, with maximum drawdowns of approximately 37.5% and 41.4%, respectively. These are backtest results, not forecasts.

## 0DTE benchmark update — 2026-09-29

The first free 0DTESPX benchmark completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ put-credit spread returned +1.04% total with a 0.07 annualized Sharpe and -16.57% maximum drawdown; the 20Δ/10Δ and 25Δ/15Δ variants returned -15.55% and -18.83%. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $5,000 account results, and none is deployment-approved.

Detailed results: [0DTE first benchmark](docs/02-research/0dte-first-benchmark-results.md).\n\n## ETF-001 trend-matrix validation — 2026-09-30\n\nThe ETF-001 research pipeline now runs a frozen 189-candidate trend/hysteresis matrix with chronological train/validation/holdout splits, then evaluates fixed top-K training cohorts against validation and untouched holdout results. The evaluator does not use holdout performance for selection.\n\nDetailed methodology: [ETF-001 trend-matrix validation](docs/02-research/etf-001-trend-matrix-validation.md).

Frozen follow-up runners are available:
- `python tools/0dte/run_free_call_benchmark.py`
- `python tools/0dte/run_free_iron_condor_benchmark.py`

Run them locally from the repository root. They prompt for credentials without echoing the password and write sanitized JSON under `artifacts/`. Upload the resulting JSON for analysis. Do not share credentials or session tokens.

## 0DTE call benchmark update — 2026-09-29

The mirrored 0DTESPX call-credit benchmark also completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ, 20Δ/10Δ, and 25Δ/15Δ call-credit spreads returned -18.01%, -25.74%, and -28.85%, respectively, with maximum drawdowns of approximately 19.50%, 29.12%, and 31.02%. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $5,000 account results, and none is deployment-approved.

The paired put/call comparison shows materially different daily behavior by market direction, so the next 0DTE test is a frozen management-timing matrix across both bullish and bearish defined-risk verticals rather than further unconstrained strike optimization.

Detailed results: [0DTE call benchmark](docs/02-research/0dte-call-benchmark-results.md).


## 0DTE iron-condor benchmark update — 2026-09-29

The symmetric 0DTESPX iron-condor benchmark completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ condor returned +14.01% total with a 0.419 annualized Sharpe and -9.14% maximum drawdown. The 20Δ/10Δ and 25Δ/15Δ variants returned -11.79% and -21.12%, respectively. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $5,000 account results, and none is deployment-approved.

This makes the 16Δ/6Δ condor an important research control, but not a production selection. The next frozen experiment is a 45-cell management-timing matrix covering the three put spreads, three call spreads, and three iron condors at five fixed time exits while keeping entry, deltas, and the 50% profit target unchanged.

Detailed results: [0DTE iron condor benchmark](docs/02-research/0dte-iron-condor-benchmark-results.md).

Runner: `python tools/0dte/run_free_management_timing_matrix.py`

## 0DTE automated benchmark workflow

The 0DTESPX runners now support non-interactive credentials through the environment variables `ODTESPX_EMAIL` and `ODTESPX_PASSWORD`. The repository includes an on-demand GitHub Actions workflow, **0DTE 0DTESPX Benchmark**, with the four frozen benchmark choices: put, call, iron-condor, and timing-matrix.

The workflow does not download the historical archive. It uses 0DTESPX's strategy-preview/backtest service and uploads the sanitized JSON result as a GitHub Actions artifact. This avoids repeated credential entry and eliminates the need to upload each result to ChatGPT manually.

One-time setup and usage: [docs/02-research/0dte-automated-benchmarks.md](docs/02-research/0dte-automated-benchmarks.md).

## OPTIONS-002 wider-wing feasibility gate — 2026-09-30

The next defined-risk options research gate is now present on main as a manual-only GitHub Actions workflow: **OPTIONS-002 Wider-Wing Research**.

It freezes three candidates without selecting on historical performance:

- 20-delta shorts with $5 fixed wings;
- 20-delta shorts with $10 fixed wings;
- 20-delta shorts with 10-delta long wings.

Each candidate is evaluated across ALL_DAYS, BROAD_SIDEWAYS, and TURBULENT_ONLY under conservative and midpoint fills. Account feasibility is tested at $5,000 and $10,000 with 3%, 5%, and 7% defined-risk ceilings and a 50% modeled BPR ceiling.

The workflow is intentionally workflow_dispatch only. It does not promote a candidate, and holdout performance is not used for selection. Candidate rejection reasons are retained for feasibility analysis.


## OPTIONS-002 vs ETF-001 common-date holdout — 2026-10-01

A common-date comparison was added for the existing 2023+ holdout. During validation, the previously generated `etf001_dma_scaffold.csv` was found to contain non-finite portfolio values beginning 2013-01-04, so it is not used as the benchmark. The comparison rebuilds ETF-001 from the raw TQQQ/SPXL/SOXL/VIX data and explicitly checks that the rebuilt equity curve is finite.

The holdout comparison is descriptive and does not promote a candidate. The dynamic 20Δ/10Δ candidate had positive candidate-level aggregate P&L in the tested holdout files, while the fixed $5 and $10 wing variants had negative aggregate candidate P&L. Normalized P&L per defined loss remained slightly negative on average for the dynamic candidate set, so this is not deployment evidence.

Detailed findings: [OPTIONS-002 vs ETF-001 common-date results](docs/research/options002-vs-etf001-common-date-results-2026-10-01.md).

Runner: `python research/compare_options002_etf001_common_dates.py`.\n\nA separate $5,000 capital-equivalent holdout gate uses the actual account-feasibility acceptance lifecycle rather than unconstrained candidate P&L: `python research/compare_options002_etf001_capital_equivalent.py`. The current artifact shows the accepted $5,000 holdout sample is sparse and concentrated in $5-wing turbulent-only configurations; this is a feasibility finding, not a strategy selection.

## Autonomous-operation requirement

Profitability is the primary objective. Autonomous operation is a required capability, not a replacement for profitability.

Before unattended paper/live operation, the system must demonstrate both:

1. a sufficiently robust economic edge after realistic fills, fees, account constraints, and held-out validation; and
2. restart-safe execution, broker reconciliation, duplicate-order protection, deterministic risk controls, and tested failure recovery.

See docs/03-execution/autonomous-operation.md for the execution architecture and deployment gates.

See docs/02-research/account-feasibility-2000.md for the legacy $2,000 feasibility findings; the active starting balance is $5,000.

See docs/01-strategies/tastytrade-strategy.md for the current options methodology draft.


## Research update — 2026-10-03

The leveraged-ETF research has moved beyond the original 200-DMA/inverse-switch experiments. ETF-017 established the canonical-accounting inverse-overlay benchmark; ETF-018 showed that MACD/channel/momentum/breadth combinations can materially improve some validation periods but did not survive the 2023+ holdout. ETF-020 through ETF-024 then tested broad technical-indicator ML, walk-forward retraining, retraining cadence, and transaction-cost stress. The walk-forward signal produced only a small, event-sparse improvement, so it remains research-only.

The next diagnostics are intentionally focused rather than another blind parameter sweep:
- ETF-019 measures which bearish signal families lead sustained weakness and how often they produce false triggers.
- ETF-025 tests whether the walk-forward holdout improvement is unusually concentrated in its three observed activation dates by comparing them with deterministic random-date placebos.

ETF-025 found that the small walk-forward holdout improvement was concentrated around a few activation dates, so it was followed by ETF-026 bearish event-archetype diagnostics and ETF-027 signal-transition diagnostics. ETF-027 found that bearish event starts are not characterized by a simple monotonic rise in the six family scores. A July 2024 activation pattern differed structurally from the 2022-12-28 false positive, but MACD fade alone was not sufficient. ETF-028 now stratifies the event population by pre-event trend/breadth context to test that distinction across the full historical sample. These remain diagnostics only; none promotes a trading rule.


## ETF-029 context robustness — 2026-10-03

ETF-029 adds a fixed robustness diagnostic around ETF-028. It repeats the bearish-event context classification at 3, 5, 10, 15, and 20 sessions before each event, using fixed non-overlapping healthy/bearish cutoffs of 1/3, 0.40, and 1/2. The experiment measures the same 20-session event outcome and does not optimize a trading rule or select a cutoff. Its purpose is to determine whether ETF-028 context differences survive reasonable changes in the pre-event observation point.

Runner: `python research/backtest_etf029_context_robustness.py`.


## ETF-030 temporal stability — 2026-10-03

ETF-030 extends the ETF-029 robustness gate by splitting the bearish-event sample into four calendar eras (2007–2014, 2015–2019, 2020–2022, and 2023–2026) and repeating the same fixed lag/cutoff context diagnostics inside each era. This is a temporal-stability check, not a parameter-selection sweep: no lag, cutoff, or trading rule is promoted from the results.

Runner: `python research/backtest_etf030_era_stability.py`.


## ETF-030 temporal-stability result — 2026-10-03

ETF-030 completed successfully. Across the tested eras, pre-event trend/breadth context produced only small differences in the already-qualified bearish-event sample; the groups remained broadly negative rather than separating into a clearly distinct predictive class. Because ETF-030 conditions on a known 20-session loss event, it is useful as a structural diagnostic but is not evidence of forward predictive power. The bearish-transition context branch therefore remains research-only and should not be promoted into an exit rule without an all-days, signal-availability, and out-of-sample strategy replay.

## Bull/cash/bear switching matrix — 2026-10-03

The existing `research/test_dma_bull_bear_switching.py` matrix now has an automated GitHub Actions workflow. It tests benchmark-DMA switching among BULL, CASH, and BEAR states across SP500, NASDAQ100, semiconductors, Dow 30, and Russell 2000 families. The implementation enforces the hard per-family constraint that a family can never hold its bull and bear ETF simultaneously. Cross-family directional differences are permitted, so a portfolio can hold, for example, a Dow bull sleeve while a semiconductor sleeve is bearish. Results are split into full, train, validation, and 2023+ holdout views; the predefined headline controls are reported rather than selected from holdout performance.


## Family-rotation risk-overlay research — 2026-10-03

The current deterministic ETF research target is the frozen **250-DMA / top-2 / 5-session family rotation** candidate across SPXL, TQQQ, SOXL, UDOW, and TNA, with cash when no family qualifies. Its historical return profile is promising but its approximately 65–68% maximum drawdown is too large to treat as deployment-ready.

The next gate therefore does not broaden the selector. The risk-overlay runner keeps that base candidate frozen and tests causal portfolio-level risk controls: prior-close realized-volatility targeting and a simple drawdown de-risking overlay. The matrix includes 20/60-session volatility windows, fixed volatility targets, drawdown thresholds, and 0/10/25/50 bps transaction-cost stress. Train/validation/holdout results are retained separately; holdout is not used for candidate selection.

The purpose of this stage is to determine whether risk can be reduced without destroying the underlying family-rotation edge. A positive result would still require further walk-forward robustness, subperiod analysis, account-level replay at the canonical $5,000 starting balance, and paper trading before any live deployment.


### Risk-overlay result — 2026-10-03

The first frozen risk-overlay matrix completed successfully in about 1.5 minutes. The raw 250-DMA/top-2/5-session rotation produced 19.18% CAGR in train, 12.93% in validation, and 80.13% in holdout, with maximum drawdowns of roughly 64–67%. These figures are historical diagnostics, not forecasts.

The simple overlay produced a meaningful risk reduction. The most useful robustness cluster from the initial matrix is around a **30% volatility target, 20-session lookback, and 20–30% drawdown trigger**. For example, the V30/L20/DD25 variant had train/validation/holdout CAGRs of 7.78% / 10.32% / 36.82%, with maximum drawdowns of -38.50% / -29.88% / -32.82%. At 25 bps transaction cost those CAGRs were 4.75% / 8.17% / 33.54%. V30/L20/DD30 was similar: 8.11% / 14.70% / 36.95% at zero cost and 5.06% / 12.35% / 33.83% at 25 bps.

This is not yet a selected production configuration. The next gate is parameter-neighborhood/era robustness for this small cluster, followed by a $5,000 account-level replay using realistic position sizing and execution constraints. The objective is to determine whether the drawdown reduction survives different historical periods and practical implementation friction before paper trading.


The era-robustness pass completed: the 30% target / 20-session lookback / 20–30% drawdown-trigger cluster remained positive in all four calendar eras even at 25 bps costs. For example, V30/L20/DD20 had 25-bps era CAGRs of 9.41%, 0.26%, 8.62%, and 25.26% across 2010–2014, 2015–2019, 2020–2022, and 2023–2026; V30/L20/DD25 produced 8.26%, 1.50%, 8.17%, and 33.54%; V30/L20/DD30 produced 6.82%, 3.41%, 12.35%, and 33.83%. These are descriptive historical results and do not establish future performance. The cluster is therefore being carried forward as a robustness region rather than a single optimized parameter point.


## $5,000 account replay and next-open execution — 2026-10-03

The $5,000 account-feasibility replay completed successfully using whole-share positions, explicit residual cash, 0/10/25/50 bps transaction-cost stress, and chronological train/validation/holdout reporting. It now evaluates both the existing prior-close research convention and a causal next-open execution sensitivity.

At 25 bps across the full 2010–2026 sample, the raw 250-DMA/top-2/5-session rotation produced 25.63% CAGR with prior-close execution and 23.61% with next-open execution, while maximum drawdown remained about 69%. The risk-overlay cluster remained materially less exposed: the V30/L20/DD20, DD25, and DD30 variants produced approximately 9.62%/11.12%/12.11% full-period CAGR with prior-close execution and 9.96%/11.93%/11.20% with next-open execution; corresponding full-period maximum drawdowns were roughly 39%–48%.

The three V30/L20 variants remained positive across train, validation, and 2023+ holdout in the account replay under both execution sensitivities at 25 bps. These are historical implementation diagnostics, not forecasts or production selections. The $5,000 whole-share constraint is therefore not the primary blocker; portfolio drawdown and execution realism remain the key gates.

Detailed methodology and results: [ETF family-rotation $5,000 account replay](docs/02-research/dma-family-rotation-5000-account-replay.md).


## Return-first drawdown re-audit — 2026-10-03

A retrospective audit was added after identifying a recurring interpretation error: large historical drawdown was sometimes given veto-level weight even when no explicit drawdown constraint had been established. The audit distinguishes genuine drawdown-driven deprioritization from candidates rejected for holdout failure, lost absolute return, transaction costs, accounting problems, or feasibility.

The clearest confirmed case is the raw **DMA250/top-2/5-session family rotation**. At 25 bps and a $5,000 starting balance it ended around $217,586 under prior-close execution and $166,456 under next-open execution, versus roughly $22,825–$33,102 for the tested risk-overlay cluster. The raw strategy's roughly 69% maximum drawdown is therefore treated as a measured path characteristic and an explicit tradeoff, not an automatic rejection criterion.

The audit preserves aggressive leveraged controls as first-class benchmarks and requires future drawdown-based rejection to be justified by an explicit survival, broker, operational, or predeclared risk constraint.

Detailed audit: [Return-first drawdown re-audit](docs/02-research/return-first-drawdown-reaudit.md).


## ETF-031 — TQQQ offensive benchmark robustness audit

ETF-031 treats 100% TQQQ buy-and-hold as a first-class offensive benchmark rather than rejecting it because of drawdown alone. The audit uses one common empirical period across the direct TQQQ/QQQ/SOXL/SPXL offensive controls and keeps the starting account at $5,000. It compares TQQQ buy-and-hold, QQQ buy-and-hold, SOXL buy-and-hold, SPXL buy-and-hold, TQQQ 200-DMA/cash, the frozen DMA-250/top-2/5-session family rotation, and the previously frozen V30/L20/DD20/25/30 overlays. It stresses 0/10/25/50 bps costs, rolling 1/3/5/10-year windows, recovery time, start dates, calendar eras, removal of each calendar year, exact-return path sequencing, and explicit 5/10/20-year forward scenarios at fractions of historical TQQQ CAGR including one-third. ETF-031 is an audit rather than a parameter-selection sweep; drawdown is measured as a path characteristic and only becomes a rejection criterion if an explicit survival, broker, operational, or predeclared risk constraint requires it.
