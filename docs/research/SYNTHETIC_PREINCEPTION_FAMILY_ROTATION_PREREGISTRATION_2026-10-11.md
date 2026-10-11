# Synthetic Pre-Inception Family-Rotation Stress Study — Preregistration (2026-10-11)

## Purpose
Test whether the frozen DMA-250/top-2/5-session family-rotation selector would have suffered near-ruin during the 2000–2002 technology bear under an explicitly synthetic daily-reset leveraged-return model. This is a stress test, not a claim about actual TQQQ, SOXL, SPXL, UDOW, or TNA returns before their inception.

## Frozen selector
- Benchmark families: SPY proxy (SPY), Nasdaq-100 (QQQ), semiconductor index (^SOX), Dow (DIA), Russell 2000 index (^RUT).
- Signals use benchmark close versus its 250-session simple moving average, calculated only through the prior close. Synthetic benchmark returns use close-to-close price returns for all five families, excluding dividends consistently across ETF and index proxies.
- Eligible families rank by prior close / prior 250-DMA minus one; equal-weight the top two eligible families; rebalance every five common sessions; otherwise hold cash.
- Warm-up: begin scored performance on the first common session where all five 250-session moving averages are valid. End 2002-12-31. No parameter search.

## Synthetic leveraged return model
For each benchmark's daily return r and prior close 3-month Treasury-bill annualized yield y (from ^IRX, percentage points), the proxy daily return is:

`r_3x = 3*r - 2*(y/100)/252 - 0.0095/252`

This approximates 3x daily reset, financing drag on the extra 2x notional, and a fixed 0.95% annual expense ratio. The daily proxy wealth index compounds these returns and is absorbing at zero; if a family proxy is wiped out, it never revives. This is a simplified stress model with no tracking error, path-specific borrowing terms, taxes, or actual ETF implementation.

## Controls and outputs
- Frozen selector with 0 and 25 bps turnover cost.
- Synthetic 3x QQQ buy-and-hold with 0 and 25 bps (no turnover after entry).
- 1x equal-weight buy-and-hold benchmark basket as an unleveraged reference.
- Report ending equity, max drawdown, minimum equity, worst rolling 252-session return, first crossings below 1% and 0.1% of initial equity, and first zero-equity date. Also report daily equity/weights/returns and each family proxy's ruin status.
- Verify all data series are frozen to a manifest with hashes and dates. Use actual underlying benchmark history only; all 3x returns are explicitly synthetic.

## Decision rules
This single historical stress window cannot select or tune strategy parameters. If the synthetic family selector approaches near-ruin, record that as a risk diagnostic and do not optimize thresholds to rescue this event. If it avoids near-ruin, do not infer future safety or assume it generalizes. Preserve actual post-inception ETF tests and the frozen B0/family-rotation controls. No paper/live promotion follows from this study alone.
