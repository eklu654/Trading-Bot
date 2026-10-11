# F75 Prospective Shadow Decision Protocol

**Status:** Preregistered review rules; F75 remains shadow-only.  
**Frozen branch:** `research/qqq-slow-bear-audit`  
**Control:** B0  
**Candidate:** F75 = `min(B0, 0.75 when the active-tightening overlay is on, otherwise 1.0)`  
**Starting shadow balance:** $5,000  
**Primary modeled cost:** 25 bp per unit of exposure turnover; 0 bp and 50 bp are sensitivity cases.

## Purpose

Test whether the frozen F75 overlay's historical drawdown reduction repeats prospectively without materially sacrificing terminal equity or recovery participation. This protocol does not authorize threshold tuning, parameter searches, or live orders.

## Data-integrity gates

A review is invalid unless all of the following pass:

- Canonical historical input hash matches the pinned SHA-256 in the monitor.
- B0's reconstructed signal matches the frozen canonical signal exactly over the historical overlap.
- Ledger dates are unique and strictly increasing; each observation has finite prices, exposures, and equity.
- The first row is explicitly marked as an initialization row; it is not counted as a market-return observation.
- F75 is 75% exposure when the tightening overlay is active, capped by B0's independent defense. Overlay state 0 is not a full-exit instruction.
- Ledger state hash matches the committed ledger, and the latest observation date agrees with the ledger tail.
- No order submission or broker connectivity is introduced by this research workflow.

Any failed gate means **stop and repair the data/process; do not interpret performance**.

## Minimum evidence before a performance review

Do not infer efficacy from ordinary sessions in which the overlay is inactive.

Open a formal performance review only after both conditions are met:

1. At least 252 completed, non-initialization market sessions have been recorded prospectively.
2. At least one completed overlay-active episode has occurred, with at least 20 sessions during which F75's 75% cap actually reduced exposure relative to B0.

If these conditions are not met, continue collecting the frozen shadow ledger. Do not tune the overlay to manufacture an event or shorten the observation window after seeing results.

## Required report at review

Compare B0 and F75 from the same $5,000 prospective starting balance, on identical dates and using the ledger's realized exposure and costs. Report:

- Terminal equity and cumulative return at 0, 25, and 50 bp costs.
- Maximum drawdown and drawdown difference.
- Number of overlay-active sessions, sessions where F75 exposure was lower than B0, and total exposure reduction.
- Net return difference by calendar year and by each completed overlay-active episode.
- Realized exposure during the 20 and 60 sessions after each episode's QQQ low, using next-session realized exposure rather than close signals.
- Source hash, ledger hash, date range, initialization rows excluded, and all accounting checks.

The 25 bp case is the primary comparison because terminal equity is the main objective. The 0/50 bp cases test cost sensitivity. Do not report episode-normalized balances as if they were the prospective account's compounded balance.

## Predeclared screening criteria

F75 may advance from shadow-only to a **separate paper-trading evaluation** only if all criteria pass at the first eligible review:

1. **Terminal-equity benefit:** F75 terminal equity exceeds B0 at 25 bp costs.
2. **Cost robustness:** F75 terminal equity is not below B0 at 50 bp costs.
3. **Drawdown benefit:** F75 maximum drawdown is at least 3 percentage points less severe than B0 at 25 bp costs.
4. **Recovery participation guardrail:** after a completed overlay-active episode's QQQ low, F75's average realized exposure over the next 60 sessions is not more than 20 percentage points below B0's, where the full 60-session window is available. Report 20-session participation as a diagnostic; it is not a separate pass condition.
5. **No single-episode shortcut:** all completed overlay-active episodes are shown separately. A positive aggregate result cannot conceal a materially negative result in another completed episode.
6. **Integrity:** every data-integrity gate above passes.

These are screening criteria, not a guarantee of future performance and not an automatic promotion. Passing permits only a separately reviewed paper-trading evaluation; it does not permit live deployment. Failing any performance criterion means F75 remains shadow-only with its parameters frozen. Do not optimize thresholds in response to a failed review.

## Current status (2026-10-11)

- Prospective ledger initialized from 2026-10-08; latest recorded market session is 2026-10-09.
- Two rows exist, but only one is a return-bearing session. The overlay was inactive on both dates, so they provide no efficacy evidence.
- Minimum evidence requirements are not met. **No performance decision is permitted yet.**
- Historical analysis remains mixed: full-period 25 bp terminal equity is modestly higher for F75, and maximum drawdown improves by about 5.8 percentage points, but historical return advantage is concentrated in 2022–2024 and weakens substantially at 50 bp costs.
