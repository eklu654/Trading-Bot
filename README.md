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

## Autonomous-operation requirement

Profitability is the primary objective. Autonomous operation is a required capability, not a replacement for profitability.

Before unattended paper/live operation, the system must demonstrate both:

1. a sufficiently robust economic edge after realistic fills, fees, account constraints, and held-out validation; and
2. restart-safe execution, broker reconciliation, duplicate-order protection, deterministic risk controls, and tested failure recovery.

See docs/03-execution/autonomous-operation.md for the execution architecture and deployment gates.

See docs/02-research/account-feasibility-2000.md for the detailed $2,000 feasibility findings.

See docs/01-strategies/tastytrade-strategy.md for the current options methodology draft.
