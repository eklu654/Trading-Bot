# B0 QQQ Drawdown-Warning Counterfactual — 2026-10-10

## Status

**All candidates rejected for promotion.** The counterfactual completed successfully on the isolated branch.

- Actions run: https://github.com/eklu654/Trading-Bot/actions/runs/38041217122
- Artifact: https://github.com/eklu654/Trading-Bot/actions/runs/38041217122/artifacts/11665747496
- Tested code commit: `59cd74d58fe316f6aec8f87f05888625369ed142`
- Market input: canonical QQQ/TQQQ frozen common input, generated and reloaded by the existing reconciliation module.
- Window: 2010-01-04 through 2026-10-07; $5,000 initial balance; execution is close signal to next open.

## Rule tested

Canonical B0 stays as the upper bound: QQQ daily adjusted return <= -4.5% exits at next open; re-entry follows the existing +10% recovery-from-low rule.

The additional warning state is based on QQQ adjusted close versus the rolling 252-session high:
- Candidate family DD10 enters warning below -10% and restores the overlay only after drawdown recovers to -5%.
- Candidate family DD15 enters warning below -15% and restores the overlay only after drawdown recovers to -10%.
- While warning is active, target exposure is capped at 0%, 50%, or 75% of TQQQ; the B0 signal can still reduce exposure further.
- The state is decided at close and therefore takes effect at the next open. Costs are applied to exposure changes.

This is a small retrospective counterfactual, not a walk-forward-selected or production-ready rule.

## Results (0 bps, continuous $5,000 inception)

| Strategy | Warning exposure | Ending balance | Difference vs B0 | Max drawdown | Improvement vs B0 |
|---|---:|---:|---:|---:|---:|
| B0 baseline | — | $4,040,315 | — | -73.53% | — |
| DD15 | 75% | $3,239,394 | -$800,921 (-19.8%) | -70.21% | +3.32 pp |
| DD15 | 50% | $2,484,391 | -$1,555,925 (-38.5%) | -67.34% | +6.19 pp |
| DD15 | 0% | $1,278,202 | -$2,762,113 (-68.4%) | -65.69% | +7.84 pp |
| DD10 | 75% | $1,834,217 | -$2,206,099 (-54.6%) | -64.79% | +8.74 pp |
| DD10 | 50% | $761,916 | -$3,278,399 (-81.1%) | -55.47% | +17.06 pp |
| DD10 | 0% | $100,639 | -$3,939,676 (-97.5%) | -61.04% | +12.50 pp |

DD10 warning state was active for 801 sessions over 23 episodes. DD15 was active for 376 sessions over 9 episodes.

## Transaction-cost sensitivity

Ending balance after the stated cost per full exposure change:

| Strategy | 0 bps | 10 bps | 25 bps |
|---|---:|---:|---:|
| B0 baseline | $4,040,315 | $3,964,236 | $3,852,658 |
| DD15 / 75% | $3,239,394 | $3,175,223 | $3,081,246 |
| DD15 / 50% | $2,484,391 | $2,432,742 | $2,357,203 |
| DD15 / 0% | $1,278,202 | $1,249,124 | $1,206,691 |
| DD10 / 75% | $1,834,217 | $1,786,233 | $1,716,544 |
| DD10 / 50% | $761,916 | $736,438 | $699,781 |
| DD10 / 0% | $100,639 | $95,825 | $89,023 |

## Decision

No warning threshold/exposure candidate passed the practical test. The most conservative terminal-wealth sacrifice was DD15/75%, yet it still finished about $801k below B0 and improved maximum drawdown by only 3.3 percentage points. More aggressive warning overlays reduced drawdown more but destroyed much more terminal wealth. DD10's hard exit is especially damaging, consistent with a warning rule that stays defensive through recoveries.

The event audit correctly identified a slow-bear failure mode, but this full-portfolio counterfactual shows that a simple drawdown threshold plus hysteresis does not solve it. **Do not add this overlay to the working strategy.**

## Next research direction

Avoid further blind threshold sweeps. Any next candidate should use a more discriminating regime variable (the existing Fed-state hypothesis remains worth testing) and must demonstrate, on identical frozen inputs, both:
1. a meaningful reduction in deep drawdown, and
2. a small enough rebound/terminal-wealth penalty to justify the defense.

No changes were merged to `main`.
