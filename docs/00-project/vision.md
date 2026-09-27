# Project Vision

## Goal

Build a research-first, rules-based automated trading system capable of comparing two distinct approaches and operating a third portfolio that switches between them according to measurable market regimes.

## Strategies

### ETF trend strategy

A leveraged ETF trend-following portfolio using:

- TQQQ
- SPXL
- SOXL
- cash

The initial concept assigns 25% of the portfolio to each ETF slot, with cash occupying unused allocation.

The strategy uses a 200-day moving-average trend filter and a VIX safety mechanism.

### Options-selling strategy

A systematic short-premium portfolio informed by current tastytrade/tastylive methodology.

It emphasizes disciplined entry criteria, controlled position sizing, portfolio-level directional balance, volatility-aware buying-power allocation, mechanical exits, and no discretionary AI override.

### Regime-switching strategy

The switching portfolio uses the same underlying strategies but determines which strategy is eligible for new risk based on market conditions.

A regime transition does not automatically liquidate existing options positions.

## AI role

AI is a research and classification component, not the ultimate risk authority.

The system must remain deterministic at the execution and risk layers.

## Research philosophy

Every important rule should have a primary source, mathematical definition, documented project decision, or explicit experimental label.
