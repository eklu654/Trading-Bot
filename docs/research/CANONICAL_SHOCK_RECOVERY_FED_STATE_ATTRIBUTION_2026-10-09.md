# Fed Lifecycle Attribution Around Canonical Baseline Drawdowns — 2026-10-09

**Status:** Diagnostic-only, completed successfully  
**Workflow:** [run 37885615208](https://github.com/eklu654/Trading-Bot/actions/runs/37885615208)  
**Artifact:** `canonical-shock-recovery-fed-state-attribution`, ID 11595504634  
**Input SHA-256:** `b3a52cf47af93a200abf0b79efe37007d8ec6c591aae48b1cd759df8fff9bbf5`  
**Scope:** Actual TQQQ window 2010-02-11 through 2026-10-07; Fed state is lagged one QQQ session. No candidate strategy is evaluated in this report.

## Frozen definitions

- Drawdown episode starts when QQQ adjusted close is at least 5% below its rolling 252-session high.
- The episode ends when QQQ recovers to 95% of the reference peak established at episode entry.
- Only episodes reaching at least -15% from that reference peak are included.
- Baseline shock is QQQ adjusted-close daily return <= -4.5%; baseline recovery is a close >=10% above the post-shock low.
- Fed lifecycle states use the existing target-rate classification, conservatively lagged one market session for this diagnostic.

## Episode attribution

| Episode | QQQ max drawdown | First daily shock | Delay from episode start | Fed state at start | Fed state at trough | Sessions both below 200-DMA and Fed-paused |
|---|---:|---|---:|---|---|---:|
| 2010 correction | -15.6% | None | None | NEUTRAL | NEUTRAL | 0 |
| 2011 selloff | -16.1% | 2011-08-04 | 0 | NEUTRAL | NEUTRAL | 0 |
| Early 2016 correction | -16.1% | None | None | TIGHTENING_ACTIVE | TIGHTENING_ACTIVE | 1 |
| 2018 bear | -22.8% | 2018-10-24 | 4 | TIGHTENING_ACTIVE | TIGHTENING_ACTIVE | 0 |
| COVID crash | -28.6% | 2020-02-27 | 3 | EASING | EASING | 0 |
| 2022 tightening bear | -35.1% | 2022-05-05 | 77 | NEUTRAL | TIGHTENING_ACTIVE | 0 |
| 2025 correction | -22.8% | 2025-04-03 | 25 | EASING | EASING | 0 |

## What the state chronology tells us

The state transitions in the frozen diagnostic are:
- 2015-12-17: TIGHTENING_ACTIVE
- 2016-03-16: TIGHTENING_PAUSED
- 2016-12-15: TIGHTENING_ACTIVE
- 2017–2019: repeated active/paused switches through successive hike and pause episodes
- 2021-03-17: NEUTRAL
- 2022-03-18: TIGHTENING_ACTIVE
- 2023-10-26: TIGHTENING_PAUSED
- 2024-07-30: NEUTRAL
- 2024-09-20: EASING

In the 2022 drawdown episode, QQQ crossed the -5% episode threshold on 2022-01-13 while the Fed state was NEUTRAL. The state became TIGHTENING_ACTIVE on 2022-03-18, and the first -4.5% daily QQQ shock did not occur until 2022-05-05. Thus an active-tightening × below-200-DMA hypothesis could have triggered before the baseline's May shock; a paused-only condition could not. The paused state did not begin until 2023-10-26, after QQQ had already recovered above its 200-DMA, explaining why the paused-only overlay never activated in 2022.

The same active state was present during early 2016 and 2018. Therefore the active-tightening hypothesis has a plausible opportunity to catch 2022 earlier, but it is not automatically a good rule: it risks false positives during earlier corrections, and needs a fixed-rule test against terminal wealth as well as stress-period results.

## Baseline event states

| Shock date | Fed state at shock (lagged) | QQQ below 200-DMA? | Fed state at recovery decision |
|---|---|---|---|
| 2011-08-04 | NEUTRAL | Yes | NEUTRAL |
| 2018-10-24 | TIGHTENING_ACTIVE | Yes | TIGHTENING_ACTIVE |
| 2020-02-27 | EASING | No | EASING |
| 2020-06-11 | EASING | No | EASING |
| 2020-09-03 | EASING | No | EASING |
| 2022-05-05 | TIGHTENING_ACTIVE | Yes | TIGHTENING_ACTIVE |
| 2022-09-13 | TIGHTENING_ACTIVE | Yes | TIGHTENING_ACTIVE |
| 2025-04-03 | EASING | Yes | EASING |
| 2026-06-05 | EASING | No | EASING |

## Decision and next experiment

1. The paused-only × below-200-DMA overlay has already been rejected: it reduced ending wealth by ~28% and did not reduce maximum drawdown.
2. The state attribution supplies a more specific, testable next hypothesis: **TIGHTENING_ACTIVE × below-200-DMA**, sticky until QQQ reclaims the 200-DMA, layered on top of the unchanged shock/recovery baseline.
3. Before running it, freeze that single rule and its exit condition. Compare it on the same common market data against the baseline and buy-and-hold, including 2016, 2018, COVID, 2022, and 2025. Do not tune the DMA or exposure from those outcomes.
4. If it reduces the 2022 loss but sacrifices more wealth in 2016/2018 or misses COVID's rebound, record that trade-off honestly; do not promote it based on drawdown alone.

## Reproducibility

- Diagnostic workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37885615208
- Script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_fed_state_attribution.py
- Workflow: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-fed-state-attribution.yml
- Baseline stress audit: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CANONICAL_SHOCK_RECOVERY_STRESS_WINDOWS_AND_SLOW_BEAR_AUDIT_2026-10-09.md
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
