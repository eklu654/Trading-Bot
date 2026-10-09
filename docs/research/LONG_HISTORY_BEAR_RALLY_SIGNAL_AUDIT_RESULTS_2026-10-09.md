# Long-history bear-rally signal audit — results

Date: 2026-10-09  
Status: **Signal-only descriptive audit; no trading rule selected.**

## Run and data
- Workflow: [run 37913829220](https://github.com/eklu654/Trading-Bot/actions/runs/37913829220), job `audit` passed.
- Artifact ID: `11607543639`; digest: `sha256:864433f76e885fe5e5717dac38aca7fd72b0d62507034d0592674e2f0489118e`.
- S&P 500 index (^GSPC), 1970-01-02 through 2026-10-07, 14,313 sessions. This does not calculate TQQQ returns or portfolio balances.
- Trigger: daily index close return <= -4.5%; recovery: first close >= +10% above post-trigger low. Label: within 252 sessions, -10% from recovery decision before +20% (failed), +20% before -10% (successful), otherwise censored.

## Results
18 events: 10 failed, 6 successful, 2 censored. Failed events include two events in 1987 and two in 2000–2002; the 2020–2021 sample has two successful events; the one resolved 2022–2026 event was successful. This sample is too small and selected to estimate stable predictive performance.

Across resolved events, failed versus successful labels showed:
- 60-session return at the recovery decision: mean -14.4% versus -4.6%; median -18.8% versus -3.6%.
- Price versus 100-DMA: mean -12.3% versus -2.7%.
- Price versus 200-DMA: mean -13.8% versus -4.4%.
- 20-session volatility proxy: mean 0.601 versus 0.399 (units are the source script's volatility measure; do not interpret these values as annualized percentages without checking code).
- Recovery speed itself did **not** separate outcomes overall: failed mean 17.6 sessions versus successful mean 20.3, because the 1987 crashes recovered to the +10% threshold very quickly and then failed. Median speeds were 4.5 versus 17.5 sessions.

The 2000–2002 cases had mean 34 sessions from low to recovery and were both labeled failed. However, their MACD histogram was positive at the recovery decision, a reminder that a single common oscillator can give misleading confirmation in a countertrend rally.

## Interpretation and limits
The most coherent descriptive signal here is **remaining price/trend damage plus weak intermediate-horizon returns**, not recovery speed alone. But the resolved sample has only 16 observations; thresholds/features were not validated out of sample, and the S&P 500 event set is not the canonical QQQ event ledger. The 2022-2026 group has only one resolved event, so it cannot establish performance for the 2022 bear.

No candidate is advanced from this study. Next, inspect the current actual-TQQQ failed-bounce feature audit and the 3-layer validation/attribution outputs as separate experiments; ensure their signal and trading windows are correct before interpreting balances. Preserve the canonical B0 strategy unchanged as control.
