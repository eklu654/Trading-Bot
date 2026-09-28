# Tastytrade/Tastylive Methodology Research

**Status:** Research baseline — not frozen for implementation  
**Last reviewed:** 2026-09-27

## Purpose

This document separates documented tastytrade/tastylive mechanics from project-specific interpretations. The project will not encode a trading rule merely because it is commonly repeated online.

## Primary-source findings

The current tastytrade developer documentation provides a useful, concrete backtesting example: SPY short 16-delta put, 45 days until expiration, with a 50% take-profit condition. The same API also supports VIX entry/exit bounds, maximum active trials, stop-loss percentage, days-in-trade exits, and days-to-expiration exits. This demonstrates that these are supported backtesting parameters; it does **not**, by itself, establish that every one is a universal tastytrade trading rule.

The official documentation therefore supports the following as **documented example parameters**:

- 45 DTE
- 16-delta short put
- 50% take-profit
- Optional VIX entry/exit filters
- Optional 21-day time-in-trade exit
- Optional DTE-based exit

Source: https://developer.tastytrade.com/docs/guides/backtesting/

## Portfolio delta

Current tastytrade educational material states that the platform exposes portfolio-level **beta-weighted Delta**, alongside Theta, Gamma, Vega and other aggregate exposures. Greeks are dynamic and change with price, time and volatility.

For this project, portfolio directional exposure should therefore be represented using beta-weighted Delta rather than simply summing contract deltas. The exact benchmark and neutrality band remain research decisions.

Source: https://tastytrade.com/learn/trading-products/options/analyzing-options-greeks/

## What is not established

The research currently does **not** establish:

1. A universal current tastytrade rule requiring exactly 45 DTE.
2. A universal current tastytrade rule requiring exactly 16 delta for every strategy.
3. A universal current tastytrade rule requiring exactly 50% profit management.
4. A universal current tastytrade rule requiring exactly 21 DTE management.
5. A universal numerical VIX-to-buying-power allocation schedule.
6. A universal portfolio beta-weighted Delta target such as exactly zero.

Those values may be useful hypotheses because they appear in official examples or platform workflows, but the project must test them rather than promote them to immutable methodology without stronger source evidence.

## Project baseline

Until the research phase produces stronger evidence, the options backtester should expose these values as configurable parameters:

- target DTE: 45
- target short delta: 16
- take profit: structure-specific
- management DTE: structure-specific; 21 DTE is a strong research baseline for several short-premium structures
- time-in-trade: configurable
- VIX entry floor/ceiling: configurable
- portfolio beta-weighted Delta neutrality band: configurable

### Structure-specific mechanics now verified

An official tastylive mechanics guide documents the following examples:

- short strangle: 50% of credit received or 21 DTE;
- iron condor: 50% of credit received or 21 DTE;
- credit spread: 50% of credit received or 21 DTE;
- ratio spread: 30% of max profit;
- broken-wing butterfly: 25% of max profit;
- diagonal: 25% of max profit.

This is stronger evidence than treating 50%/21 DTE as a universal strategy rule. The project should encode exits by structure and preserve these values as documented mechanics, subject to backtesting and current-source review.

Official research also supports 45 DTE as a common duration and shows that DTE can be adjusted with IV: 60 DTE when IVR is low, 45 DTE generally, and 30 DTE when IVR is higher in one SPY study. 21-DTE management reduced P/L volatility across the tested durations.

No parameter becomes a hard production rule until it is documented in the strategy specification and supported by backtesting.

## Research discipline

Every strategy parameter should be classified as one of:

- **Primary-source verified** — directly supported by an authoritative source.
- **Documented example** — appears in an official example but is not shown to be universal.
- **Project rule** — deliberately chosen by this project.
- **Experimental parameter** — being tested through backtesting.
- **Unresolved** — insufficient evidence to encode.

This classification prevents accidental conversion of examples into dogma.

## References

- tastytrade Developer Docs — Run a backtest: https://developer.tastytrade.com/docs/guides/backtesting/
- tastytrade Developer Docs — Create a backtest: https://developer.tastytrade.com/reference/backtesting/postBacktests/
- tastytrade — Analyzing Options Greeks: https://tastytrade.com/learn/trading-products/options/analyzing-options-greeks/
