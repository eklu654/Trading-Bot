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

The independently reproduced terminal balance is approximately $128.315 billion.

## 2020 is confirmed as a successful independent catch

The 100-DMA strategy exited on **2020-02-27**, at the beginning of the COVID crash.

This is especially important for the Fed research because the Federal Reserve's first emergency 2020 rate cut was not until **March 3, 2020**, when it cut the target range by 50 basis points. The second emergency cut came March 15, taking the target to 0–0.25%. The official Fed record confirms both actions.

Therefore, the 100-DMA signal did **not** need a prior Fed hike, Fed cut, or rate-cycle transition to detect the 2020 market break. The market-price signal independently moved defensive before the Fed's emergency response.

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
|---|---:|---:|---:|
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

The Fed is clearly relevant, but the evidence now argues against using Fed policy as the primary trigger.

The 2000 episode occurred during an aggressive tightening cycle.

The 2008 episode began after the Fed had already started cutting.

The 2020 episode began before the Fed's emergency cuts.

The 2022 episode began before the first 2022 rate hike.

So the Fed cannot simply be represented as "hiking = danger" or "cutting = safety."

A better hypothesis is:

- **Market trend = primary trigger**
- **Fed regime = contextual classifier**
- **Macro stress = contextual confirmation**
- **Re-entry/recovery behavior = critical for avoiding whipsaw**

## Next research gate

For every 100-DMA exit/re-entry episode, reconstruct the information actually available at the time:

1. Fed target rate and direction.
2. Days since latest hike/cut.
3. Cumulative tightening/loosening from the preceding policy-cycle trough/peak.
4. Distance from the policy-cycle peak.
5. Yield-curve state.
6. Labor/activity/credit stress.
7. Market decline magnitude and duration.
8. Subsequent recovery speed.

The objective is classification, not threshold optimization.

Only after this episode anatomy is understood should we test an adaptive rule out-of-sample.
