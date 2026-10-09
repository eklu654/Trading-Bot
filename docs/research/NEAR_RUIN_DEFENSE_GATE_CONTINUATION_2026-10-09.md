# Near-Ruin Defense Gate — Continuation Log (2026-10-09)

**Status: UNRESOLVED. B0 remains the control; no defensive overlay is promoted.**  
**Purpose:** Continue the specific question: can a defensive rule reduce the synthetic pre-inception near-ruin risk without sacrificing the rapid recoveries that drive B0's returns?

## Frozen control and comparability

- Rule ID: canonical B0, QQQ adjusted-close daily return <= -4.5% exits at next TQQQ open; stay defensive until QQQ closes >= 10% above the post-trigger running low; re-enter next open.
- Starting capital: $5,000.
- Actual TQQQ control: 2010-02-11 through 2026-10-07, 4,189 aligned sessions; approximately $4.040M ending balance, -73.5343% maximum drawdown. This is a verified historical backtest under the frozen input and execution convention, not a forecast.
- Synthetic 3x QQQ proxy: 1999-03-10 through 2026-10-07; approximately $836,044 ending balance, -99.3720% maximum drawdown. During 2000–2002, the proxy returned -98.1713% and had -99.1484% local maximum drawdown. It did not cross -99.9% or zero in that run.
- **Interpretation boundary:** TQQQ did not exist in 2000. The synthetic proxy is an uncalibrated daily-reset 3x approximation, not actual TQQQ or a validated reconstruction of a real fund. Its near-ruin result identifies a stress case, not a historical TQQQ loss claim.

## Work inspected in this continuation

- Latest failed-bounce structural matrix run: [37915726270](https://github.com/eklu654/Trading-Bot/actions/runs/37915726270), artifact 11608513701; job completed successfully.
- Latest failed-bounce robustness run: [37915725568](https://github.com/eklu654/Trading-Bot/actions/runs/37915725568), artifact 11609492820; job completed successfully. Its event counterfactuals and 0/5/10/25/50-bp cost table were emitted.
- Latest independent event audit: [37915725606](https://github.com/eklu654/Trading-Bot/actions/runs/37915725606), artifact 11609277874; job completed successfully and recorded nine actual-TQQQ B0 events.
- Latest long-history drawdown/rally audit: [37915725769](https://github.com/eklu654/Trading-Bot/actions/runs/37915725769), artifact 11609397806; job completed successfully.
- The most recent research-test workflow [37915725661](https://github.com/eklu654/Trading-Bot/actions/runs/37915725661) completed successfully in this burst. Earlier bursts had cancelled test jobs; do not conflate those cancellations with this run.
- Multiple workflows in the same burst were triggered by successive pushes and repeated the same code/input. They are not independent replications.

## Defensive-rule results so far

1. **Structural + fast-shock matrix, continuously applied:** materially reduces drawdown in the synthetic proxy (best reported synthetic row about -88.65% vs B0 -99.37%) but the corresponding actual-TQQQ overlay loses most terminal wealth (best reported row about $727k vs B0 $4.040M) and turns the COVID crash/rebound window from +24.58% to -8.63%. Rejected.
2. **Non-sticky/daily structural matrix:** reduces some state persistence but still ends far below B0 on actual TQQQ and still blocks the COVID recovery. Rejected.
3. **Recovery-gated structural confirmation with 5/8/10-session fast exceptions:** actual-TQQQ ending balances about $1.724M / $3.102M / $3.102M versus B0 $4.040M; all have worse max drawdown. Rejected.
4. **Bounded 3/5/10-session wait after a slow flagged recovery:** actual-TQQQ ending balances about $3.921M / $3.774M / $3.451M; none beats B0 and drawdown worsens. Rejected.
5. **Active Fed tightening × below-200-DMA partial exposure:** the frozen-input ablation showed a promising risk/wealth trade-off in the modern sample (50% and 75% exposure rows ended about $4.087M / $4.125M with max DD -61.19% / -67.65% before costs). However, the apparent benefit is concentrated in the 2022 tightening bear; it has not demonstrated a robust defense of the 2000–2002 proxy, and it is not yet a validated choice.
6. **Historical signal-only audits:** slow bears can occur without a qualifying daily shock; the 1973–1974 S&P 500 decline is one example. The dot-com QQQ decline was about -82.96%, and a Fed-active/below-200-DMA state did not remain continuously defensive through the entire decline. These are index/signal diagnostics, not leveraged portfolio returns.

## Main diagnosis

The problem is not simply that the current matrix needs another threshold. The known structural flags are too nonspecific at recovery points: they can be present during the successful 2019 and COVID recoveries. Conversely, the daily shock rule can be late or absent during slow deterioration. A useful defense must therefore distinguish **slow deterioration before/around the entry of a bear** from **fast rebound after a shock** without using future outcomes.

## Next gate — do not launch another blind parameter grid

1. Keep B0 unchanged as the control and keep the $5,000 start, frozen common inputs, and close-to-next-open accounting convention.
2. Any next candidate must be a *single pre-registered rule* with a live-available state definition and an explicit rapid-recovery escape. Do not use forward labels, eventual Fed cycle endpoints, or same-day intraday returns as decision inputs.
3. Before a full strategy replay, run a signal-state timeline on the synthetic 1999–2009 period and the actual 2010–2026 period. Explicitly mark dot-com, 2008–09, COVID, 2018 Q4, 2020 June/September, 2022, and April 2025. Report whether the defense is active before a slow-bear loss, and whether it remains active on the B0 recovery decision / next-open re-entry.
4. Then run exactly one frozen candidate versus B0 and buy-and-hold on both data regimes, with identical inputs and 0/10/25/50-bp transition-cost sensitivity. Report terminal balance, max drawdown, worst rolling 252-session return, time at each exposure, every entry/exit, COVID and 2022 window results, 2000–2002 proxy ending value and local drawdown, and first crossing of -99%, -99.9%, or zero.
5. Use chronological development/validation/holdout boundaries; do not select from the already-inspected 2020/2022 outcomes and then describe them as out-of-sample confirmation. If no candidate clears the wealth-retention and recovery-preservation gates, retain B0 and document that no tested defense solves the trade-off.

## Audit caution

The objective is not to minimize drawdown at any cost. A candidate that avoids near-ruin by sitting out the compounding recoveries is not a successful result. Conversely, B0's $4.040M actual-period terminal balance does not prove robustness: its -73.53% actual-period maximum drawdown and the synthetic proxy's -99.37% maximum drawdown remain major stress warnings. No candidate is approved for paper/live operation by this log.
