# TQQQ Fed Lifecycle Research — 2026-10-05

## Conclusion

The Fed layer is retained, but as a regime/lifecycle classifier rather than a standalone crash detector.

## Key results

### Episode validation
FRESH_PAUSE + QQQ below 200 DMA is unusually bearish in the 2000 episode, but it also produces benign 2016/2019 false positives. Episode deduplication confirms the signal is not an artifact of overlapping daily observations.

### Persistence test
Requiring 10, 20, or 40 consecutive sessions below the 200 DMA did not solve the 2016 false positives. Full-exit CAGRs were 24.63%, 23.03%, and 22.63%, with maximum drawdowns around -98.5% to -99.1%. This branch is closed.

### Fed + curve + 200 DMA
The frozen yield-curve stress signal is the strongest transmission confirmation for the 2000-style regime. With FRESH_PAUSE + curve stress + QQQ below 200 DMA, sticky defense, and 5-session DMA reentry, full-exit performance was 25.44% CAGR, 516.5x ending multiple, and -98.30% maximum drawdown.

### Genuine recovery confirmation
The strongest frozen candidate adds a rising-200-DMA recovery condition: QQQ must be above the 200 DMA for 5 consecutive sessions and the 200 DMA must be rising.

Result:
- CAGR: 34.09%
- Ending multiple: 3,245x
- Maximum drawdown: -94.25%
- Defensive episode: 2000-09-11 through 2003-04-22
- No later defensive episodes in the sample

### Chronological holdout
| Period | Candidate CAGR | Buy & Hold CAGR | Candidate defensive fraction |
|---|---:|---:|---:|
| 1999-03-10 to 2009-12-31 | 14.19% | -31.35% | 24.0% |
| 2010-01-01 to 2019-12-31 | 48.91% | 48.91% | 0.0% |
| 2020-01-01 to 2026-10-04 | 46.60% | 46.60% | 0.0% |
| Full sample | 34.09% | 9.83% | 9.4% |

The candidate's large full-sample advantage is therefore overwhelmingly a dot-com-era survivability effect. It does not improve the modern-era TQQQ path.

### Post-tightening transmission
Using FRESH_PAUSE or EASING plus QQQ below 200 DMA and one frozen macro transmission dimension showed:

- Labor: 24.44% CAGR, -99.23% max drawdown; catches 2008 but too late.
- Activity: 18.87% CAGR, -99.02% max drawdown; catches 2008/2020 but too late.
- Credit: 18.47% CAGR, -99.70% max drawdown; catches 2008 but too late.
- Curve: 33.58% CAGR, -94.25% max drawdown; strongest, but primarily 2000/2025.

### Fed-gated macro quorum
Frozen 2-of-4 and 3-of-4 macro quorum tests produced 20.83% and 14.57% CAGR respectively, with maximum drawdowns of -99.02% and -99.70%. This reinforces the earlier finding that more confirmation is not automatically better.

## Current research classification

KEEP THE FED LAYER.

The evidence supports this architecture:

1. Fed tightening begins.
2. Restriction accumulates.
3. Fed pauses.
4. Transmission indicators determine whether the pause is benign or dangerous.
5. Market trend determines whether the deterioration is actionable.
6. Recovery requires genuine confirmation.

The best current Fed candidate is therefore a research component for identifying a 2000-style post-tightening regime, not a complete production defense.

## What remains unresolved

The Fed branch does not adequately protect 2008 or 2020. Those regimes require a separate live-safe transmission/market layer. This should be researched architecturally rather than by random DMA or exposure tuning.

Do not reopen the already-explored DMA/partial-exposure family solely to improve this Fed result.

## Automation

Research workflows created and validated in this branch include episode validation, sticky defense, persistence confirmation, macro transmission confirmation, weekly reentry, rising-DMA recovery, chronological holdout, post-tightening transmission, and Fed-gated macro quorum.

The repository-wide pytest collection problem caused by research runners named test_*.py was fixed with pytest.ini. The subsequent repository test suite passed.