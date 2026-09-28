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

See `docs/01-strategies/tastytrade-strategy.md` for the current options methodology draft.


<!-- CI validation branch: account feasibility replay verification. -->
