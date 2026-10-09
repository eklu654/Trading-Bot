# Long-history drawdown/recovery-rally diagnostic — results

Date: 2026-10-09  
Status: **Signal-only exploratory diagnostic; no strategy selected.**

## Execution record
- Workflow: [run 37913801136](https://github.com/eklu654/Trading-Bot/actions/runs/37913801136), completed successfully.
- Artifact ID: `11607489248`; digest: `sha256:e3433b3d57435e4c99ec16ecbdd845db6c7b298b201ef4418b1ada3aa0efd0b0`.
- Data: S&P 500 index (^GSPC), 1970-01-02 through 2026-10-07, 14,313 rows. This is not QQQ/TQQQ and computes no leveraged portfolio balances.
- Event rule: trigger when index falls below -10% from trailing 252-session high; mark first close at least +10% above post-trigger low; re-arm after recovering to 95% of trigger peak.
- Outcome label: within 252 sessions after recovery, did a -10% decline occur before a +20% gain? If neither, event is censored.

## Results
There were 24 events: 12 failed, 9 successful, and 3 censored. Selected stress windows:
- 1970s: one failed and one censored event.
- 1987: one failed event; the recovery threshold was reached just two sessions from the low, but the index then fell another 10% within three sessions.
- 2000–2002: two failed events; average low-to-recovery speed was 34.5 sessions. At the recovery decisions, mean 120-session forward return was -4.1% and mean 200-session forward return was +0.7%, before the outcome's competing-threshold termination.
- 2010–2019: two failed, one successful, one censored event.
- 2020–2021: two successful events.
- 2022–2026: two failed and two successful events.

Across the 12 failed and 9 successful resolved events, average low-to-recovery speed was 38.5 versus 20.8 sessions; medians were 31.5 versus 16 sessions. This is a potentially useful descriptive distinction, but it is not a trading rule and is based on a small, selected event sample.

## Caveats
- This is a broad-market S&P 500 diagnostic, not the canonical QQQ -4.5% shock / +10% recovery rule and not evidence of pre-inception TQQQ performance.
- Forward outcomes define the labels and are only for retrospective classification; they must never be used as live inputs.
- Event selection and re-arming can omit overlapping downturns; 24 observations are far too few to support extensive feature selection.
- Individual technical features did not provide a decisive separation in this sample. Treat feature averages as exploratory, not proof of predictive value.

## Research implication
The result supports examining **recovery speed and post-recovery confirmation** as a hypothesis, but the 1987 counterexample shows speed alone can fail badly. A next candidate should combine a strictly causal confirmation criterion with an explicit fast-rebound escape, and must be tested on QQQ canonical events and actual TQQQ only from its inception. Do not simply transplant this S&P 500 event label into the trading rule.
