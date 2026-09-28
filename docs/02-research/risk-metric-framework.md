# Options Risk-Metric Framework

**Status:** Research specification — not yet production-frozen  
**Last reviewed:** 2026-09-28

## Purpose

The options system must not collapse all risk into a single number.

Current tastylive research supports treating BPR as an important operational risk gauge for undefined-risk positions, while also showing that BPR alone does not determine realized loss. The risk engine therefore uses several independent measurements.

## 1. Buying Power / BPR

BPR measures the capital reserved by the broker for a position.

tastylive's 2025 research describes BPR as a useful risk gauge for undefined-risk positions and identifies price, delta, and implied volatility as major drivers. It also reports that BPR can expand sharply when volatility and price move against a position.

A separate 2024 study found that higher BPR does not automatically mean higher realized risk: tested strangles could require substantially more BPR than iron condors without necessarily producing larger losses.

**System rule:** BPR is a hard capital-allocation constraint and a dynamic stress signal, but it is not treated as a standalone estimate of maximum loss.

## 2. BPR expansion

Initial BPR is insufficient for naked/undefined-risk positions.

The system must record:

- entry BPR;
- current BPR;
- BPR expansion multiple;
- BPR as percentage of current NLV;
- BPR as percentage of entry NLV;
- portfolio-wide BPR;
- concentration of BPR by underlying;
- change in BPR caused by price movement;
- change in BPR caused by implied-volatility movement.

2025 tastylive research documented examples where a 15% underlying move could increase BPR by more than 200%, with a worst-case example reaching 3.6× initial BPR.

**System implication:** the risk engine needs a dynamic BPR-stress control, not merely an entry-time allocation check.

## 3. Net Liquidation Value

NLV is the denominator used by the recovered historical portfolio presentation for individual trade sizing and the 15% single-underlying concentration limit.

NLV-based controls are therefore kept separate from BP-based controls.

## 4. Beta-weighted Delta

Beta-weighted Delta converts positions into an approximate SPY share-equivalent directional exposure.

Use:

- portfolio beta-weighted Delta;
- per-position beta-weighted Delta;
- directional contribution by underlying.

It is primarily a directional-bias metric.

It is **not** a substitute for BPR, notional exposure, correlation, or tail-risk testing.

## 5. Unit / notional exposure

Notional exposure measures the scale of the underlying exposure represented by the position.

This is especially important for undefined-risk positions because a position that starts near delta-neutral can acquire substantial directional exposure after a large underlying move.

The system therefore tracks notional/unit exposure independently from Delta.

## 6. Correlation

Diversifying ticker symbols does not necessarily diversify risk.

tastylive's 2024 research found high correlations among major U.S. index products and positive correlation among options-strategy P/L across those products.

Therefore:

- SPY + QQQ should not automatically count as two independent risk buckets;
- IWM + SPY + QQQ can still create concentrated equity-beta exposure;
- implied-volatility correlation should be considered separately from price correlation where data permits.

The previously documented -0.5 to +0.5 correlation range is retained as a **research threshold**, not yet a frozen production rule.

## 7. Tail-risk / maximum-loss exposure

For defined-risk positions, track:

- maximum theoretical loss;
- maximum loss as % of NLV;
- aggregate defined-risk maximum loss;
- expiration/event concentration.

For undefined-risk positions, maximum theoretical loss is not useful as a sizing metric because it can be extremely large. Instead track:

- BPR;
- BPR expansion;
- notional/unit exposure;
- beta-weighted Delta;
- stress scenarios;
- concentration.

## 8. VIX is an allocation input, not a risk score

The historical VIX framework increases maximum BP allocation as VIX rises.

That should not be interpreted as higher VIX meaning lower risk.

For the modern system:

**VIX → allocation ceiling**

while:

**BPR + BPR expansion + Delta + notional + correlation + stress → actual risk controls**

## 9. Proposed risk-engine ordering

The deterministic engine should evaluate a new trade in this order:

1. Account emergency controls
2. Assignment/expiration restrictions
3. VIX-derived aggregate BP ceiling
4. 75/25 strategy sleeve
5. NLV individual-trade sizing
6. 15% underlying concentration
7. Current and projected BPR
8. BPR expansion stress
9. Beta-weighted Delta
10. Unit/notional exposure
11. Correlation/concentration
12. Defined-risk maximum loss
13. Liquidity/execution constraints
14. AI opportunity score

A trade is rejected if any hard constraint fails.

## 10. Small-account implication

The $2,000 account makes dynamic BPR particularly important.

A position that looks compliant at entry can become disproportionately large if BPR expands.

Therefore the bot should simulate or stress-test projected BPR before entry and continuously monitor actual BPR after entry.

The project should not solve this by simply increasing the allowed allocation percentage.

## 11. Research experiments

At minimum test:

- entry BPR vs. peak BPR;
- BPR expansion distribution by delta;
- BPR expansion by VIX/IVR regime;
- BPR expansion by underlying price;
- BPR expansion for 16-delta vs. 20-delta vs. other candidate deltas;
- BPR concentration by underlying;
- beta-weighted Delta versus realized portfolio drawdown;
- notional exposure versus tail drawdown;
- correlation versus portfolio drawdown;
- combinations of these controls.

## Current conclusion

The modern risk engine should be **multi-dimensional**.

BPR is essential because it governs capital usage and can expand dramatically, but current tastylive research does not support treating BPR as a perfect proxy for realized loss. The safest architecture for our research system is therefore to preserve BPR, Delta, notional exposure, correlation, maximum loss, and stress testing as separate controls.
