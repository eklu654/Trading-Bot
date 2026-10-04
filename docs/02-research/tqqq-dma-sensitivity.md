# TQQQ DMA Sensitivity — 2010 to Latest

## Purpose

This experiment directly answers whether the 200-DMA rule is materially better
or worse than other predeclared DMA lengths when applied to TQQQ alone.

The primary matrix compares TQQQ buy-and-hold plus 100, 125, 150, 175, 200,
225, 250, and 300 DMA variants.

All DMA variants use the same five-session re-entry confirmation. The only
variable in the primary matrix is the DMA length.

## Accounting

- Starting balance: $5,000
- Common evaluation start: first available TQQQ session in 2010
- End: latest available research-data session
- Price series: adjusted close
- Signal: prior-session close relative to prior-session DMA
- Exit: prior close below DMA
- Re-entry: prior close above DMA for five consecutive sessions
- Execution: next-session return
- Cash return: 0%
- No optimization on the evaluation period

## Additional control

A 200-DMA immediate-re-entry result is included separately to reconcile this
test with earlier 200-DMA research that did not use the five-session
confirmation rule.

## Required headline metric

The result reports the final account balance from $5,000 for every strategy,
alongside CAGR, maximum drawdown, volatility, Sharpe, Sortino, worst day, time
invested, and position transitions.

Artifacts:
data/research/tqqq_dma_sensitivity_primary.csv
data/research/tqqq_dma_sensitivity_2010_latest.csv
