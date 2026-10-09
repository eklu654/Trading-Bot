# Historical Signal-Only Stress Audit — 1970s, 1987, Dot-Com, and GFC

**Date:** 2026-10-09 UTC  
**Status:** SIGNAL-ONLY DIAGNOSTIC; no TQQQ wealth claims for pre-2010 periods  
**Workflow:** [run 37887083424](https://github.com/eklu654/Trading-Bot/actions/runs/37887083424)  
**Artifact:** `canonical-shock-recovery-historical-signal-audit`, ID 11596921774  
**QQQ + lagged-state input SHA-256:** `160cf804e17fbe47801cabfab64fef0fb05dfb4e81c1132d1d4d5cad8c4d0eb7`.

## Scope and guardrails

This is not a TQQQ backtest. TQQQ did not exist before 2010. The study measures only signal timing and index behavior:
- S&P 500 broad-market proxy from 1970-01-02 through 1999-03-09;
- QQQ adjusted-close series from 1999-03-10 through 2026-10-02;
- the canonical -4.5% daily shock / +10% recovery-from-low event logic;
- QQQ's existing 200-DMA and a one-session-lagged Fed lifecycle state where QQQ data exists.

Any leverage performance before TQQQ is explicitly **not applicable**. The S&P 500 is not QQQ; its signals are historical context, not interchangeable Nasdaq/TQQQ performance.

## Historical window context

| Window | Index signal proxy | Total index return | Maximum index drawdown | Actual TQQQ return |
|---|---|---:|---:|---|
| 1971–1975 | S&P 500 | -1.05% | -48.20% | Not applicable |
| 1973–1975 | S&P 500 | -24.27% | -48.20% | Not applicable |
| 1987 crash year | S&P 500 | +4.31% | -33.51% | Not applicable |
| 2000–2002 dot-com bear | QQQ | -74.28% | -82.96% | Not applicable |
| 2007–2009 GFC | QQQ | +7.09% | -53.40% | Not applicable |

Window total return is from first to last observation in that window, not a leveraged portfolio return.

## Findings for the canonical daily-shock signal

### 1973–1974: major gradual bear with no qualifying single-day shock

The S&P 500 drawdown episode began 1973-03-15, troughed 1974-10-03, and did not recover to 95% of its reference peak until 1980-01-28. The peak-to-trough decline was approximately **-48.2%**, and the -4.5% daily-shock rule had **no trigger during the episode**.

This is direct signal-level evidence that a single-day shock trigger cannot detect every prolonged bear. It is not evidence of how actual TQQQ would have performed in the 1970s.

### 1987: the signal detects the crash, but rallies are rapid and repeated

The S&P 500 proxy first entered the -5% drawdown episode on 1987-10-06. The first -4.5% daily shock occurred on 1987-10-16, eight sessions later. The recovery rule then recorded a decision close on 1987-10-21, three sessions after the shock; a later shock event occurred on 1987-10-26.

This illustrates the speed and repeated transitions of a V-shaped crash. It is a timing diagnostic only.

### 2000–2002: QQQ's daily shock rule fires repeatedly; the Fed-active overlay does not stay defensive through the whole bear

QQQ declined approximately **-82.96% peak-to-trough** from the 2000 peak to the 2002 trough. The shock/recovery signal produced many events across 2000–2002, including:
- 2000-04-03 shock, 2000-04-17 recovery decision;
- 2000-09-21 shock, 2000-10-19 recovery decision;
- 2001-02-02 shock, 2001-04-10 recovery decision;
- 2001-05-29 shock, 2001-10-04 recovery decision;
- 2002-06-19 shock, 2002-08-14 recovery decision.

The active-tightening × below-200-DMA condition first appeared on 2000-05-10, but the 200-DMA overlay repeatedly exited on brief crosses above trend and later the Fed state transitioned to EASING while QQQ continued its long decline. The candidate rule therefore did **not** maintain a continuous defensive state through the entire dot-com bear.

This is an important limitation: the overlay's 2022 improvement cannot be generalized to mean it detects all prolonged structural bears. The Fed-active condition is tied to the policy phase, while the market decline can persist after the Fed begins easing.

## Implications for the current actual-TQQQ comparison

1. The baseline is useful as a reproducible growth control and reacts to acute shocks, but the 1973 S&P proxy shows a class of slow bear it cannot detect through the daily-shock rule alone.
2. The active-tightening/200-DMA overlay materially helped the measured 2022 actual-TQQQ period, but signal-only QQQ history shows it is not a universal structural-bear detector: during the dot-com bear, its Fed state and market-trend conditions did not stay aligned throughout the decline.
3. The macro overlay tested on actual TQQQ did not identify 2022 under its frozen classifier, despite the older synthetic study's historical dot-com benefit. These are different periods and different kinds of evidence; neither result cancels the other.
4. Keep the baseline, 50% overlay, and 75% overlay as development candidates only. The current sample supports a wealth/drawdown trade-off, not a claim of survival through every historical bear.
5. Do not use synthetic pre-2010 leverage results to claim real TQQQ performance. Any future synthetic proxy must be separately labeled and fully specified.

## Reproducibility

- Workflow: https://github.com/eklu654/Trading-Bot/actions/runs/37887083424
- Script: https://github.com/eklu654/Trading-Bot/blob/main/research/canonical_shock_recovery_historical_signal_audit.py
- Workflow definition: https://github.com/eklu654/Trading-Bot/blob/main/.github/workflows/canonical-shock-recovery-historical-signal-audit.yml
- Current state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
