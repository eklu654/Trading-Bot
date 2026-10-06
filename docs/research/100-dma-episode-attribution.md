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
