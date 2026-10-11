# Defensive Research Gate Summary — 2026-10-11

## Executive decision
Keep the verified B0 and frozen family-rotation strategy as research controls. **None of the tested defensive overlays meets its preregistered risk/wealth criteria. Do not promote a candidate to paper or live trading, and do not broaden any of the rejected parameter searches.**

The goal is not to engineer around the 2000 crash specifically. Treat 2000 as one stress-test regime, with pre-inception results explicitly labeled synthetic daily-reset simulations; use actual TQQQ/SOXL history only from their real inception dates.

## TQQQ B0 branch

Canonical B0 was independently reconciled on the same frozen inputs (2010-02-11 through 2026-10-07; $5,000 initial balance). Its ending balance was about $4.04M and maximum drawdown about -73.53%.

| Experiment | Result | Decision |
|---|---|---|
| DMA partial exposure matrix | Lower drawdown came with excessive terminal-wealth loss | Reject the DMA overlay family |
| R1 immediate re-entry / R2 staged-reset / R2P staged-retain | None improved the risk/wealth trade-off | Reject |
| R3: +5% rebound plus close above 20-SMA for half exposure; +10% for full | About 7.1% less terminal wealth; slightly worse drawdown and worst 252-session return | Reject |
| R4: clustered shock gate | About 8.7% less terminal wealth; slightly worse drawdown | Reject |
| RB95/RB90 fixed exposure caps | RB95 lost about 20% terminal wealth for 2.2 points of drawdown improvement; RB90 lost about 37% for 4.6 points | Reject |

References:
- [B0 canonical/partial-DMA decision](B0_CANONICAL_DEFENSE_MATRIX_DECISION_2026-10-11.md)
- [R3 re-entry results](REENTRY_CONFIRMATION_R3_RESULTS_2026-10-11.md)
- [R4 shock-cluster results](SHOCK_CLUSTER_R4_RESULTS_2026-10-11.md)
- [Fixed risk-budget results](STRUCTURAL_RISK_BUDGET_RESULTS_2026-10-11.md)

## Multi-family rotation branch

Frozen control: DMA-250 eligible families, top two, 5-session cadence; SPXL/SPY, TQQQ/QQQ, SOXL/SOXX, UDOW/DIA, TNA/IWM; $5,000 initial capital; actual data 2010-03-12 through 2026-10-02 in performance reports.

| Experiment | 25 bps terminal equity | Full max DD | Decision |
|---|---:|---:|---|
| Frozen base rotation | $249,490 | -68.53% | Control; high drawdown remains unacceptable |
| Family-specific -4.5% shock / +10% recovery gate | $76,067 | -66.32% | Reject: only 2.2-point DD improvement, ~69.5% wealth loss |
| Gate plus scheduled replacement rotation | $125,965 | -66.32% | Reject: only 2.2-point DD improvement, ~49.5% wealth loss |
| Permanent SOXL 25% cap with replacement family | $183,713 | -63.92% | Reject: 4.61-point DD improvement, ~26.4% wealth loss; misses both preregistered gates |
| SOXL 25% cap only during SOXX 60-session drawdown stress (-15% entry / -10% exit) | $237,314 | -67.69% | Reject: preserves ~95% of wealth but improves DD by less than one point |

Corrected selector attribution shows the deepest drawdowns are multi-family events: SOXL was a large contributor, but SPXL, TQQQ and TNA also produced substantial losses in different episodes. The COVID crash caused a 65.5% drawdown in 16 sessions while the strategy held TQQQ/SOXL at 50% each. The slow DMA eligibility rule is not an account-level crash circuit breaker. Permanent caps miss too much upside; the stress-conditioned SOXL cap preserves upside but barely changes drawdown. See [frozen selector attribution audit](SELECTOR_ATTRIBUTION_AUDIT_RESULTS_2026-10-11.md). This is evidence against further tuning of these simple family gates, not proof that all risk controls are futile.

References:
- [Family-specific shock gate results and event attribution](FAMILY_SPECIFIC_SHOCK_GATE_RESULTS_2026-10-11.md)
- [Replacement rotation results](FAMILY_GATE_REPLACEMENT_ROTATION_RESULTS_2026-10-11.md)
- [Permanent SOXL cap results](SOXL_CONCENTRATION_CAP_RESULTS_2026-10-11.md)
- [Stress-conditioned SOXL cap results](SOXL_STRESS_CONDITIONED_CAP_RESULTS_2026-10-11.md)

## What to do next
1. Freeze the rejected rules and stop threshold sweeps.
2. Selector attribution is complete: the 250-DMA filter does not prevent fast crashes, leveraged family losses are multi-family, and strong recovery participation is important. Do not tune DMA/top-N/cadence or the rejected family gates from this audit.
3. Existing volatility-targeting evidence has been recovered from the main README and the $5,000 account replay. The V30/L20/DD20–30 cluster reduced drawdown to roughly 39–48% but ended around $23k–$34k at 25 bps, versus roughly $177k next-open / $228k prior-close for the raw family rotation. Do not rerun or broaden that matrix; this is an established wealth-versus-drawdown tradeoff.
4. A separately preregistered synthetic daily-reset family-rotation stress study is now running for the 2000–2002 technology bear. It uses SPY, QQQ, ^SOX, DIA, and ^RUT benchmark history and explicitly models 3x daily reset, funding drag, and a fixed fee. It is not actual TQQQ/SOXL/SPXL history and must not be used to tune parameters to 2000–2002.
5. Keep live/paper trading downstream of data validation, execution realism, walk-forward stability, and a defensible account-level risk limit.

## Audit trail
All runs and artifacts are linked from the individual reports above. The corrected R4 run explicitly supersedes its invalid preliminary implementation; the corrected family shock-gate workflow builds/restores the historical dataset before execution; the final SOXL cap runs passed their unit tests and accounting invariants.
