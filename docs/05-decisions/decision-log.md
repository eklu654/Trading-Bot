# Decision Log

## 2026-09-27 — Repository established

**Decision:** Use \`eklu654/Trading-Bot\` as the authoritative project repository.

## 2026-09-27 — Three isolated strategy instances

**Decision:** Use one codebase with three isolated portfolio/account instances.

- ETF-001 — $2,000 initial paper account
- OPTIONS-001 — $2,000 initial paper account
- SWITCH-001 — $2,000 initial paper account

All instances receive the same market data but maintain independent state.

## 2026-09-27 — Regime changes do not force-close options

**Decision:** Existing options positions remain governed by the options strategy's own exit rules when the regime changes.

The regime switcher controls eligibility for new positions rather than acting as a discretionary liquidation engine.

## 2026-09-27 — AI cannot override hard risk rules

**Decision:** AI-generated signals may propose regimes and opportunities, but the deterministic risk engine has final authority.

## 2026-09-27 — Historical VIX/portfolio framework reconstructed

**Decision:** Treat the following as verified historical tastytrade methodology for research purposes, based on the primary-source **From Strategy to Practice — India 2020** presentation:

- VIX 10–15 → 25% maximum BP allocation
- VIX 15–20 → 30%
- VIX 20–30 → 35%
- VIX 30–40 → 40%
- VIX >40 → 50%
- 75% of the allocated options sleeve → undefined-risk strategies
- 25% → defined-risk strategies
- undefined-risk individual trade sizing → 3–7% of net liq
- defined-risk individual trade sizing → 1–3% of net liq
- maximum 15% of net liq in any single underlying

Primary-source presentation:
https://s3.amazonaws.com/tastytradepublicmedia/website/cms/tastytrade_TomSosnoff_India2020.pdf/original/tastytrade_TomSosnoff_India2020.pdf

The user's screenshot is preserved as **Screenshot_20210413-175727.png**. fileciteturn2file0

**Important:** These are classified as historical documented methodology, not as a claim that tastytrade currently requires these exact figures in 2026.

## 2026-09-27 — Historical framework is not yet the production specification

**Decision:** Do not freeze the historical methodology directly into production code yet.

Before implementation, test:

- broker-specific BPR behavior;
- $2,000 contract granularity;
- current/recent tastylive risk guidance;
- beta-weighted Delta limits;
- notional/unit exposure;
- correlation;
- assignment/expiration risk;
- and realistic option execution costs.

The historical framework becomes the baseline research model against which modern adaptations are compared.
