# Historical Research Run 46 — Results and Interpretation

**Run:** GitHub Actions `Historical Research` #46  
**Commit:** `95a2b4c7d0f0509ee34aebcc1ac8d47c04696351`  
**Status:** Completed successfully  
**Period:** ETF data 2010-03-11 through 2026-09-25; options replay uses historical SPY option-chain observations available to the workflow.

## Executive summary

The automated workflow completed all stages, including dataset construction, ETF backtests, regime evaluation, historical SPY option-chain retrieval, OPTIONS-001 baseline/no-stop replay, defense replay and artifact upload.

The current results do **not** validate a production strategy. They are exploratory outputs from the existing research models. In particular, the options replay is a one-contract SPY mechanics study and does not enforce the full $2,000 account's buying-power, concentration, margin, assignment or portfolio-risk constraints. Its dollar P/L must not be interpreted as a return on a $2,000 account.

## ETF-001: DMA versus DMA plus VIX safety filter

| Model | Total return (multiplicative) | Annualized return | Maximum drawdown | Annualized volatility | Sharpe, zero risk-free | Mean invested weight |
|---|---:|---:|---:|---:|---:|---:|
| 200-DMA | 1,813.5% | 19.53% | -37.53% | 29.73% | 0.751 | 50.31% |
| 200-DMA + VIX | 660.5% | 13.05% | -41.35% | 27.56% | 0.585 | 46.79% |

The VIX overlay as currently coded reduced the reported compounded return and did not improve maximum drawdown in this historical run. This is evidence against treating the current VIX rule as an established safety improvement. It does not prove that every VIX-based filter is ineffective: the threshold, trigger timing, re-entry rule, price basis and interaction with the moving average require controlled sensitivity testing.

The reported total returns are not directly comparable to a simple buy-and-hold investment without matching the cash, rebalance, distribution, fee, slippage and instrument-history assumptions. The ETF history begins when the available leveraged ETF data permits; the three funds do not share identical inception dates, so the portfolio's start date and missing-history handling need continued scrutiny.

## OPTIONS-001: no adjustment versus rolling the untested leg

Candidate: `BROAD_SIDEWAYS`; SPY; one position at a time; nominal 45-DTE selection within 30–60 DTE; approximately 16-delta entry legs; 50% profit target or 21-DTE exit; one roll maximum. Challenge is detected using end-of-day closes at/beyond a short strike.

| Fill assumption | Defense | Completed trades | Total P/L | Mean P/L/trade | Win rate | Worst trade | Challenged trades | Adjusted trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative bid/ask | No adjustment | 103 | $4,557 | $44.24 | 72.82% | -$1,537 | 49 (47.57%) | 0 |
| Conservative bid/ask | Roll untested | 103 | $2,955 | $28.69 | 71.84% | -$2,297 | 49 (47.57%) | 19 (18.45%) |
| Midpoint | No adjustment | 106 | $5,266 | $49.68 | 75.47% | -$1,466 | 50 (47.17%) | 0 |
| Midpoint | Roll untested | 106 | $3,768 | $35.55 | 75.47% | -$2,255 | 50 (47.17%) | 19 (17.92%) |

### Interpretation

- In both fill models, rolling the untested leg lowered total and mean P/L versus the no-adjustment control.
- The roll did not improve the worst trade; the worst observed outcome became more negative in both fill models.
- Under conservative fills, the roll reduced reported win rate by about one percentage point. Under midpoint fills, win rate was unchanged.
- The roll's adjustment cash-flow contribution was a net debit of $1,297 under conservative fills and $1,352 under midpoint fills (as reported by the replay summary's adjustment accounting).
- Turbulent/high-volatility mean P/L was notably lower with the roll: $29.13 to $7.94 under conservative fills; $33.97 to $14.43 at midpoint. Sideways/choppy results also declined modestly.

**Research disposition:** do not promote `ROLL_UNTESTED`. The current deterministic implementation fails the project's initial promotion gate on aggregate results and worst-trade behavior. Keep it as a documented comparison, not an active rule. Do not proceed to roll-out or inversion until the replay's accounting and assumptions are reviewed and a distinct hypothesis justifies further work.

## Important limitations and audit items

1. **Account feasibility:** no full portfolio-level $2,000 buying-power or NLV sizing gate is applied in this one-contract options replay. Large aggregate dollar P/L relative to initial capital is a warning that the replay is not a deployable account simulation.
2. **Execution:** the conservative model uses bid/ask conventions on EOD observations; it is not a true intraday fill simulator. Midpoint results are optimistic sensitivity, not expected fills.
3. **Data coverage:** options results depend on the historical chain vendor's available contracts and quotes. Missing quotes, contract selection, quote quality, and historical survivorship/coverage need explicit audits.
4. **Regime labels:** `BROAD_SIDEWAYS` is a candidate filter, not a validated forecast. The output includes many observations that fall into `TRENDING_NORMAL`; the label does not mean every entry was truly sideways.
5. **Single strategy/underlying:** these outputs cover SPY short strangles, not the proposed full underlying and structure universe.
6. **No live inference:** historical backtest results are sensitive to model specification and are not evidence of future returns.

## Next steps

1. Audit replay cash-flow arithmetic, contract selection and the meaning of `max_observed_open_debit_proxy` before interpreting risk statistics.
2. Add an explicit account ledger with cash, realized/unrealized P/L, BPR, NLV, and trade rejection reasons; run at $2,000, $5,000, $10,000 and $25,000.
3. Add walk-forward / chronological split reporting to the defense comparison itself; avoid selecting parameters from the full history.
4. Revisit ETF VIX threshold and re-entry mechanics through a prespecified sensitivity grid, including a no-VIX baseline.
5. Only after these audits, decide whether to expand options structures or test further defense mechanisms.

## Artifacts

The workflow uploaded a `historical-research-results` artifact containing the daily ETF ledgers, regime datasets and summaries, opportunity-window outputs, and OPTIONS-001 replay ledgers and summaries. See the run page: https://github.com/eklu654/Trading-Bot/actions/runs/36459483295
