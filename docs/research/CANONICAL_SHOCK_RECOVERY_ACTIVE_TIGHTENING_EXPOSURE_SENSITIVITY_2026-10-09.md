# Active-Tightening Overlay — Predeclared Partial-Exposure Sensitivity

**Date:** 2026-10-09 UTC  
**Status:** EXPLORATORY EXPOSURE SENSITIVITY; no candidate selected  
**Workflow:** [run 37886436961](https://github.com/eklu654/Trading-Bot/actions/runs/37886436961)  
**Artifact:** `canonical-shock-recovery-active-tightening-exposure-sensitivity`, ID 11596473497  
**Market-input SHA-256:** `e04023f3b4c0fc23be11842e9462727bbd5423c0107c56ddc5d6932081fbf89f`.

## Fixed rule; only exposure varies

The overlay state rule is frozen:
- Arm when QQQ adjusted close is below the existing 200-session SMA and the previous-session Fed lifecycle state is TIGHTENING_ACTIVE.
- Remain armed until QQQ closes at/above the 200-DMA.
- During the overlay, hold a predeclared fraction of TQQQ (0%, 25%, 50%, or 75%); remaining allocation is cash.
- The baseline shock/recovery rule independently overrides the overlay with 0% TQQQ when its own defensive state is active.
- Signal at close[t], execute at open[t+1], and assign overnight/intraday returns to the correct held position.

This is a four-level exposure sensitivity using the user's already-established 0/25/50/75% exposure tiers, not a search over DMA lengths or signal thresholds.

## Whole-period results

| Strategy | Ending balance | Difference vs baseline | CAGR | Max drawdown | Worst rolling 252-session return |
|---|---:|---:|---:|---:|---:|
| Baseline shock/recovery | $4,040,315 | — | 49.49% | -73.53% | -72.64% |
| Active overlay, 0% TQQQ | $3,674,918 | -9.04% | 48.64% | -57.34% | -47.11% |
| Active overlay, 25% TQQQ | $3,932,880 | -2.66% | 49.25% | -57.34% | -52.81% |
| Active overlay, 50% TQQQ | $4,087,451 | +1.17% | 49.59% | -61.19% | -59.88% |
| Active overlay, 75% TQQQ | $4,124,680 | +2.09% | 49.67% | -67.65% | -66.56% |
| TQQQ buy-and-hold | $2,094,669 | -48.16% | 43.70% | -81.66% | -81.04% |

Two candidates are worth keeping in the research comparison:
- **50% TQQQ during active-tightening/below-DMA:** ends about $47,136 above the baseline while reducing maximum drawdown by 12.35 percentage points and improving the worst rolling-year return by 12.76 points.
- **75% TQQQ during that state:** ends about $84,365 above the baseline while reducing maximum drawdown by 5.88 points and improving the worst rolling-year return by 6.08 points.

The 50% variant is the stronger drawdown/wealth compromise in this sample. The 75% variant is the more growth-oriented choice and has the highest ending balance in the predeclared family. Neither is selected or validated; the full period has already been inspected.

## Stress windows

Returns below are each portfolio's return from its own inherited start equity over the exact window. Drawdown is local to the window.

| Window | Baseline return | 25% TQQQ in overlay | 50% TQQQ in overlay | 75% TQQQ in overlay |
|---|---:|---:|---:|---:|
| 2010 slow correction | -7.39% | -7.39% | -7.39% | -7.39% |
| 2016 slow correction | -18.09% | -17.14% | -16.88% | -17.20% |
| 2018 Q4 bear through 2019-03-29 | +0.04% | -22.61% | -15.56% | -8.02% |
| COVID crash/rebound | +24.58% | +24.58% | +24.58% | +24.58% |
| 2022 tightening bear | -69.83% | -50.45% | -57.21% | -63.73% |

The state overlay does not change COVID or 2025 exposure because those episodes are classified as EASING, not TIGHTENING_ACTIVE. In 2022, it reduces the baseline's calendar-year loss substantially. The exposure fraction controls the strength of that protection.

The 2018 window is the key counterweight: the active state/200-DMA overlay enters during choppy crosses and misses recovery exposure. Partial exposure reduces that opportunity cost compared with 0% TQQQ, but it does not eliminate it.

## Transaction-cost sensitivity

The script charges costs proportional to the size of each exposure change.

| Cost per full exposure change | Baseline | 25% TQQQ in overlay | 50% TQQQ in overlay | 75% TQQQ in overlay |
|---|---:|---:|---:|---:|
| 0 bp | $4.040M | $3.933M | $4.087M | $4.125M |
| 10 bp | $3.964M | $3.819M | $3.983M | $4.033M |
| 25 bp | $3.853M | $3.653M | $3.830M | $3.899M |
| 50 bp | $3.673M | $3.392M | $3.588M | $3.685M |

The 75% variant remains slightly above the baseline even at 50 bp under this simplified model; the 50% variant falls modestly below the baseline at 25/50 bp. Neither estimate captures all real-world slippage, spreads, taxes, funding, market impact, or broker fills.

## Episode contribution diagnostic

Leave-one-overlay-episode-out counterfactuals explain the trade-off:
- The long 2022 defense episode from 2022-04-05 to 2023-01-25 was the largest positive contribution. At 0% overlay exposure, its conditional terminal contribution was about **+$1.50M**.
- The 2018-12-04 to 2019-02-04 episode was the largest negative contribution: about **-$794k** at 0% overlay exposure, because it kept the account out through part of the 2019 recovery after the baseline had re-entered.
- The 2019-02 and 2019-03 episodes were also negative. Several 2018 episodes fully overlapped baseline defense and therefore had zero incremental effect.

These are conditional one-episode counterfactuals and are **not additive**; each is calculated against the rest of the full candidate path.

## Current conclusion

The evidence no longer supports treating the active-tightening overlay as simply “bad” because its 0% variant loses wealth. Partial exposure materially changes the result. In this in-sample comparison, 50% and 75% overlay exposure both finish above the unchanged baseline while reducing the maximum drawdown; 50% offers more downside reduction, while 75% preserves more growth.

**Do not select a winner yet.** These variants were compared after the full history had been inspected, so this is development evidence only. Keep the baseline, 50%, and 75% candidates as a small comparison set. Next, diagnose the 2018 false-positive episode and establish a chronological validation protocol before any rule or exposure choice is promoted.

## Reproducibility

- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37886436961
- Script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_active_tightening_exposure_sensitivity.py
- Workflow definition: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-active-tightening-exposure-sensitivity.yml
- Candidate 2 baseline test: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CANONICAL_SHOCK_RECOVERY_ACTIVE_TIGHTENING_OVERLAY_RESULT_2026-10-09.md
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
