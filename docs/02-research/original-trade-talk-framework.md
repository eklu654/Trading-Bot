# Historical Portfolio Framework — Source Provenance

**Status:** Primary-source provenance record  
**Last reviewed:** 2026-09-27

## Primary source

**Presentation:** *From Strategy to Practice — India 2020*  
**Presenter:** Tom Sosnoff / tastytrade  
**Format:** PDF presentation  
**Primary-source URL:**  
https://s3.amazonaws.com/tastytradepublicmedia/website/cms/tastytrade_TomSosnoff_India2020.pdf/original/tastytrade_TomSosnoff_India2020.pdf

The relevant material appears in the presentation's **Trade Small / Trade Often** section.

## Relevant slides

### Slide 34 — Individual sizing and VIX framework

The presentation states:

- market volatility determines the percentage of capital used;
- individual trade sizing is a percentage of net liquidation value;
- no more than 15% of net liq in any single underlying;
- undefined risk: 3–7%;
- defined risk: 1–3%.

### Slide 35 — VIX allocation

The presentation states:

| VIX | Maximum allocation of BP |
|---|---:|
| 10–15 | 25% |
| 15–20 | 30% |
| 20–30 | 35% |
| 30–40 | 40% |
| >40 | 50% |

### Slide 36 — Strategy-type allocation

The presentation states:

- 75% allocated to undefined-risk strategies;
- no more than 3–7% per undefined-risk trade;
- examples: straddles and strangles;
- 25% allocated to defined-risk strategies;
- no more than 1–5% per defined-risk trade on the slide.

### Important discrepancy to preserve

Slide 34 gives **defined risk: 1–3%**, while slide 36's parenthetical says **no more than 1–5% per trade**.

This is a real source inconsistency and must not be silently resolved.

For the project's primary historical baseline, use the more specific slide-34 individual-sizing statement:

**Defined risk = 1–3% of net liq**

and preserve the slide-36 **1–5%** figure as a historical variant requiring investigation.

For undefined risk, both slides use **3–7%**.

## VIX >40 vs. VIX >50 discrepancy

Some secondary/community references report the highest band as VIX >50. The recovered primary-source presentation explicitly says:

**VIX greater than 40 → 50% maximum allocation of BP.**

The project therefore records **>40** as authoritative for this historical presentation.

The user's screenshot also shows >40. **Screenshot_20210413-175727.png**. fileciteturn2file0

## Nested interpretation

The slides place the VIX maximum-BP table directly before the 75/25 strategy allocation slide, inside the same Trade Small / Trade Often section.

The project's historical reconstruction therefore models:

**Account → VIX BP ceiling → 75/25 strategy-type allocation → individual trade sizing → 15% single-underlying concentration**

This is a reconstruction of the presentation's portfolio framework, not a claim about a current universal 2026 tastytrade policy.

## Why this source matters

Earlier project drafts had three unresolved questions:

1. whether the VIX table was real;
2. whether 75/25 sat inside the VIX ceiling;
3. what the individual trade-size ranges actually were.

The primary presentation resolves the first two sufficiently for a historical research model and supplies direct evidence for the third.

The remaining production questions concern adaptation to the bot's $2,000 account and current broker/risk mechanics.

## Related primary/official context

tastylive identifies *How to build a portfolio using complex options strategies* as one of its major educational portfolio videos:
https://www.tastylive.com/news-insights/watch-these-top-10-youtube-videos-to-master-options-trading

A 2019 tastylive Reserve Capital episode provides an earlier version of the framework:

- 75% undefined risk;
- 25% defined risk;
- 3–5% undefined per trade;
- 0.5–2% defined per trade;
- increase allocation as VIX rises.

That earlier version should be treated as a historical variant rather than mixed with the 2020 presentation without labeling.

## Research rule

When a historical source and a later/current source differ:

1. preserve both;
2. identify the date;
3. do not silently merge them;
4. test them as separate variants;
5. prefer current primary-source guidance for a production rule once current applicability is established.
