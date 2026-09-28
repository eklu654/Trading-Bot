# Options Portfolio Allocation Methodology Research

**Status:** Research reconciliation — historical framework reconstructed; production rules not yet frozen  
**Last reviewed:** 2026-09-28

## Purpose

This document reconciles the tastytrade/tastylive evidence for:

- VIX-based aggregate allocation;
- undefined-risk vs. defined-risk allocation;
- individual trade sizing;
- per-underlying concentration;
- beta-weighted Delta;
- diversification/correlation;
- and reserve capital.

The key question is no longer whether the historical VIX table exists. The primary-source presentation has now been recovered, and it shows the surrounding portfolio-construction rules on adjacent slides.

## 1. Recovered primary-source presentation

A primary-source tastytrade presentation titled **From Strategy to Practice — India 2020**, presented by Tom Sosnoff, contains the relevant slides.

The presentation explicitly states:

- market volatility determines the percentage of capital used;
- individual trade sizing is expressed as a percentage of **net liquidation value**;
- no more than **15% of net liq in any single underlying**;
- undefined-risk trade sizing: **3–7%**;
- defined-risk trade sizing: **1–3%**;
- VIX-based maximum allocation of buying power;
- 75% allocation to undefined-risk strategies;
- 25% allocation to defined-risk strategies.

Primary-source PDF:
https://s3.amazonaws.com/tastytradepublicmedia/website/cms/tastytrade_TomSosnoff_India2020.pdf/original/tastytrade_TomSosnoff_India2020.pdf

tastylive also identifies *How to Build a Portfolio Using Complex Options Strategies* as a major Tom Sosnoff portfolio-building presentation:
https://www.tastylive.com/news-insights/watch-these-top-10-youtube-videos-to-master-options-trading

The user's screenshot independently preserves the same VIX table. **Screenshot_20210413-175727.png**. fileciteturn2file0

## 2. VIX-based aggregate allocation

The recovered presentation gives:

| VIX | Maximum allocation of BP |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| >40 | 50% |

This resolves the earlier ambiguity around the exact historical table. The official presentation says **VIX greater than 40 → 50% maximum allocation of BP**.

The table is historical documented guidance. It is not automatically a current universal 2026 tastytrade requirement.

### Critical metric distinction

The presentation uses **maximum allocation of BP** for the VIX table, while it separately describes individual trade sizing as a percentage of **net liq**.

The bot must therefore not treat these as the same metric.

## 3. Nested portfolio structure

The slide sequence now provides strong evidence for a nested model:

**VIX → maximum total options buying-power allocation → strategy-type allocation → individual trade sizing → underlying concentration**

The presentation first states that market volatility determines the percentage of capital used and then gives the VIX maximum-BP table. The following slide allocates the resulting options portfolio:

- **75% undefined-risk strategies**
- **25% defined-risk strategies**

This is materially stronger evidence than our previous inference that the 75/25 split might be independent of the VIX ceiling.

### Project interpretation

For the historical framework reconstruction, model the 75/25 split **inside the VIX-derived aggregate options allocation** unless a later primary source contradicts it.

Example at VIX 20–30:

- maximum options BP allocation = 35% of account BP;
- of that allocated options sleeve, target composition = 75% undefined / 25% defined;
- individual trades remain subject to their own sizing and concentration limits.

This is a reconstruction of the historical framework, not yet a frozen production rule.

## 4. Individual trade sizing

The recovered presentation gives:

| Structure | Historical individual trade size |
|---|---:|
| Undefined risk | 3–7% of net liq |
| Defined risk | 1–3% of net liq |

The same slide states:

**No more than 15% of net liq in any single underlying.**

This is important because our previous project draft incorrectly framed 5–7% as merely a project-specific small-account exception.

### Corrected interpretation

The **3–7% undefined-risk** and **1–3% defined-risk** ranges are directly documented historical presentation guidance.

However, they remain historical methodology inputs rather than automatically current production limits.

The project's $2,000 account still requires contract-granularity testing.

## 5. $2,000 account translation

For a $2,000 account:

### VIX allocation ceiling

| VIX | Max BP allocation | Dollar equivalent |
|---|---:|---:|
| 10–15 | 25% | $500 |
| 15–20 | 30% | $600 |
| 20–30 | 35% | $700 |
| 30–40 | 40% | $800 |
| >40 | 50% | $1,000 |

### Historical individual trade ranges

| Structure | Percentage of net liq | $2,000 equivalent |
|---|---:|---:|
| Undefined risk | 3–7% | $60–$140 |
| Defined risk | 1–3% | $20–$60 |

### Underlying concentration

15% of $2,000 = **$300 maximum net-liq sizing per underlying** under the historical presentation framework.

These dollar figures are translations of the historical percentages, not recommendations to deploy those amounts.

## 6. Allocation is a ceiling, not a deployment target

A VIX allocation ceiling does not mean:

> At VIX 25, deploy exactly 35%.

It means:

> Under the historical framework, total options BP allocation may be as high as 35%, subject to the other portfolio constraints.

The bot must be able to remain below the ceiling because:

- no eligible trade exists;
- a trade would violate the 75/25 sleeve budget;
- a trade would breach the per-trade limit;
- an underlying would exceed the 15% concentration cap;
- portfolio Delta would become excessive;
- correlation would become excessive;
- BPR stress would become unacceptable; or
- another hard account safeguard would block the trade.

## 7. Risk metrics are not interchangeable

The research now clearly separates:

### Buying Power / BPR

Measures capital required by the broker to support the position. This is the metric used by the historical VIX allocation table.

### Net Liquidation Value

The denominator explicitly used by the presentation for individual trade sizing and the 15% single-underlying limit.

### Beta-weighted Delta

Measures standardized directional exposure, with SPY as the benchmark in tastylive methodology. It is useful for portfolio neutrality but is not a complete tail-risk metric.

### Unit / notional exposure

Measures the scale of underlying exposure. tastylive research has shown that notional exposure can be more conservative for outlier-risk assessment than beta-weighted Delta alone.

### Correlation / concentration

Measures whether apparently separate positions are actually exposed to the same underlying risk factors.

The risk engine must keep these metrics separate.

## 8. Relationship to older 2019 guidance

A 2019 tastylive Reserve Capital episode described:

- 75% BP to undefined-risk strategies;
- 25% BP to defined-risk strategies;
- 3–5% per undefined-risk trade;
- 0.5–2% per defined-risk trade;
- increased allocation as VIX rises.

The recovered 2020 presentation updates the individual sizing ranges to **3–7% undefined** and **1–3% defined**, while retaining the 75/25 framework and VIX scaling.

For this project, the 2020 primary-source presentation is the stronger historical reference for the reconstructed framework because it contains all of these rules together.

We should not mix the 2019 per-trade ranges with the 2020 ranges unless explicitly testing historical variants.

## 9. Current/recent risk-management context

Newer tastylive material does not simply reproduce the 2020 table as a timeless rule. A 2024 portfolio-risk article discusses prudent capital allocation in a 25%–50% range with a 75% maximum cap and warns that BPR can expand under market stress.

That newer material should be treated as a risk-control overlay when designing the modern bot rather than silently replacing the historical methodology.

## 10. New 2024–2025 risk-management reconciliation

Recent tastylive research sharpens the role of BPR rather than replacing the historical VIX framework.

A 2024 study found that higher BPR does not automatically mean higher realized risk when comparing strangles and iron condors. However, a 2025 study describes BPR as a useful risk gauge for undefined-risk positions and documents large BPR expansion after adverse price/volatility moves. citeturn0search6turn0search5

The correct reconciliation is:

- **BPR is a hard capital-usage constraint.**
- **BPR expansion is a dynamic stress signal.**
- **BPR is not, by itself, a maximum-loss estimate.**
- **Delta, notional exposure, correlation, and stress testing remain separate controls.**

The 2025 small-account research is particularly relevant to the $2,000 project account: it documents examples of BPR increasing by more than 200%, with a worst-case example reaching 3.6× initial BPR. citeturn0search0

## 11. Preliminary deterministic hierarchy

For the reconstructed historical model:

1. Account-level emergency/loss controls
2. Assignment/expiration safeguards
3. VIX-derived aggregate BP ceiling
4. 75/25 undefined/defined portfolio sleeve budget
5. Individual trade net-liq sizing limit
6. 15% per-underlying concentration limit
7. Portfolio beta-weighted Delta limits
8. Correlation/concentration stress limits
9. Entry-quality/liquidity rules
10. AI opportunity ranking

The exact numerical Delta, correlation, and stress thresholds remain unresolved.

## 12. $2,000 account problem

The historical framework was not designed specifically around a $2,000 account.

At this account size:

- a single contract can exceed the intended percentage range;
- undefined-risk positions can consume disproportionate BPR;
- defined-risk spreads can have minimum risk increments that are too large;
- exact 75/25 allocation may be impossible;
- exact Delta neutrality may be impossible;
- diversification may be severely constrained.

Therefore the bot must report **constraint infeasibility** rather than silently relaxing the methodology.

The small-account question becomes an explicit experiment:

> What is the smallest account size at which the historical framework can be executed without systematically violating its own sizing and diversification constraints?

## 13. Research experiments

The next backtesting matrix should include:

### Historical framework

- VIX 25/30/35/40/50 BP ceiling;
- nested 75/25 strategy allocation;
- 3–7% undefined-risk trade size;
- 1–3% defined-risk trade size;
- 15% maximum net-liq concentration per underlying.

### Historical variants

- 2019 per-trade ranges: 3–5% undefined / 0.5–2% defined;
- 2020 ranges: 3–7% undefined / 1–3% defined.

### Modern risk overlays

- aggregate BPR stress;
- beta-weighted Delta;
- correlation;
- notional/unit exposure;
- drawdown;
- volatility regime.

### Small-account tests

Test $2,000, $5,000, $10,000, and larger accounts to determine where contract granularity stops dominating the framework.


## 14. Current conclusion

We have now reconstructed the most important missing relationship:

**The historical VIX schedule, 75/25 strategy mix, individual trade sizing, and 15% underlying concentration limit appear together in the same primary-source portfolio presentation.**

That substantially reduces the ambiguity in the portfolio architecture.

What remains unresolved is not the historical framework itself, but whether and how that historical framework should be adapted for the bot's $2,000 paper account and current market/broker mechanics.
