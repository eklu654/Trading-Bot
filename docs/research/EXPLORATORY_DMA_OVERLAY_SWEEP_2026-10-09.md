# Fresh exploratory DMA overlays on canonical QQQ shock/recovery strategy

**Date:** 2026-10-09  
**Status:** design frozen; execution pending  
**Type:** exploratory feature discovery; results must not be described as validated.

## Purpose

At the user's direction, start a fresh search without assuming prior conclusions about how DMA-based signals work. Keep the canonical QQQ shock/recovery baseline unchanged and measure whether a moving-average feature adds value as an overlay. This document is separate from prior rejected DMA-only and Fed/DMA experiments; old results remain preserved.

## Frozen baseline

- Signal: QQQ adjusted close.
- Traded instrument: TQQQ, initial capital $5,000.
- Signal window: recorded 2010-01-01 through 2026-10-08; report actual aligned dates.
- Enter defense when QQQ adjusted-close daily return <= -4.5%; track post-shock running low; leave defense when QQQ adjusted close is >= 10% above that low.
- Signal at close[t] executes at open[t+1].
- Baseline otherwise holds 100% TQQQ.
- No leverage proxy before TQQQ inception in the primary portfolio comparison.

## Initial DMA candidate grid

Compute moving averages from QQQ adjusted close, using completed observations only. Test periods: **20, 30, 40, 50, 60, 75, 100, 125, 150, 175, 200, 250 sessions**. The requested 50/100/200 are explicitly included. This is a finite exploratory grid, not a claim that these periods are theoretically privileged.

For each length, test the following distinct feature forms, independently:
1. **Below/above state:** QQQ close < its DMA.
2. **Cross-down event:** close crosses from at/above to below DMA.
3. **Cross-up event:** close crosses from below to at/above DMA.
4. **Slope/trend:** DMA today versus its value 20 sessions earlier (positive/negative).
5. **Price-to-DMA distance:** report continuous percentage distance; do not optimize thresholds in this first pass.

## Overlay semantics to compare (predeclared)

- **Diagnostic only:** feature timestamps and market outcomes; no portfolio change.
- **Sticky defense:** the first qualifying feature arms defense until the corresponding feature's recovery condition is met. For below/above state, defense ends when close returns to/above DMA. For cross-down event, defense starts on the cross-down and ends on the next cross-up.
- **Baseline interaction:** when a structural defense is armed, baseline shock/recovery logic continues to be tracked in parallel. The structural overlay can keep exposure at zero beyond the baseline recovery only while its condition remains armed; execution at next open. Never reset or erase the baseline event ledger because of overlay activation.

Do not silently mix these variants. Each has a distinct rule ID. The first run should report diagnostics for all feature forms, then portfolio simulations for the two explicitly defined sticky variants.

## Measures

For every candidate, report:
- Ending wealth from $5,000, CAGR, max drawdown, worst rolling 12-month return, average exposure, defensive days, exits/reentries, turnover and costs.
- Incremental ending wealth vs unchanged baseline and TQQQ buy-and-hold.
- Outcomes for 2020 COVID V-shaped recovery, 2022 bear, 2018 Q4, 2020 June/September false positives, 2025 April; plus mechanically selected worst rolling 12-month QQQ windows.
- Event timing and missed rebound after each defense exit.
- Segment results in chronological order. These are exploratory results, not independent validation.

## Controls against false discovery

- Do not select a winner based on 2022 alone or drawdown alone.
- Report every grid row, not just best candidates.
- Account for the fact that testing many lengths creates multiple-comparison/selection bias.
- Freeze any candidate before testing an untouched later chronological holdout. Once inspected, a period is development data, not a holdout.
- Use the same QQQ/TQQQ aligned sessions, adjusted-price conventions, next-open execution, starting balance, and costs across all candidates.
- Do not conflate the signal's index-only behavior with TQQQ portfolio results.
- No Fed condition in this first DMA-only pass; Fed features are a separate future experiment after this baseline sweep is documented.
- No assumption that any DMA candidate is already accepted or rejected based on previous experiments.

## Next actions

1. Implement a reproducible script that reads the repository's established data source/cache and emits machine-readable daily states, event ledgers, per-candidate metrics, and a hash manifest.
2. Run the same-date baseline reproduction alongside the entire candidate grid.
3. Audit the outputs and record which features, if any, warrant a predeclared follow-up. Do not change this plan after viewing outcomes; append follow-up plans as new documents.
