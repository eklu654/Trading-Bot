# Most-Aggressive Macro-Regime Control — Research Specification

**Status:** Proposed research gate — 2026-10-05

## Research question

The current DMA research treats the market trend itself as the primary defensive trigger. The survivability study raises a different hypothesis:

> The most aggressive mode should not use a DMA exit at all during the normal economic regime. It should remain fully exposed until a separately measured, broad economic/regime deterioration indicates that the environment has fundamentally changed.

This is deliberately different from a faster or slower DMA. A DMA is a tactical market-price control; this proposed control is a **structural macro-regime control**.

The purpose is not to assume that the dot-com economy should dictate a modern strategy. It is to test whether the exceptional 2000–2002 path can be recognized as a distinct macro regime without sacrificing the enormous upside of remaining fully exposed during ordinary modern corrections.

## Why this test is necessary

The current evidence creates a genuine conflict:

- TQQQ buy-and-hold is the historical wealth benchmark.
- TQQQ 200-DMA/next-open materially reduces path risk but sacrifices substantial terminal wealth.
- Synthetic pre-TQQQ testing shows that a daily-reset 3x Nasdaq-100 exposure would have been devastated by the dot-com collapse.
- The pre-2002 economic environment was structurally different from much of the modern sample.
- Therefore, a universal DMA may be solving the wrong problem: it may be reacting to ordinary market volatility that does not represent a true structural regime break.

The research should test whether a **macro-aware sliding defense** can preserve buy-and-hold behavior in normal regimes while activating a strong defense only when the broader economic environment has changed.

## Candidate operating modes

The research will compare at least these frozen conceptual controls:

1. **MAX_AGGRESSIVE**
   - 100% TQQQ exposure.
   - No DMA.
   - No routine price-based exit.
   - Remains active until the macro regime controller declares a structural deterioration.

2. **MACRO_DEFENSIVE**
   - Activated only by the macro controller.
   - Defense may move to cash, lower-leverage exposure, or a predeclared DMA control.
   - Re-entry is controlled by the same macro framework rather than an arbitrary short DMA delay.

3. **DMA_CONTROL**
   - Existing best validated DMA control, retained as the direct tactical benchmark.
   - No macro information.
   - This is the control against which the macro approach must demonstrate incremental value.

4. **BUY_AND_HOLD**
   - Permanent 100% TQQQ exposure.
   - Wealth benchmark and upper-risk-bound reference.

No parameter is selected from the final holdout.

## Macro regime design

The first implementation must avoid building a complicated indicator soup. It should use a small number of broad, economically interpretable dimensions that existed during the full historical sample.

Candidate dimensions:

### Labor market

- Unemployment rate level.
- Unemployment rate change over a multi-month horizon.
- Unemployment-rate acceleration.

The purpose is to detect deterioration in the real economy rather than short-term market noise.

### Business cycle / activity

- ISM manufacturing or equivalent broad activity indicator where a consistent historical series is available.
- Industrial production growth.
- Real personal income or another broad activity proxy where publication history is sufficient.

### Financial conditions / credit stress

- High-yield credit spread or a closely related FRED series with sufficiently long history.
- Investment-grade credit spread where useful.
- Financial conditions index if a consistent long-history series is available.

Credit stress is important because leveraged equity exposure can become dangerous before conventional recession statistics fully confirm a downturn.

### Yield curve

- 10Y minus 2Y Treasury spread.
- Optional 10Y minus 3M spread as a robustness check.

The yield curve must not be treated as a standalone sell signal. It is a contextual structural-regime feature.

### Inflation / policy pressure

- CPI inflation trend.
- Federal-funds rate or broad policy-rate proxy.

These are contextual features rather than direct trading triggers.

### Equity-market confirmation

Market data may be used as a **confirmation layer**, but not as the primary definition of a macro regime.

Candidate confirmations:

- QQQ drawdown from trailing high.
- QQQ medium-term trend.
- volatility regime.

This prevents the system from waiting for a recession indicator alone while the leveraged position is already experiencing a catastrophic market decline.

## Regime states

The first deterministic classifier should use three states:

- **STRUCTURAL_EXPANSION**
- **MACRO_DETERIORATION**
- **MACRO_CRISIS**

The exact thresholds are research parameters and must be selected chronologically.

### STRUCTURAL_EXPANSION

Default state.

MAX_AGGRESSIVE remains fully exposed.

Ordinary corrections, volatility spikes, and short-lived market selloffs do not automatically leave this state.

### MACRO_DETERIORATION

Evidence indicates that the broader economy and/or financial system has moved materially away from the expansion regime.

The system may reduce exposure according to the frozen defensive policy.

A single weak monthly data point must not be enough to trigger this state.

### MACRO_CRISIS

Multiple independent macro dimensions indicate severe systemic deterioration, ideally with market/credit confirmation.

The system enters the strongest predeclared defense.

This state is intended for events analogous to a genuine structural bear regime rather than ordinary corrections.

## Persistence and hysteresis

A central design requirement is **persistence**.

The macro controller should not switch modes because of one noisy observation.

Every candidate classifier must therefore test:

- minimum number of consecutive qualifying observations;
- confirmation across multiple macro dimensions;
- minimum time before reversing state;
- separate entry and exit thresholds;
- publication-date-aware data availability.

The goal is to avoid rapid mode oscillation.

## Publication-lag rule

All macro features must use the information that would actually have been available to the strategy at the decision time.

For each economic series, the dataset must retain:

- observation date;
- release/availability date where available;
- value;
- source.

A value cannot influence a historical decision until its release date.

If release dates cannot be established reliably for a series, that series must either be excluded from the primary test or clearly labeled as a sensitivity-only feature.

This is critical. Macro data is especially vulnerable to look-ahead bias through later revisions.

## Sliding-defense concept

The preferred conceptual architecture is not:

> market falls below DMA → sell.

It is:

> remain fully exposed while the economic regime is normal → detect persistent broad deterioration → progressively activate defense → remain defensive until the broader regime has demonstrably stabilized.

This permits the strategy to ignore many ordinary market drawdowns while still having a mechanism for historically extreme structural regimes.

The initial research should test at least three defense strengths:

- **Light:** reduce TQQQ exposure but retain meaningful upside.
- **Medium:** move primarily to cash / low-leverage exposure.
- **Hard:** move to cash or the strongest validated defensive sleeve.

These are research controls, not production rules.

## Required historical tests

### Test A — Dot-com stress

Run the macro controller against the synthetic daily-reset 3x QQQ history beginning 1999-03-10.

Required questions:

1. Did the classifier recognize deterioration before or during the catastrophic decline?
2. How much synthetic TQQQ drawdown occurred before defense activated?
3. How much capital was preserved?
4. Did the system re-enter too early?
5. How long did it remain defensive?
6. How much of the eventual recovery was missed?
7. What would $5,000 become under each defense mode?

The classifier must be frozen before examining the final stress outcome.

### Test B — Modern full history

Run the same frozen classifier over the common modern sample.

Compare against:

- TQQQ buy-and-hold;
- TQQQ 200-DMA/next-open;
- the strongest frozen DMA/re-entry candidates;
- MAX_AGGRESSIVE without macro defense.

### Test C — Ordinary corrections

Explicitly measure whether the macro controller avoids unnecessary exits during:

- ordinary corrections;
- short volatility shocks;
- fast V-shaped declines;
- sideways markets;
- recoveries that do not represent structural economic deterioration.

This test is essential. A macro controller that catches 2000 but repeatedly exits normal bull-market corrections is not useful.

### Test D — Other structural stress periods

Without optimizing on individual episodes, report behavior during broad historical stress regimes including:

- 2000–2002;
- 2007–2009;
- 2020;
- 2022;
- later available stress episodes.

These are interpretation slices after the chronological classifier is frozen.

## Evaluation metrics

For every candidate:

- ending balance from $5,000;
- CAGR;
- maximum drawdown;
- minimum equity;
- maximum dollar drawdown;
- time to recover starting capital;
- time to recover prior peak;
- average exposure;
- percentage of time in each macro state;
- number of regime transitions;
- average defensive duration;
- premature exits;
- missed recovery return;
- worst 20-day return;
- worst 60-day return;
- rolling 3/5/10-year CAGR;
- drawdown breach frequency;
- time underwater.

The most important comparison is:

> How much terminal wealth does macro defense sacrifice in normal conditions versus how much catastrophic path risk does it remove in genuine structural bear regimes?

## Walk-forward discipline

Initial chronological structure:

- Training: earliest available history through a fixed pre-validation cutoff.
- Validation: subsequent period.
- Final holdout: latest untouched period.

Thresholds, persistence lengths, and defense strengths must be frozen before the final holdout.

No named crisis may be used as the reason to tune a threshold.

## Important methodological constraint

Do not assume that a recession indicator is an effective trading signal merely because it is economically meaningful.

Economic indicators are often lagging.

Therefore the research should separately measure:

1. **economic recognition lag** — when the macro data first identifies deterioration;
2. **market protection lag** — how much leveraged-equity loss occurs before the defense actually becomes active;
3. **recovery cost** — how much upside is lost because the controller remains defensive too long.

A theoretically correct recession classifier can still be a poor trading control if it protects capital only after most of the damage has occurred.

## Expected outcome categories

Every tested macro control should be classified as one of:

- **VALUE-ADDING:** preserves substantially more downside than buy-and-hold without sacrificing disproportionate normal-regime wealth.
- **REDUNDANT:** produces little benefit beyond an existing DMA control.
- **OVER-DEFENSIVE:** reduces drawdown but sacrifices too much of the TQQQ wealth engine.
- **LAGGING:** recognizes structural deterioration too late to protect leveraged exposure.
- **UNSTABLE:** switches states too frequently or fails persistence/robustness tests.
- **PROMISING:** warrants deeper validation but is not yet a production candidate.

## Key hypothesis

The central hypothesis is deliberately asymmetric:

> In a modern expansion regime, the best strategy may genuinely be to leave TQQQ alone. The defense should exist primarily to recognize when the environment has stopped being the environment in which that aggressive exposure works.

This is the research question we should answer rather than continuing to search indefinitely for a universally optimal DMA.

## Relationship to the current DMA research

This study does **not** invalidate the DMA family.

The DMA family answers:

> Can a price-based trend control improve survivability across all environments?

The macro-control study asks:

> Can we avoid paying the DMA's opportunity cost during normal regimes while still having a structural escape mechanism for abnormal economic regimes?

Both must remain in the comparison until the evidence separates them.

## Gate

No macro controller may be promoted merely because it saves the synthetic dot-com path.

It must also demonstrate:

- chronological robustness;
- modern-era wealth retention;
- low unnecessary turnover;
- acceptable protection lag;
- recovery discipline;
- no holdout tuning;
- and a clear improvement over the existing TQQQ 200-DMA control or buy-and-hold tradeoff.

