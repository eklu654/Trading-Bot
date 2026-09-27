# Decision Log

## 2026-09-27 — Repository established

**Decision:** Use `eklu654/Trading-Bot` as the authoritative project repository.

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

## 2026-09-27 — VIX allocation schedule remains unresolved

**Decision:** Do not encode an unverified numerical VIX-to-buying-power schedule as an official tastytrade rule.

A project-specific schedule may be tested later, but it must be explicitly labeled as such.
