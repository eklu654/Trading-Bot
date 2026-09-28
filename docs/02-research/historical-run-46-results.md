# Historical OPTIONS-001 Replay — Corrected Run 48

**Corrected run:** [GitHub Actions run 48](https://github.com/eklu654/Trading-Bot/actions/runs/36481614364)  
**Code commit:** `087539ffc4ff4fb24e0d715d5bacdf1e6fa2d0a6`  
**Status:** Completed successfully

> **Correction:** All OPTIONS-001 results from run 46 are superseded because of an expiration-selection defect. Use the corrected run 48 results below. ETF figures from run 46 are unaffected by that options-specific defect.

## Corrected OPTIONS-001 results (run 48)

The replay now selects one expiration per entry date before selecting option legs. A post-run audit found no call/put expiration inconsistencies in the baseline and 2×-loss-stop ledgers.

| Fill assumption | Defense | Completed trades | Total P/L | Mean P/L/trade | Win rate | Worst trade | Challenged | Adjusted |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative | No adjustment | 96 | $5,885 | $61.30 | 79.17% | -$2,098 | 53 (55.21%) | 0 |
| Conservative | Roll untested | 96 | $4,108 | $42.79 | 76.04% | -$2,097 | 53 (55.21%) | 22 (22.92%) |
| Midpoint | No adjustment | 98 | $7,211 | $73.58 | 81.63% | -$2,080 | 53 (54.08%) | 0 |
| Midpoint | Roll untested | 98 | $6,343 | $64.72 | 82.65% | -$2,081 | 53 (54.08%) | 21 (21.43%) |

### Corrected interpretation

- Rolling the untested leg reduced aggregate P/L by $1,777 under conservative fills and $868 under midpoint fills.
- Worst-trade outcomes were effectively unchanged; the roll did not materially improve the observed worst trade.
- The roll's adjustment cash-flow contribution is positive in the summary ($1,907 conservative; $1,828 midpoint). Its sign and relationship to per-trade adjustment P/L, net credit, exit debit and final P/L still require reconciliation; do not label it a net debit yet.
- These are one-contract SPY mechanics results, not a $2,000 account backtest. They omit full account-level buying-power, NLV, concentration, margin, assignment and portfolio-risk constraints.
- EOD challenge detection and bid/ask/midpoint assumptions are model limitations. This does not validate future performance or prove that all defense methods fail.

**Research disposition:** do not promote ROLL_UNTESTED on current evidence. Retain it as a comparison only. Audit adjustment accounting and the max-debit proxy before relying on risk statistics.

## ETF-001: DMA versus DMA plus VIX safety filter

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
