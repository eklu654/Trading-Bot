# 0DTE Research Specification

**Status:** Research specification — not production-authorized  
**Date:** 2026-09-28

## Objective

Determine whether a tastytrade/tastylive-informed 0DTE strategy can add positive, robust, account-feasible expectancy to OPTIONS-001, especially for the small-account cases.

This is a separate strategy candidate. The project will not assume that rules developed for 30–60 DTE short premium transfer unchanged to 0DTE.

## Source-derived evidence

tastylive describes 0DTE as materially different because gamma rises sharply as expiration approaches. Its research also discusses defined-risk structures such as butterflies and iron flies as ways to reduce the risk/capital burden of naked 0DTE premium selling. citeturn1search6turn1search4

tastylive research has studied multiple 0DTE entry windows and profit targets. One study found favorable results for opening short strangles near the market open and managing after roughly 90 minutes, while warning against initiating short premium late in the session. Other 2025 studies examined 10%, 25%, and 50% profit targets and IVR-dependent behavior. These findings are research observations, not a single permanent official rule set. citeturn0search3turn1search9turn3search0

## Test families

### A. 0DTE iron condor
- Defined risk.
- Short strikes selected mechanically by delta or expected move.
- Long wings selected by fixed width and/or expected-move distance.
- Test 10%, 25%, and 50% profit targets.
- Test fixed intraday time exits.
- Never hold beyond the defined expiration-session boundary.

### B. 0DTE iron fly
- Defined risk.
- ATM/near-ATM short strike.
- Symmetric or mechanically selected wings.
- Test the same profit/time matrix.

### C. 0DTE butterfly
- Defined risk.
- Test range-centered structures.
- Include the wider-wing variants discussed in tastylive research.
- Test 10%, 25%, and 50% debit-profit targets.

### D. 0DTE verticals
- Defined risk.
- Test both bullish and bearish credit structures.
- Portfolio must be approximately Delta-balanced across simultaneous positions rather than assuming one directional bias.

### E. Naked short strangle control
- Include only as a research control.
- Apply hard BPR/stress constraints.
- Do not use its historical profitability to justify deployment if account-level risk is infeasible.

## Entry-window matrix

Where timestamped data exists, test:
- opening window;
- first 30 minutes;
- first 60 minutes;
- first 90 minutes;
- mid-session;
- last 60 minutes;
- last 30 minutes.

Late-session short-premium entries must be explicitly separated because tastylive research reports materially different results near the close. citeturn0search3

## Profit-target matrix

Test:
- 10% of maximum profit;
- 25%;
- 50%.

Do not select the target using the full historical sample. Use chronological train/validation/holdout splits.

## Risk controls

For every candidate:
- defined maximum loss;
- maximum percentage of NLV at risk;
- aggregate BPR limit;
- beta-weighted Delta band;
- single-underlying concentration;
- expiration concentration;
- daily loss limit;
- stale-data halt;
- no new risk after the defined session cutoff;
- explicit handling of expiration and exercise/assignment.

## Data requirements

The current options replay dataset is daily-granularity. A valid 0DTE test requires:
- timestamped option quotes or trades;
- underlying intraday prices;
- bid/ask or executable trade prices;
- option contract identifiers;
- strikes;
- expiration;
- option type;
- delta or sufficient inputs to reconstruct delta without look-ahead;
- trading-session timestamps.

The existing workflow therefore performs a dataset audit first. If no timestamped fields exist, the project must acquire an appropriate intraday historical source before producing 0DTE P/L statistics.

## No look-ahead

Strike selection must use only information available at the simulated entry timestamp.

Profit-target detection must use subsequent timestamps only.

If the exact intraday path between two observations is unknown, the replay must not assume that a target or stop was hit.

## Primary outputs

For each structure and parameter set:
- trade count;
- net P/L;
- return on allocated capital;
- average P/L;
- win rate;
- average winner/loser;
- profit factor;
- maximum drawdown;
- worst trade;
- CVaR/expected shortfall;
- BPR;
- maximum loss;
- target-hit frequency;
- time-in-trade;
- slippage sensitivity;
- performance by VIX/IVR;
- performance by entry window;
- performance by weekday;
- event-day segmentation;
- account feasibility at $2,000, $5,000, and $10,000.

The strategy is not eligible for the combined portfolio unless it survives the same profitability, robustness, and account-feasibility gates as the other strategies.
