# Decision Log

## 2026-09-27 — Repository established

**Decision:** Use the Trading-Bot repository as the authoritative project repository.

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

**Decision:** Treat the following as verified historical tastytrade methodology for research purposes, based on the primary-source From Strategy to Practice — India 2020 presentation:

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

The user's screenshot is preserved as Screenshot_20210413-175727.png.

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

## 2026-09-28 — Small-account feasibility and risk-model refinement

The options research now treats account size as an explicit feasibility variable rather than assuming the historical portfolio framework scales linearly to $2,000.

Current tastylive research documents substantial BPR expansion risk for naked positions in small accounts and discusses risk-defined structures as a practical response to small-account constraints. The project therefore will test historical-mix and defined-risk feasibility models separately rather than silently relaxing sizing rules.

Beta-weighted Delta will remain a monitored directional metric but will not receive a frozen numerical neutrality band until stronger quantitative evidence is recovered. Recent tastylive material also emphasizes gamma and correlation behavior during volatility spikes.

Undefined-risk defense methods will be tested comparatively rather than hard-coded from a single educational example.

See docs/02-research/small-account-options-feasibility.md.

## 2026-09-28 — Underlying-universe research

The options strategy will begin research with a deliberately small candidate universe: SPY, QQQ, IWM, GLD, TLT and SLV. This is a research universe based on historical tastylive study precedent, liquidity considerations, and the need to avoid prematurely introducing individual-company event risk.

The list is not a permanent production whitelist. Quantitative liquidity, capital-efficiency, event-risk and correlation filters must determine actual eligibility.

See docs/02-research/options-underlying-universe.md.

## 2026-09-28 — Historical regime classifier is not frozen

**Decision:** Reject the current regime classifier as a production candidate.

The 2010–2026 historical dataset contains 4,208 sessions. The current classifier labels approximately 91.6% of sessions as options-eligible, which conflicts with the architecture that expects ETF-001 to remain the default for most normal conditions.

The ETF-001 backtest also does not support treating all current sideways/choppy sessions as ETF-failure periods. Under the current labels, sideways/choppy periods had positive aggregate historical return but a large within-regime drawdown, while turbulent/high-volatility periods showed materially weaker results in the validation and holdout splits for the stricter candidate definitions.

Candidate testing produced a useful research range:

- stricter volatility candidates: approximately 18–28% options-eligible depending on the chronological split;
- broader sideways candidate: approximately 23% eligible over the full 2010–2026 sample;
- turbulent-only candidate: approximately 10% eligible.

None is frozen yet. The next decision depends on historical OPTIONS-001 replay rather than further indicator accumulation.

See docs/02-research/historical-regime-validation.md.

## 2026-09-28 — Historical options replay source

**Decision:** Use the public SPY 2008–2025 end-of-day options-chain dataset as the first research replay source, without committing the raw data to this repository.

The replay must test bid/ask-conservative and midpoint-sensitive execution assumptions and preserve source/version provenance.

Cboe DataShop remains the higher-fidelity reference source if the public dataset fails quality or coverage requirements.

See docs/02-research/options-historical-data.md.

## 2026-09-28 — First historical OPTIONS-001 replay

**Decision:** Do not combine SIDEWAYS_CHOPPY and TURBULENT_HIGH_VOL into a single options-entry regime based on the first replay.

The 2010–2025 SPY replay of a 45-DTE, approximately 16-delta short strangle, one position at a time, produced:

- conservative bid/ask: 114 trades, -$2,206 total P/L, 69.3% winners;
- midpoint sensitivity: 114 trades, -$551 total P/L, 72.8% winners.

The regime split was materially different:

- SIDEWAYS_CHOPPY: +$2,173 conservative / +$2,372 midpoint;
- TURBULENT_HIGH_VOL: -$4,379 conservative / -$2,923 midpoint.

This is preliminary because the replay currently uses a temporary 2×-credit loss threshold and does not implement the documented defensive roll/untested-side/inversion mechanics.

**Next:** test defense variants and $2,000 account feasibility before modifying SWITCH-001 regime thresholds further.


## 2026-09-28 — No-stop OPTIONS-001 benchmark

**Decision:** Retire the 2×-initial-credit loss threshold as a candidate production rule.

With the same 45-DTE / approximately 16-delta SPY short-strangle construction and BROAD_SIDEWAYS entry gate, removing the temporary loss threshold changed results from negative to positive:

- conservative bid/ask: 103 trades, +$4,557 total P/L, 72.8% winners;
- midpoint: 106 trades, +$5,266 total P/L, 75.5% winners.

TURBULENT_HIGH_VOL was positive under both no-stop fill models (+$2,068 conservative; +$2,446 midpoint). Therefore the first replay's turbulent-period losses cannot be treated as evidence against turbulent options entries; they were strongly affected by the arbitrary 2×-credit stop.

**Next:** implement deterministic challenge-management research variants rather than adding more regime indicators. Compare no adjustment, untested-side roll, roll-out, and inversion using only EOD chain information available after each entry. Do not freeze any defense rule or regime gate until the defense comparison and $2,000 feasibility analysis are complete.


## 2026-09-28 — Initial options structure research scope

**Decision:** Limit the first structure comparison to short strangles, iron condors, and directional credit verticals. Treat this as a research scope decision, not production approval.

Short strangles and iron condors form the neutral short-premium comparison; credit verticals remain a separate directional family and must not be treated as delta-neutral substitutes. Defer straddles, iron butterflies, broken-wing butterflies, ratio spreads, diagonals/calendars and hybrid structures until the core comparisons and $2,000 feasibility analysis justify expanding scope.

No structure may bypass hard sizing, buying-power, concentration, liquidity, stress, or expiration constraints to make it feasible for the small account. Rejected opportunities must be recorded as part of feasibility results.

See docs/02-research/options-structure-universe.md.


## 2026-09-28 — Historical run 46 results superseded

The OPTIONS-001 figures from run 46 are invalidated by an expiration-selection defect. Do not use those figures. The defect was corrected in commit 087539ffc4ff4fb24e0d715d5bacdf1e6fa2d0a6, and corrected run 48 completed successfully.

## 2026-09-28 — Corrected historical OPTIONS-001 replay (run 48)

**Decision:** Use run 48 as the current corrected replay reference, while retaining its exploratory status.

The corrected SPY BROAD_SIDEWAYS short-strangle comparison reports:
- Conservative fills: no adjustment +$5,885 across 96 trades; roll untested +$4,108 across 96.
- Midpoint fills: no adjustment +$7,211 across 98 trades; roll untested +$6,343 across 98.
- Rolling the untested side reduced aggregate P/L in both fill models and did not materially improve the worst trade. Do not promote this defense on current evidence.

A ledger audit found no call/put expiration inconsistencies in the baseline and 2×-loss-stop outputs. Adjustment cash-flow accounting and the max-debit risk proxy remain unresolved audit items.

The replay is not a $2,000 account simulation; do not interpret its cumulative dollar P/L as account return. The ETF VIX-overlay comparison remains exploratory and did not improve the reported return or maximum drawdown in the tested implementation.

See docs/02-research/historical-run-46-results.md and https://github.com/eklu654/Trading-Bot/actions/runs/36481614364.
