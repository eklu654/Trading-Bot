# VIX and Buying-Power Allocation Research

**Status:** Historical framework reconstructed from primary source; current production adaptation still requires validation  
**Last reviewed:** 2026-09-27

## 1. Primary-source evidence

The project now has both direct screenshot evidence and a recovered primary-source presentation.

The presentation is **From Strategy to Practice — India 2020** by Tom Sosnoff.

Primary-source PDF:
https://s3.amazonaws.com/tastytradepublicmedia/website/cms/tastytrade_TomSosnoff_India2020.pdf/original/tastytrade_TomSosnoff_India2020.pdf

The user's screenshot is **Screenshot_20210413-175727.png**. fileciteturn2file0

The recovered presentation explicitly gives:

| VIX | Maximum allocation of BP |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| >40 | 50% |

This resolves the previous uncertainty over whether the top band was >40 or >50: the primary presentation says **greater than 40**.

## 2. What the VIX percentage actually measures

The presentation labels these figures **maximum allocation of BP**.

Therefore:

- it is an aggregate portfolio buying-power ceiling;
- it is not an individual trade size;
- it is not a requirement to deploy the maximum;
- it is not the same denominator as individual trade sizing.

Individual trade sizing on the same presentation is expressed as a percentage of **net liquidation value**.

The bot must preserve this distinction.

## 3. Nested 75/25 strategy allocation

The presentation follows the VIX framework with:

- **75% allocated to undefined-risk strategies**
- **25% allocated to defined-risk strategies**

It gives examples:

### Undefined risk
- straddles in higher IV Rank;
- strangles in lower IV Rank.

### Defined risk
- iron condors;
- debit and credit spreads.

For the historical framework reconstruction, model this as a composition of the VIX-limited options sleeve:

**Account → VIX BP ceiling → 75/25 strategy-type budgets → individual trade sizing**

This is the most coherent reading of the presentation because the rules appear together in the same “Trade Small / Trade Often” section.

## 4. Individual trade sizing in the same framework

The presentation states:

- undefined risk: **3–7% of net liq per trade**;
- defined risk: **1–3% of net liq per trade**;
- no more than **15% of net liq in any single underlying**.

This is important because our previous draft treated 5–7% as a project-only small-account exception.

The historical source itself supports 3–7% for undefined-risk trades.

The project should still separately test whether these percentages are executable in a $2,000 account.

## 5. $2,000 translation

| VIX | Max BP allocation | $2,000 equivalent |
|---|---:|---:|
| 10–15 | 25% | $500 |
| 15–20 | 30% | $600 |
| 20–30 | 35% | $700 |
| 30–40 | 40% | $800 |
| >40 | 50% | $1,000 |

Individual historical sizing:

| Structure | Net-liq range | $2,000 equivalent |
|---|---:|---:|
| Undefined risk | 3–7% | $60–$140 |
| Defined risk | 1–3% | $20–$60 |

Underlying concentration:

**15% × $2,000 = $300 maximum per underlying** under the historical framework.

These are translations, not deployment instructions.

## 6. Historical vs. current guidance

The 2020 presentation is strong primary-source evidence for the historical framework.

It should not automatically be treated as a universal current 2026 rule.

Newer tastylive material uses additional risk framing. For example, a 2024 portfolio-risk article describes prudent capital allocation in a 25%–50% range with a 75% maximum cap and warns that BPR can expand during market stress.

Therefore the bot should preserve the historical framework as a reproducible research model and test modern risk overlays separately.

## 7. Why high VIX does not mean “safe”

The VIX schedule increases the maximum permitted BP allocation as volatility rises. That does **not** mean higher VIX is lower risk.

Higher volatility can increase:

- option premium;
- BPR;
- position Delta changes;
- correlation;
- drawdown magnitude;
- assignment/adjustment pressure.

The project must therefore treat the VIX table as a capital-allocation framework, not as a risk score.

## 8. Constraint hierarchy

For the historical model:

1. account-level emergency controls;
2. assignment/expiration safeguards;
3. VIX-derived aggregate BP ceiling;
4. 75/25 undefined/defined allocation;
5. 3–7% / 1–3% individual trade sizing;
6. 15% underlying concentration;
7. beta-weighted Delta;
8. correlation/stress controls;
9. liquidity/entry criteria.

The most restrictive applicable constraint wins.

## 9. Research matrix

### Historical framework

- VIX 25/30/35/40/50 schedule;
- nested 75/25 strategy allocation;
- 3–7% undefined-risk trades;
- 1–3% defined-risk trades;
- 15% per-underlying net-liq concentration.

### Historical variant

Compare against the 2019 Reserve Capital ranges:

- undefined: 3–5%;
- defined: 0.5–2%.

### Modern overlay

Test:

- BPR expansion;
- beta-weighted Delta;
- notional/unit exposure;
- correlation;
- drawdown;
- realized volatility;
- IVR;
- assignment risk.

### Account-size study

Test $2,000, $5,000, $10,000, and larger accounts.

Measure the percentage of eligible trades that are rejected solely because contract granularity prevents compliance with the historical framework.

## Current conclusion

The VIX table is no longer an unsupported project hypothesis.

More importantly, the surrounding primary-source presentation establishes a coherent historical structure:

**VIX maximum BP allocation → 75/25 strategy mix → individual trade sizing → 15% single-underlying concentration.**

The remaining work is to determine how much of this historical framework should become the modern bot's production specification and how to handle the severe contract-granularity constraints of the $2,000 paper account.
