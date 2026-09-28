# Historical Regime Validation Research

**Status:** Research specification — 2026-09-28

## Objective

Test the core hypothesis behind SWITCH-001 before adding more indicators:

> ETF-001 should remain active for most of the time, while OPTIONS-001 should become eligible primarily during sideways/choppy or turbulent/high-volatility regimes.

This research must answer three separate questions:

1. Do the proposed regimes correspond to materially different outcomes for ETF-001?
2. Are the regime labels stable and sufficiently frequent to be operationally useful?
3. Do the proposed sideways/turbulent windows contain enough actual options opportunities for OPTIONS-001 to be a practical alternate strategy?

A regime is not accepted because it sounds economically plausible. It must demonstrate out-of-sample usefulness.

## Historical sample

Use the longest common history available for all ETF-001 instruments:

- TQQQ
- SPXL
- SOXL
- VIX

The initial common sample begins in 2010, subject to verified source availability.

The dataset should retain the complete available history rather than selecting only famous crisis periods. Named episodes such as 2011, 2015–16, 2018 Q4, 2020 COVID, 2022 bear market, and later volatility episodes are useful for interpretation but must not be selected as the statistical sample.

VIX is sourced from CBOE via FRED (series VIXCLS). CBOE identifies VIX as a measure of expected near-term U.S. equity-market volatility. The FRED series is daily close data.

## Dataset layers

The research dataset should contain four logical layers.

### 1. Raw market data

Daily observations with:

- date
- open
- high
- low
- close
- adjusted close where supplied
- volume
- symbol
- source

Required symbols:

- TQQQ
- SPXL
- SOXL
- SPY or another broad U.S. equity benchmark
- VIX

### 2. Derived regime features

Calculate without using future information:

- benchmark close vs 200-day SMA
- 200-day SMA slope
- ADX
- Kaufman Efficiency Ratio
- 20-day realized volatility
- 60-day realized volatility
- VIX level
- VIX percentile using a trailing historical window
- 5-day VIX change
- benchmark 20-day return
- benchmark 60-day return
- benchmark 20-day high-low range
- benchmark drawdown from trailing 252-day high

Every feature must be timestamped using information available at that day's decision time.

### 3. Regime label

The first implementation should use the existing SWITCH-001 research specification rather than inventing new indicators.

The initial research labels are:

- 'TRENDING_NORMAL'
- 'SIDEWAYS_CHOPPY'
- 'TURBULENT_HIGH_VOL'

Thresholds remain research parameters until validated.

Do not optimize thresholds against the entire historical sample. Threshold selection must be performed on a training period and evaluated on a later validation period.

### 4. Strategy outcome layer

For every trading day and regime, calculate:

- ETF-001 daily return
- ETF-001 cumulative return
- ETF-001 maximum drawdown
- ETF-001 realized volatility
- ETF-001 time invested
- benchmark return
- benchmark maximum drawdown
- number and duration of ETF exits caused by the 200-DMA rule
- number of VIX safety-rule exits
- post-exit re-entry delay

## ETF-001 backtest definition

The historical test must reproduce the intended strategy rather than use a generic leveraged-ETF backtest.

Initial rules:

- 25% TQQQ
- 25% SPXL
- 25% SOXL
- 25% cash
- sell a leveraged ETF when it closes below its 200-day moving average
- re-enter only after it has remained above the 200-day moving average for a full week
- retain the proposed VIX safety mechanism around VIX 28 as a separately measured rule

The VIX rule must be tested in two forms:

1. ETF-001-DMA: only the 200-DMA rules
2. ETF-001-DMA-VIX: 200-DMA rules plus the VIX safety rule

This isolates whether the VIX rule actually improves the ETF strategy rather than allowing it to hide behind the regime classifier.

Transaction costs, slippage, and dividends/splits must be represented consistently in the eventual executable backtest.

## Regime validation tests

For each regime, compare ETF-001 against the same strategy without regime filtering.

Primary measurements:

- annualized return
- maximum drawdown
- Sharpe ratio
- Sortino ratio
- percentage of profitable days
- volatility
- worst day
- worst rolling 20-day return
- worst rolling 60-day return
- time spent in regime
- ETF-001 return while regime is active
- ETF-001 drawdown while regime is active

The most important question is not whether one regime has the highest return. The test is whether the regime labels separate materially different risk/return conditions.

For SWITCH-001 specifically, measure:

- ETF return during TRENDING_NORMAL
- ETF return during SIDEWAYS_CHOPPY
- ETF return during TURBULENT_HIGH_VOL
- drawdown contribution from each regime
- fraction of ETF drawdown days occurring in non-trending regimes
- fraction of total ETF profit earned during trending regimes

## Avoiding look-ahead bias

All regime decisions must be made from information available at the close used by the strategy.

If execution is modeled at next-session open, today's close may determine tomorrow's state.

No future VIX value, future return, future volatility, or completed future moving-average information may enter today's label.

Regime transitions must therefore be evaluated with an explicit one-bar execution delay.

## OPTIONS-001 validation

There are two distinct tests.

### Phase A — opportunity-density test

Using the public underlying/VIX dataset, identify every day that satisfies the current OPTIONS-001 eligibility regime.

Measure:

- number of candidate entry days
- number of candidate windows
- average candidate-window duration
- median candidate-window duration
- number of windows lasting at least 21 trading days
- number lasting at least 45 calendar days
- percentage of the full sample classified as options-eligible
- number of transitions into and out of eligibility

This answers whether SWITCH-001 would actually give OPTIONS-001 enough operating time.

### Phase B — historical option-chain replay

A true test of OPTIONS-001 cannot be inferred from VIX alone.

For each candidate entry day, replay actual historical option chains and apply the documented trade mechanics:

- approximately 45 DTE entry where specified
- short strangle construction
- delta/strike selection according to the authoritative OPTIONS-001 rules
- 50% profit target
- 21 DTE management
- documented challenged-trade defenses
- position-sizing constraints

Record:

- entries
- exits
- win/loss
- credit received
- P/L
- maximum adverse excursion
- duration
- buying-power usage
- margin requirement
- number of challenged positions
- number of rolls
- number of inversions
- number of positions that cannot be opened because the account is too small

The first historical replay should use SPY if it is the authoritative OPTIONS-001 underlying. Additional underlyings should only be added after the underlying-universe research explicitly authorizes them.

## Important data limitation

CBOE provides historical VIX data publicly, but complete historical option trades/quotes are a separate data product. CBOE's historical option-trade dataset is available from January 2012 and is offered through Cboe DataShop.

Therefore:

- VIX/regime analysis can be performed immediately from public data.
- ETF-001 can be backtested from historical ETF prices.
- OPTIONS-001 candidate-window frequency can be tested without option chains.
- OPTIONS-001 actual historical P/L and trade viability requires historical option-chain/trade data.

We must not present the opportunity-density test as a completed options backtest.

## Acceptance criteria

Do not finalize SWITCH-001 merely because the classifier produces visually appealing historical labels.

The research passes to the next design stage only if:

1. ETF-001 outcomes differ meaningfully across at least some regimes.
2. The differences persist in a held-out validation period.
3. SIDEWAYS_CHOPPY and TURBULENT_HIGH_VOL are not so rare that OPTIONS-001 receives too few opportunities.
4. Regime transitions are not so frequent that switching itself creates excessive turnover.
5. OPTIONS-001 produces a measurable number of historical candidate entries.
6. A true option-chain replay is subsequently able to verify whether those candidates were actually tradable and economically viable.
7. No threshold is accepted solely because it maximizes historical returns.

## Initial research periods

Use chronological walk-forward evaluation rather than random train/test sampling.

Suggested first split:

- Training: 2010–2018
- Validation: 2019–2022
- Out-of-sample holdout: 2023–present

The split is deliberately chronological so that no information from later market conditions leaks into earlier parameter selection.

## Expected deliverables

The research implementation should produce:

- historical_market_data.csv
- historical_regime_dataset.csv
- etf_strategy_backtest.csv
- regime_summary.csv
- options_opportunity_windows.csv
- research_report.md

The CSV files are generated artifacts and should not be committed to the repository by default if they are large. The repository should instead contain the reproducible data-ingestion and backtest code plus small validation fixtures.

## External evidence

Cboe/FRED documents VIX as a daily-close index measuring expected near-term volatility. Cboe provides historical VIX data from 1990 onward.

tastylive's published research supports using 45-DTE short strangles and managing winners at 50% of credit or positions at 21 DTE as documented mechanics. Its published studies also report that higher implied-volatility environments can produce larger premiums and P/L while increasing P/L volatility. These are methodology inputs, not proof that OPTIONS-001 will work in this project's regime-switching system.

Sources:

- Cboe VIX historical data
- FRED VIXCLS
- tastylive, 'How to Use Options Strategies & Key Mechanics'
- tastylive, 'The Impact of High Implied Volatility (IV) on Trading Profits'
- Cboe DataShop historical option-trade data documentation
