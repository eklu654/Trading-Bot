# 100-DMA Episode Attribution — Current Findings

Status: frozen descriptive research, not parameter optimization.

## Baseline

The confirmed synthetic-TQQQ survivability experiment uses:

- $5,000 starting capital
- 1999-03-10 through 2026-10-03
- daily-reset 3x QQQ proxy
- QQQ adjusted close for the 100-DMA signal
- 100-DMA
- 100% exposure above the DMA
- 0% exposure below the DMA
- immediate re-entry
- next-open execution

The independently reproduced terminal balance is approximately **$128.315 billion**.

## 2020 is confirmed as a successful independent catch

The 100-DMA strategy exited on **2020-02-27**, before the Federal Reserve's first emergency 2020 rate cut on March 4 in the corrected official historical record. The Fed then cut another 100 basis points on March 16, taking the target range to 0–0.25%.

Therefore, the 100-DMA signal did **not** need a prior Fed hike, Fed cut, or rate-cycle transition to detect the 2020 market break. The market-price signal independently moved defensive before the emergency Fed response.

The 100-DMA path then experienced several rapid re-entry/exit signals:

- 2020-02-27: exit
- 2020-03-02: re-enter
- 2020-03-03: exit
- 2020-03-04: re-enter
- 2020-03-06: exit
- 2020-04-14: re-enter

This is exactly the trade-off we need to study: the rule recognized the shock quickly, but the violent V-shaped market also generated whipsaws.

From the February 27 exit through the April 14 sustained re-entry, synthetic TQQQ buy-and-hold fell about 9.6% from the exit-date level and suffered an interim drawdown of roughly 51.0%. The 100-DMA strategy remained largely defensive through the collapse and then re-entered during the recovery.

This makes 2020 an extremely useful test case because it was **not a conventional Fed-tightening-led bear market**.

## Episode anatomy

The value is not evenly distributed across hundreds of small exits. It is dominated by a small number of long defensive episodes.

Important examples include:

| Exit | Re-entry | Defensive days | Synthetic TQQQ return while out |
|---|---|---:|---:|
| Apr 12, 2000 | Jun 19, 2000 | 45 | −8.3% |
| Sep 25, 2000 | May 21, 2001 | 163 | −92.6% |
| Mar 12, 2002 | Oct 21, 2002 | 154 | −82.3% |
| Aug 29, 2008 | Feb 9, 2009 | 110 | −78.5% |
| Apr 5, 2022 | Jul 29, 2022 | 78 | −39.6% |

The longest 2000-2001 and 2002 defensive intervals are particularly important: the synthetic TQQQ proxy lost roughly 92.6% and 82.3%, respectively, while the strategy remained flat.

## The central trade-off

The same 100-DMA rule also produces short exits that are followed by rapid positive returns. Those are the whipsaw cost.

The research question therefore should not be:

> "Is 100-DMA universally optimal?"

It should be:

> **"What distinguishes a trend break that will persist from one that will reverse?"**

That distinction is now more important than comparing another dozen DMA lengths.

## Crisis comparison

| Window | 100-DMA strategy | Buy-and-hold synthetic TQQQ |
|---|---:|---:|
| 2000-2003 | +509.6% | −99.61% |
| 2008-2009 | +254.8% | −61.31% |
| 2020 | +188.7% | +118.8% |
| 2022 | +14.2% | −78.2% |

These are window returns from the first to last trading observation in each calendar window, not standalone backtests with capital reset for each crisis.

## Fed context

The Fed is clearly relevant, but the evidence argues against using Fed policy as the primary trigger.

The official historical record shows:

- 1999–2000: a sustained tightening cycle culminating at 6.50%.
- 2001: rapid easing after the tightening cycle broke.
- 2007–2008: easing began before the worst of the financial crisis.
- 2020: emergency easing came after the market-price signal had already exited.
- 2022: tightening began after the market had already entered the deterioration that produced the first 100-DMA exit.

The Fed therefore cannot simply be represented as "hiking = danger" or "cutting = safety." The policy state may still materially distinguish environments, but it is not a reliable standalone trigger.

A better hypothesis is:

- **Market trend = primary trigger**
- **Fed regime = contextual classifier**
- **Macro stress = contextual confirmation**
- **Re-entry/recovery behavior = critical for avoiding whipsaw**

## New macro-attribution layer

A new frozen descriptive workflow now attaches macro context to every 100-DMA episode.

The research script is at research/analyze_tqqq_100dma_macro_context.py.

The workflow is at .github/workflows/tqqq-100dma-macro-context.yml.

It records:

1. Fed target rate immediately before the exit.
2. Current Fed policy-cycle direction.
3. Net change within the current consecutive hike/cut cycle.
4. Number of moves in that cycle.
5. Days since the latest Fed move.
6. 2s10s Treasury yield-curve level.
7. 20-trading-day change in the 2s10s curve.
8. The market outcome of the defensive episode.

This is intentionally **not** an adaptive trading rule yet. It is an evidence-building layer whose job is to answer whether persistent failures and whipsaws have materially different macro environments.

The Fed historical target-rate source is the Federal Reserve's official Open Market Operations record. The current official table confirms, among other periods, the 2008 cuts, 2020 emergency cuts, 2022 tightening sequence, and later policy changes. 

## Important methodological warning

The Fed target series is event-based and therefore suitable for describing the policy state known on a given date. The Treasury curve is sourced from FRED daily observations.

This first macro pass is **descriptive, not publication-vintage-safe** for labor or other revised macroeconomic series. We therefore should not add unemployment, GDP, payrolls, or similar revised indicators to a prospective trading rule until we explicitly handle their historical publication vintages.

## Next research gate

For every 100-DMA exit/re-entry episode, reconstruct the information actually available at the time:

1. Fed target rate and direction.
2. Days since latest hike/cut.
3. Cumulative tightening/loosening from the preceding policy-cycle trough/peak.
4. Distance from the policy-cycle peak.
5. Yield-curve state.
6. Labor/activity/credit stress, with publication-vintage controls.
7. Market decline magnitude and duration.
8. Subsequent recovery speed.

The objective is classification, not threshold optimization.

Only after this episode anatomy is understood should we test an adaptive rule out-of-sample.


## Macro classification result — October 6, 2026

The first completed macro-classification run analyzed **160** 100-DMA exit/re-entry episodes.

### Fed policy state is not a strong discriminator

At the exit date:

| Policy state | Episodes | Negative episode return | Major interim-loss rate (<= -50%) | Median BH return to re-entry | Median worst interim return |
|---|---:|---:|---:|---:|---:|
| Easing | 93 | 15.1% | 4.3% | +4.39% | -0.35% |
| Tightening | 67 | 17.9% | 4.5% | +3.71% | -2.02% |

The difference is small. In particular, the rate of major losses is essentially identical between easing and tightening.

The seven episodes whose worst interim synthetic-TQQQ loss exceeded 50% also demonstrate why a simple Fed-direction rule is inadequate:

- 2000-09-25: tightening
- 2001-08-03: easing
- 2002-03-12: easing
- 2008-08-29: easing
- 2020-03-06: easing
- 2022-04-05: tightening
- 2000-04-12: tightening

The severe episodes therefore span both policy directions.

### Continuous Fed relationships are weak

Across all 160 episodes, Pearson correlations with the episode's worst interim buy-and-hold return were:

- Fed target at exit: **-0.123**
- Days since latest Fed move: **+0.136**
- Fed cycle net change: **+0.035**
- Fed moves in cycle: **+0.080**
- Distance from cycle peak: **-0.003**
- Distance from cycle trough: **+0.072**

None is strong enough to justify making Fed state the primary exit trigger.

The 2s10s curve variables were also weak:

- Curve level at exit: **+0.052**
- 20-day curve change: **+0.093 Pearson / +0.249 Spearman**

The latter is the strongest relationship found so far, but it is still far below what we would want before turning it into a trading rule. More importantly, it is an episode-level descriptive relationship and has not been validated prospectively.

### Interpretation

This does **not** mean the Fed layer is useless.

It means the evidence currently supports a narrower role:

1. **100-DMA / market trend remains the primary defense mechanism.**
2. **Fed policy remains a regime/context variable.**
3. **Macro variables can be used to explain why an exit is occurring and potentially to modify re-entry behavior, but there is not yet evidence that they should replace the price signal.**
4. **The next useful macro question is therefore not "Can the Fed predict exits?" but "Can macro context distinguish genuine trend breaks from short-lived whipsaws after the 100-DMA has already exited?"**

That is a materially narrower and more testable question.

## Research gate after this result

The Fed layer should remain in the research architecture, but we should stop expanding it indiscriminately.

The next test should compare **persistent vs. short 100-DMA exits** using only information available at the exit:

- Fed policy state
- 2s10s curve level/change
- recent market decline magnitude
- volatility / realized volatility
- distance below the DMA
- rate of change of the DMA itself
- breadth or participation if a clean historical series is available

The objective is classification of persistence, not another parameter sweep.



## Market-state persistence result — October 6, 2026

The next frozen descriptive pass added market-state measurements at each exit:

- distance of QQQ below/above its 100-DMA
- 20-day DMA slope
- 5-, 20-, and 60-day QQQ returns
- 20-day realized QQQ volatility

These variables were compared with three episode outcomes across the same 160 episodes: return to re-entry, worst interim buy-and-hold return, and time spent defensive.

### Market state is substantially stronger than Fed state

The strongest relationships with **worst interim return** were:

| Exit feature | Pearson | Spearman |
|---|---:|---:|
| 20-day realized volatility | **-0.387** | -0.245 |
| Distance from 100-DMA | **+0.324** | +0.285 |
| 60-day QQQ return | +0.155 | +0.156 |
| 20-day DMA slope | +0.133 | +0.165 |
| 20-day return | -0.061 | -0.044 |
| 5-day return | -0.056 | -0.066 |

For comparison, the strongest Fed relationship with worst interim return was only **-0.123** for the Fed target level; the strongest yield-curve relationship was **+0.093 Pearson / +0.249 Spearman** for the 20-day 2s10s change.

The duration relationships are also notable:

- Distance from the 100-DMA vs. defensive duration: **-0.255 Pearson / -0.403 Spearman**
- Realized volatility vs. defensive duration: **+0.266 Pearson / +0.173 Spearman**
- 60-day QQQ return vs. defensive duration: **-0.178 Pearson / -0.189 Spearman**

These are descriptive relationships, not optimized thresholds.

### What this changes

We now have evidence for a much more specific hypothesis:

> **The important information may arrive after the 100-DMA exit, in the market's state at the break, rather than in the Fed's policy state.**

A severe break tends to have characteristics such as:

- a larger gap below the DMA,
- elevated realized volatility,
- weaker medium-term momentum,
- and a more negative DMA slope.

That gives us a plausible way to distinguish a genuine regime break from a shallow whipsaw **without making the Fed responsible for predicting the break itself**.

The Fed layer remains valuable as context, but the evidence now strongly favors investigating a **market-state persistence classifier** before attempting any Fed-driven adaptive exit rule.

## Next research gate: persistence classification

The next experiment should remain descriptive/out-of-sample rather than become another DMA parameter sweep.

The candidate task is:

1. Freeze the 100-DMA exit.
2. Use only information available at the exit.
3. Predict whether the defensive episode will be short/whipsaw-like or persistent/severe.
4. Use time-based holdouts rather than random train/test splits.
5. Compare a market-state-only model against:
   - Fed-only context
   - market-state + Fed context
6. Judge whether Fed context adds incremental information after market state is known.

Only if the combined model produces stable out-of-sample improvement should we consider using macro context to modify re-entry behavior.

