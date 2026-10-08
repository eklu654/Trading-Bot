# Trading-Bot Research — Current State

**Last updated:** 2026-10-08  
**Active investigation:** Reverify the QQQ shock / recovery TQQQ strategy family.  
**Starting capital:** $5,000.

## Active baseline (user-confirmed, exact rule still being recovered)
The user's remembered current baseline is approximately **$3.3M**, based on a QQQ daily-drop trigger and +10% recovery from the post-shock low, plus an additional anti-bear-rally rule. The exact anti-fakeout rule must be recovered from prior source history/logs before implementing or changing it. Do not substitute the simple ~$4.04M strategy for this baseline.

## Results status
- **~$3.337M structural-matrix result: REJECT AS CURRENTLY IMPLEMENTED / REVERIFY.** Source: `research/failed_bounce_structural_matrix.py`. Confirmed defect: the event builder assigns future 252-session outcome labels; strategy signal generation skips events labelled `censored`. Future outcomes therefore gate whether recent events are traded. This is look-ahead/sample-selection leakage. The reported number may be reproducible but is not a valid strategy result as implemented.
- **~$4.04M canonical shock/+10% result: PROVISIONAL / NOT APPROVED.** This is the simpler QQQ -4.5% daily shock, defensive until +10% off the post-shock low, using actual TQQQ returns. It does not include the remembered anti-bear-rally filter. Need corrected independent day-by-day reconstruction and chronological validation.
- **~$3.7M Fed/DMA synthetic-history result: REJECTED FOR ACTUAL-TQQQ CLAIMS.** It used synthetic leveraged returns and is not the actual-TQQQ shock/recovery baseline.
- **Historical reason the ~$4M result was previously withdrawn:** not recovered yet; don't invent it. Investigate code, run logs, commits and prior decisions.

## Source files inspected
- `research/failed_bounce_structural_matrix.py` — blob `92ed802d5e4c97064cae6191e74b3ba89980d8c4`
- `research/failed_bounce_robustness.py` — blob `753ecc24f8df11406601495c2427e457fcd7be22`
- `research/audit_failed_bounce_canonical_independent.py` — blob `740d3bb7f71a9c143efe61b153b91c940cc39c80`
- `research/failed_bounce_strategy_walkforward.py` — blob `e6f7cd1103ab749b5cc20ca6a97726ad3095e325`
- `research/causal_execution.py` — blob `caf48a0f64b0485021cf27adf0d822ab795735ae`
- Detailed checkpoint: `docs/research/TQQQ_SHOCK_RECOVERY_REVERIFICATION_LOG_2026-10-08.md`

## Mandatory next steps
1. Recover exact frozen anti-bear-rally rule from git history, workflow logs, or committed artifacts.
2. Fix signal construction so future event labels never affect whether/when the strategy trades.
3. Use one date-aligned frame for QQQ adjusted-close signals and actual TQQQ adjusted OHLC; implement close[t] -> next-open[t+1] execution once.
4. Generate a dated event/trade ledger and assert signal construction does not consume future labels.
5. Reproduce the remembered ~$3.3M baseline, then separately reconstruct the ~$4.04M simple rule.
6. Compute buy-and-hold on identical dates, price basis, capital, and execution assumptions.
7. Only then run frozen chronological holdouts and transaction-cost/parameter sensitivity checks.

## Context-preservation rule
Before any new experiment, read this file and the detailed checkpoint. After every meaningful step, commit the current rules, exact output/result, status (VERIFIED / PROVISIONAL / REJECTED / UNVERIFIED), reason, commit SHA, workflow run ID, and next step. Never silently replace prior findings. At the end of every work session, update this file first.