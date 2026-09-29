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

The first corrected $2,000 account-feasibility replay completed successfully.

The current OPTIONS-001 configuration uses one-contract SPY short strangles. Under the current modeled 50%-of-NLV BPR ceiling, **0 of 929 historical candidate entries were feasible in the $2,000 account**. The dominant rejection was buying-power capacity.

This is a strategy/account feasibility result, not an execution failure. The unconstrained options replay remains useful for studying trade economics, but its historical P/L cannot be treated as realizable by the $2,000 account.

The next research stage is therefore to test:

- an unconditional/all-market OPTIONS-001 baseline, so the options portfolio is measured independently across the full historical sample;
- turbulent-only and broad-sideways options eligibility;
- capital-feasibility sensitivity at $2,000, $5,000, and $10,000;
- defined-risk options structures that can actually fit small accounts;
- 0DTE structures using timestamped intraday data when the data-quality gate is satisfied;
- validation of the research BPR model against broker behavior;
- combined ETF + options regime-switching economics.

ETF-001 currently has a complete historical replay from 2010-03-11 through 2026-09-25. The plain 200-day trend version produced a 19.53% annualized return in that historical model versus 13.05% for the DMA+VIX variant, with maximum drawdowns of approximately 37.5% and 41.4%, respectively. These are backtest results, not forecasts.

## 0DTE benchmark update — 2026-09-29

The first free 0DTESPX benchmark completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ put-credit spread returned +1.04% total with a 0.07 annualized Sharpe and -16.57% maximum drawdown; the 20Δ/10Δ and 25Δ/15Δ variants returned -15.55% and -18.83%. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $2,000 account results, and none is deployment-approved.

Detailed results: [0DTE first benchmark](docs/02-research/0dte-first-benchmark-results.md).

Frozen follow-up runners are available:
- `python tools/0dte/run_free_call_benchmark.py`
- `python tools/0dte/run_free_iron_condor_benchmark.py`

Run them locally from the repository root. They prompt for credentials without echoing the password and write sanitized JSON under `artifacts/`. Upload the resulting JSON for analysis. Do not share credentials or session tokens.

## 0DTE call benchmark update — 2026-09-29

The mirrored 0DTESPX call-credit benchmark also completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ, 20Δ/10Δ, and 25Δ/15Δ call-credit spreads returned -18.01%, -25.74%, and -28.85%, respectively, with maximum drawdowns of approximately 19.50%, 29.12%, and 31.02%. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $2,000 account results, and none is deployment-approved.

The paired put/call comparison shows materially different daily behavior by market direction, so the next 0DTE test is a frozen management-timing matrix across both bullish and bearish defined-risk verticals rather than further unconstrained strike optimization.

Detailed results: [0DTE call benchmark](docs/02-research/0dte-call-benchmark-results.md).


## 0DTE iron-condor benchmark update — 2026-09-29

The symmetric 0DTESPX iron-condor benchmark completed across 1,012 sessions per candidate (2022-06-16 through 2026-09-28). The 16Δ/6Δ condor returned +14.01% total with a 0.419 annualized Sharpe and -9.14% maximum drawdown. The 20Δ/10Δ and 25Δ/15Δ variants returned -11.79% and -21.12%, respectively. All results include platform-reported fees and slippage. These are $100,000 platform previews, not $2,000 account results, and none is deployment-approved.

This makes the 16Δ/6Δ condor an important research control, but not a production selection. The next frozen experiment is a 45-cell management-timing matrix covering the three put spreads, three call spreads, and three iron condors at five fixed time exits while keeping entry, deltas, and the 50% profit target unchanged.

Detailed results: [0DTE iron condor benchmark](docs/02-research/0dte-iron-condor-benchmark-results.md).

Runner: `python tools/0dte/run_free_management_timing_matrix.py`

## 0DTE automated benchmark workflow

The 0DTESPX runners now support non-interactive credentials through the environment variables `ODTESPX_EMAIL` and `ODTESPX_PASSWORD`. The repository includes an on-demand GitHub Actions workflow, **0DTE 0DTESPX Benchmark**, with the four frozen benchmark choices: put, call, iron-condor, and timing-matrix.

The workflow does not download the historical archive. It uses 0DTESPX's strategy-preview/backtest service and uploads the sanitized JSON result as a GitHub Actions artifact. This avoids repeated credential entry and eliminates the need to upload each result to ChatGPT manually.

One-time setup and usage: [docs/02-research/0dte-automated-benchmarks.md](docs/02-research/0dte-automated-benchmarks.md).

## Autonomous-operation requirement

Profitability is the primary objective. Autonomous operation is a required capability, not a replacement for profitability.

Before unattended paper/live operation, the system must demonstrate both:

1. a sufficiently robust economic edge after realistic fills, fees, account constraints, and held-out validation; and
2. restart-safe execution, broker reconciliation, duplicate-order protection, deterministic risk controls, and tested failure recovery.

See docs/03-execution/autonomous-operation.md for the execution architecture and deployment gates.

See docs/02-research/account-feasibility-2000.md for the detailed $2,000 feasibility findings.

See docs/01-strategies/tastytrade-strategy.md for the current options methodology draft.
