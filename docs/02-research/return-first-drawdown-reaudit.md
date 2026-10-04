# Return-First Drawdown Re-Audit — 2026-10-03

## Purpose

This audit reviews prior ETF research decisions for cases where large historical drawdown was treated as a reason to deprioritize a strategy before comparing the wealth actually produced.

The audit deliberately distinguishes:

- **DD-driven deprioritization:** drawdown materially influenced the decision.
- **Return/holdout rejection:** the strategy failed for other reasons. These are not counted as drawdown mistakes.
- **Accounting/data rejection:** the result was invalid or not comparable. These are not counted as drawdown mistakes.
- **Still a control:** a high-drawdown strategy was retained as a benchmark rather than rejected.

No strategy is retrospectively promoted merely because it had a high historical ending balance.

## Core finding

The repository provides strong evidence of **one major confirmed drawdown-framing mistake** and several related cases where drawdown was given more interpretive weight than the stated profitability objective justified.

The most important confirmed case is the 250-DMA/top-2/5-session family rotation. At 25 bps and $5,000 starting capital:

| Strategy | Execution | Ending equity | CAGR | Max DD |
|---|---|---:|---:|---:|
| Raw DMA250/top-2/C5 | prior close | $217,586 | 25.63% | -68.62% |
| Raw DMA250/top-2/C5 | next open | $166,456 | 23.61% | -69.91% |
| V30/L20/DD20 overlay | prior close | $22,825 | 9.62% | -38.94% |
| V30/L20/DD25 overlay | prior close | $28,599 | 11.12% | -41.27% |
| V30/L20/DD30 overlay | prior close | $33,102 | 12.11% | -43.65% |

The raw strategy was previously treated as unsuitable primarily because its drawdown was very large. The subsequent account replay demonstrated that this framing concealed an enormous terminal-wealth tradeoff: the risk overlays reduced drawdown but also reduced ending wealth by roughly an order of magnitude.

The correct interpretation is not that the raw strategy is automatically better. It is that the drawdown reduction must be evaluated as an explicit economic tradeoff rather than an automatic improvement.

## Candidate-by-candidate classification

### 1. DMA250/top-2/5-session family rotation — CONFIRMED DD-FRAMING ERROR

This is the clearest case.

The base strategy produced roughly $217.6k from $5k at 25 bps using the research prior-close convention and roughly $166.5k under next-open execution. Its maximum drawdown was about 69%.

We moved toward V30/L20/DD20–30 overlays because of the drawdown. Those overlays produced roughly $22.8k–$33.1k under the same $5k/25-bps/full-period comparison.

This was not enough evidence to replace the base strategy. The correct next step is to characterize the drawdown path and survivability while preserving the raw strategy as a first-class candidate.

**Status after audit:** primary research candidate.

### 2. Equal-weight five-family always-bull control — SHOULD NOT HAVE BEEN TREATED AS DISQUALIFIED BY DD

Historical result:

- Full-period CAGR: 33.85%
- Total return: 123.285x
- $5,000 equivalent ending wealth: approximately $621,427
- Maximum drawdown: -78.26%

This was a benchmark rather than a formal production candidate, so it is not counted as a formal rejection. However, its very large drawdown was used heavily in interpreting the benchmark.

The correct treatment is to preserve it as the aggressive offensive control and quantify its historical path, rather than dismissing it because of the drawdown.

**Status after audit:** permanent aggressive control; requires survivability analysis before any deployment consideration.

### 3. TQQQ buy-and-hold — NOT A DD-DRIVEN REJECTION

2018–2025:

- CAGR: 32.62%
- Max DD: -81.66%

The TQQQ 200-DMA/cash control produced 34.42% CAGR and -50.01% max DD.

We did not actually reject TQQQ buy-and-hold. It was retained as an important control. The data instead show a genuine tradeoff: in this window the 200-DMA rule historically improved both CAGR and drawdown.

Approximate $5,000 terminal values, using the reported CAGR and the window length, are useful only as estimates; the exact equity curve should be used for final comparison.

**Status after audit:** retained control, not a prior DD rejection.

### 4. SOXL buy-and-hold — NOT A DD-DRIVEN REJECTION

2018–2025:

- CAGR: 21.65%
- Max DD: -90.46%
- Approximate $5,000 terminal wealth: ~$25k

SOXL 200-DMA/cash:

- CAGR: 8.44%
- Max DD: -69.63%
- Approximate $5,000 terminal wealth: ~$9.6k

The drawdown is extreme, but the research did not formally reject SOXL buy-and-hold because of it. It was retained as a permanent aggressive benchmark.

This comparison is especially important to the return-first audit because it demonstrates that reducing drawdown can come with a very large wealth cost.

**Status after audit:** retained aggressive control.

### 5. SPXL buy-and-hold — NOT A DD-DRIVEN REJECTION

2018–2025:

- CAGR: 23.08%
- Max DD: -76.86%
- Approximate $5,000 terminal wealth: ~$25k

It remains a useful control rather than a rejected strategy.

**Status after audit:** retained control.

### 6. Original ETF-001 25%-cash 200-DMA — NOT A DD-DRIVEN REJECTION

The canonical historical baseline produced approximately:

- CAGR: 19.53%
- Max DD: ~-37.5%

The DMA+VIX variant produced approximately:

- CAGR: 13.05%
- Max DD: ~-41.4%

The plain DMA version remains the baseline. The lower drawdown was useful descriptive information, but the baseline was not selected solely because it minimized drawdown.

**Status after audit:** retained baseline.

### 7. ETF-001 cash-allocation variants — NEEDS RETURN-FIRST COMPARISON, NOT ASSUMED DEFENSIVE WIN

The repository explicitly established that cash percentage was an untested design choice and created a factorial comparison of 0%, 10%, 25%, and 50% cash against buy-and-hold and DMA controls.

Therefore these variants should not be considered rejected merely because higher cash allocations had lower drawdowns. Their terminal wealth needs to remain visible alongside drawdown.

**Status after audit:** reopen any variants previously deprioritized primarily for DD.

### 8. ETF-015 bull-family rotation — NOT A DD-DRIVEN REJECTION

ETF-015's best validation-only configuration reached approximately 33.30% annualized, but the validation-selected holdout was approximately 40.44% annualized, below the canonical ETF-001 holdout baseline.

The documented reason for not promoting it was chronological generalization/selection discipline, not simply drawdown.

**Status after audit:** not a DD mistake; remain rejected on the documented holdout gate unless re-audit finds a separate return-first issue.

### 9. ETF-016 consistency-gated bull selection — NOT A DD-DRIVEN REJECTION

No candidate passed the requirement to beat baseline Sharpe on both training and validation. This was a robustness/generalization gate, not a maximum-drawdown rejection.

**Status after audit:** not a DD mistake.

### 10. E3 volatility sizing — NOT A DD-DRIVEN REJECTION

E3 full-ratio sizing:

- CAGR 9.38%
- Max DD -16.79%

E3 square-root sizing:

- CAGR 15.78%
- Max DD -31.20%

E2 risk-adjusted selection:

- CAGR 24.47%
- Max DD -62.33%

The documented conclusion was that volatility sizing sacrificed too much upside. This is exactly the kind of tradeoff the new framework is supposed to preserve, but it was not a mistaken DD-based rejection.

**Status after audit:** not a DD mistake.

### 11. E4c risk-aware target — NOT A DD-DRIVEN REJECTION

E4c produced:

- Validation CAGR 6.23%, max DD -70.08%
- Holdout CAGR 26.97%, max DD -56.79%

It was not promoted because it did not reproduce the large absolute-return edge of deterministic E2 and still had substantial drawdown. Its primary rejection was lack of sufficient absolute-return improvement, not simply the drawdown.

**Status after audit:** not a DD mistake.

### 12. Inverse/bull-bear switching — NOT PRIMARILY A DD-DRIVEN REJECTION

The inverse branch failed because inverse exposure did not show persistent value across train, validation, and holdout and was highly transaction-cost sensitive.

For example, the predefined 200/50 C5 bear-enabled configuration had:

- Train CAGR: -2.46% at 0 bps
- Validation CAGR: -11.84%
- Holdout CAGR: +12.82%

At 25 bps:

- Train: -12.55%
- Validation: -18.10%
- Holdout: -2.21%

The no-bear control was dramatically stronger.

This branch should remain deprioritized, but not because of drawdown.

**Status after audit:** rejection remains supported by return/robustness/cost evidence.

## What this means for the historical research

The audit does **not** support saying that we threw away dozens of high-return strategies solely because of drawdown.

It does support saying that we made a significant methodological error in how we interpreted the family-rotation result, and that the same bias was present in how we discussed several aggressive controls.

The strongest concrete correction is:

> A strategy that historically turns $5,000 into $166k–$218k cannot be replaced by a $23k–$33k strategy merely because the latter has a smaller maximum drawdown unless we have explicitly decided that the drawdown reduction is worth that wealth sacrifice.

## Required follow-up

The next re-audit should therefore calculate, using the actual equity curves wherever available:

1. exact $5,000 ending balances;
2. maximum dollar drawdown;
3. lowest account value;
4. recovery time;
5. 25/50/60/70% drawdown events;
6. time spent below each threshold;
7. whether capital ever approached practical ruin;
8. next-open versus prior-close results;
9. 10/25/50 bps cost sensitivity;
10. parameter-neighborhood robustness.

The final comparison should preserve **aggressive offensive controls, baseline controls, and defensive overlays side-by-side**.

No candidate should be eliminated merely because its drawdown is uncomfortable.



## 2026-10-04 TQQQ DMA-grid update

The corrected TQQQ DMA × re-entry experiment has now tested 56 combinations rather than assuming the earlier 5-session rule.

On the common TQQQ-only period 2010-02-11 → 2026-10-02:

| Strategy | Ending $5k | CAGR | Max DD |
|---|---:|---:|---:|
| TQQQ buy-and-hold | $1,974,071 | 43.24% | -81.66% |
| TQQQ 225-DMA + immediate | $380,012 | 29.73% | -49.96% |
| TQQQ 200-DMA + 3-session | $369,948 | 29.52% | -48.14% |
| TQQQ 200-DMA + 5-session | $306,150 | 28.06% | -48.14% |

This is important for the return-first audit because the earlier 5-session rule was not validated as a robust universal choice. In the 200-DMA family, 3-session confirmation produced approximately $369.9k versus $306.1k for 5 sessions, with the same measured maximum drawdown. The broader grid also shows that long confirmation periods can materially destroy terminal wealth.

The strongest new TQQQ challengers should therefore be preserved as first-class controls rather than selecting 5 sessions by convention.

## 2026-10-04 bull/bear switching update

The corrected bull/bear artifact is now available after fixing a CI race in which the bull/bear process was launched in the background but not added to the workflow's PID wait list.

The full-period bull/bear matrix confirms that inverse exposure is not automatically a superior defense. Among bear-enabled configurations, the strongest terminal result in the tested matrix was approximately:

- SEMICONDUCTORS 150-DMA / bear 50-DMA / 5-session / 25% bear allocation: **~$330,348 from $5,000**
- CAGR: **28.83%**
- Max DD: **-76.15%**

That remains far below the TQQQ buy-and-hold control over its own full period and carries a substantially larger drawdown than the leading TQQQ DMA challengers.

The combined 2023-2026 holdout also shows that the strongest bear-enabled configurations do not establish a general superiority over bull-only controls. In particular, the bear-enabled 200-DMA/bear-50-DMA/5-session all-family configuration had 12.82% holdout CAGR in the earlier documented cost analysis, while the corresponding no-bear control was materially stronger.

**Current conclusion:** bull/bear switching remains a valid defensive challenger, but its rejection is supported by return/robustness/cost evidence rather than by drawdown alone.

## Revised research priority

The immediate comparison set should now preserve:

1. TQQQ buy-and-hold;
2. TQQQ 225-DMA + immediate;
3. TQQQ 200-DMA + 3-session;
4. TQQQ 200-DMA + 5-session;
5. TQQQ 200-DMA/next-open;
6. frozen family rotation;
7. bull/bear switching;
8. explicit risk overlays.

The next gate is common-period survivability and execution/cost sensitivity across this set, not another assumption-driven rejection based on maximum drawdown alone.
