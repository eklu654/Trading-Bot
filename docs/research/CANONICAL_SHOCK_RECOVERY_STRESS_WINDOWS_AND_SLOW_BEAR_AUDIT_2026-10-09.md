# Baseline Stress Windows and Slow-Bear Trigger Audit — 2026-10-09

**Status:** Diagnostic of the unchanged working baseline; no new strategy rule selected.  
**Frozen-input source:** same-input reconciliation run [37884245700](https://github.com/eklu654/Trading-Bot/actions/runs/37884245700), artifact 11595546962.  
**Input SHA-256:** `a7e63d7d936d9fcb44a4f928b8f9dcd8d31f621e7d4a0082bd217b2543d03ad2`.  
**Data:** 4,189 common sessions, 2010-02-11 through 2026-10-07.  
**Execution:** close[t] signal, open[t+1] execution; prior position earns overnight, new position earns intraday.

## A. Exact stress windows from the frozen daily equity curve

For each window, start equity is the previous session's ending equity, and ending equity is the last session in the window. Return is calculated from those two values for each portfolio independently. Drawdown is measured from the portfolio's running peak inside the displayed window, including the start equity. These are inherited-account diagnostics, not independent $5,000-reset simulations.

| Window | Strategy start → end | Strategy return | Buy/hold start → end | Buy/hold return | Window max DD: strategy / buy-hold | Days with defensive close signal |
|---|---:|---:|---:|---:|---:|---:|
| COVID acute crash, 2020-02-19–2020-07-31 | $441,650 → $550,196 | +24.58% | $341,707 → $355,526 | +4.04% | -47.01% / -69.92% | 36 |
| 2018 Q4 selloff, 2018-10-01–2019-02-28 | $217,931 → $196,319 | -9.92% | $211,425 → $151,893 | -28.16% | -31.63% / -57.53% | 49 |
| 2022 tightening bear, 2022-01-03–2022-12-30 | $1,417,876 → $427,832 | -69.83% | $990,695 → $207,154 | -79.09% | -72.60% / -81.02% | 93 |
| June 2020 exit, 2020-06-01–2020-07-31 | $477,646 → $550,196 | +15.19% | $246,497 → $355,526 | +44.23% | -14.72% / -14.72% | 16 |
| September 2020 exit, 2020-09-01–2020-11-30 | $743,672 → $673,519 | -9.43% | $480,546 → $470,600 | -2.07% | -37.76% / -35.37% | 26 |
| April 2025 exit, 2025-03-03–2025-06-30 | $1,910,773 → $2,011,386 | +5.27% | $925,188 → $1,030,869 | +11.42% | -47.06% / -47.92% | 4 |

The June 2020 and April 2025 windows show opportunity cost: in both, the baseline missed part of a strong rebound after a qualifying shock. September 2020 also underperformed in the local window. The initial COVID shock and 2018 Q4 exit were helpful. These differences are why event-by-event counterfactuals should remain part of the audit.

## B. Mechanical slow-bear screen

Definition, fixed before inspecting strategy outcomes:
- Use QQQ adjusted close and the rolling 252-session high.
- A drawdown episode begins when QQQ is at least 5% below that high.
- The reference peak is the rolling high at episode entry; episode ends when QQQ recovers to 95% of that reference peak.
- Report only episodes whose trough reaches at least -15% from the reference peak.
- Find the first QQQ adjusted-close daily return <= -4.5% during the episode. This is a signal-timing diagnostic, not an optimized rule.

| Episode start | QQQ trough | Episode end | Peak-to-trough decline | First -4.5% daily shock | Delay from episode start |
|---|---|---|---:|---|---:|
| 2010-05-13 | 2010-07-02 | 2010-09-16 | -15.6% | None | No trigger during episode |
| 2011-08-04 | 2011-08-19 | 2011-09-16 | -16.1% | 2011-08-04 | 0 sessions |
| 2016-01-06 | 2016-02-09 | 2016-03-29 | -16.1% | None | No trigger during episode |
| 2018-10-18 | 2018-12-24 | 2019-03-13 | -22.8% | 2018-10-24 | 4 sessions |
| 2020-02-24 | 2020-03-16 | 2020-05-08 | -28.6% | 2020-02-27 | 3 sessions |
| 2022-01-13 | 2022-11-03 | 2023-07-17 | -35.1% | 2022-05-05 | 77 sessions |
| 2025-02-27 | 2025-04-08 | 2025-05-13 | -22.8% | 2025-04-03 | 25 sessions |

The central vulnerability is now measurable: the single-day shock rule did not trigger during the 2010 and early-2016 episodes despite QQQ declines of about 16%; in 2022, the first qualifying shock arrived 77 sessions after the drawdown episode began. It reacted quickly in COVID and 2018. This does not prove that a moving-average or Fed overlay is better; it identifies the specific gap a candidate overlay would need to address.

## C. Interpretation

1. **Acute crash:** the baseline avoided a substantial portion of the COVID crash's leveraged loss and was back in TQQQ after the March 26 recovery signal. It nevertheless had a separate June 2020 exit that cost meaningful rebound exposure.
2. **Gradual/prolonged bear:** 2022 still produced a -69.8% calendar-year loss on the inherited strategy account, despite outperforming TQQQ buy-and-hold. The first daily-shock defense was late relative to the mechanically defined drawdown episode.
3. **Slow correction without a shock:** 2010 and 2016 reached -15% or worse without this rule activating. These are concrete examples of what the strategy cannot detect by design.
4. **Do not jump to a fix:** the next candidate should be a narrow, frozen structural overlay that activates only when the already-defined market structure and live-safe Fed state align. Measure its benefit against the unchanged baseline and its opportunity cost in COVID/false-positive periods. No new indicator search or parameter sweep.

## Reproducibility

- Same-input reconciliation run: https://github.com/eklu654/Trading-Bot/actions/runs/37884245700
- Frozen daily curve and events are in artifact `tqqq-canonical-same-input-reconciliation` (artifact ID 11595546962).
- First period scorecard: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CANONICAL_SHOCK_RECOVERY_FIRST_STRESS_SCORECARD_2026-10-09.md
- Current project state: https://github.com/eklu654/Trading-Bot/blob/main/docs/research/CURRENT_STATE.md
