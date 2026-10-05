# TQQQ Dot-Com Survivability Research

## Research question

TQQQ did not exist during the 2000-2002 dot-com collapse. This experiment reconstructs a **synthetic daily-reset 3x QQQ exposure** from QQQ's historical adjusted daily returns, beginning with QQQ's March 10, 1999 inception. QQQ tracks the Nasdaq-100, so this is a much closer stress proxy for TQQQ than the Nasdaq Composite itself.

This is explicitly a **survivability/stress test**, not a claim that a synthetic series is identical to actual TQQQ.

## Frozen methodology

- Starting balance: **$5,000**
- Data: QQQ historical adjusted daily returns
- Synthetic leverage: **3x daily**
- Start: **1999-03-10**
- Signals: prior-session information only
- Cash earns 0%
- No parameter optimization in this experiment
- Modern-era candidates are frozen from the completed 2010-2026 research
- TQQQ itself launched after the dot-com bust, so all pre-2010 TQQQ results are synthetic

### Strategies

1. Synthetic TQQQ buy-and-hold
2. 200-DMA / 0% below / immediate re-entry
3. 200-DMA / 0% below / 3-session re-entry
4. 225-DMA / 0% below / immediate re-entry
5. 250-DMA / 0% below / 10-session re-entry
6. 225-DMA / 50% below / immediate re-entry

## Required outputs

For every strategy:

- ending balance;
- CAGR;
- maximum drawdown;
- minimum equity;
- trough date;
- time from peak to trough;
- date/time to recover the original $5,000;
- date/time to recover the pre-crash peak;
- average exposure.

The primary stress window is the 2000-2002 collapse and the long recovery afterward.

## Interpretation rules

- Do not treat synthetic TQQQ as an actual historical fund.
- Do not select parameters from the dot-com results.
- The objective is to determine whether the spectacular modern TQQQ result depends on surviving an extreme historical path that did not occur in the fund's own live history.
- The results should be compared against the completed 2010-2026 research rather than replacing it.

## External factual anchors

QQQ began trading on March 10, 1999. The Nasdaq-100 itself dates to 1985, so QQQ provides an actual ETF history spanning the dot-com episode. TQQQ is a daily 3x Nasdaq-100 product, but its multi-day result can differ materially from 3x the index's multi-day return.

## Status

Automated workflow. Results are authoritative only after the workflow completes successfully and the generated artifacts are inspected.
