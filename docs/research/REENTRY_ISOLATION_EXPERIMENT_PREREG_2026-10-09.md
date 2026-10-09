# Re-entry Isolation Experiment — Preregistration (2026-10-09)

## Purpose
Test the hypothesis that B0's opportunity cost is concentrated in delayed re-entry, without changing its exit rule. This is a preregistration/specification, not a result; no candidate performance is claimed here.

## Frozen control (B0)
- Starting equity: $5,000.
- QQQ signal series: adjusted-close daily return.
- Exit trigger: when QQQ adjusted-close daily return is <= -4.5%, set target exposure to 0 at the next open.
- While defensive, track the lowest QQQ adjusted close from the trigger onward.
- Recovery trigger: QQQ adjusted close >= 1.10 × that running low; restore 100% TQQQ exposure at the next open.
- If another low occurs before recovery, update the running low.
- Use QQQ/TQQQ aligned sessions and the same frozen input files across all candidates.
- Keep actual TQQQ history distinct from any pre-inception synthetic daily-reset 3× QQQ proxy.

## Candidates — change re-entry only
1. **B0:** existing binary exit / +10% recovery rule, unchanged.
2. **R1 immediate:** after an exit, restore 100% exposure at the next open. This is a deliberately aggressive upper-bound counterfactual, not presumed best.
3. **R2 staged:** restore 50% exposure at the next open after QQQ closes at least 5% above the post-trigger running low; restore 100% at the next open after the original +10% threshold. Continue updating the running low until the +5% condition first occurs. Once the +5% threshold has triggered, do not reduce the staged 50% position merely because QQQ subsequently falls; the original +10% full-restoration threshold is measured against the running low as defined by B0. If the running low makes a new low before the +5% trigger, the +5% threshold is recalculated from that low.
4. **No momentum-gated candidate in this pass.** Do not introduce a discretionary or retrospectively selected momentum rule. A later momentum experiment requires a separately preregistered exact formula and independent validation.

## Execution and accounting
- Signals are evaluated using close[t] information only and execute at open[t+1].
- For each session, use prior-position exposure for close[t-1] to open[t], then apply any execution cost at open[t], then use newly executed exposure for open[t] to close[t].
- Use the shared causal execution helper; do not multiply same-day close signals by full-day returns.
- Compare 0, 10, 25, and 50 basis-point one-way exposure-change cost assumptions consistently across every candidate. Also report the no-cost path.
- Reconcile the 0-bps candidate equity against an independently implemented loop on the exact same frozen inputs before interpreting results.

## Required metrics
- Ending balance from $5,000; CAGR using the actual aligned first/last observation dates; maximum drawdown.
- Worst rolling 252-session return and minimum equity / drawdown, including any near-ruin episodes.
- Number of exposure changes, days at 0%, days at 50%, days at 100%, and average exposure.
- Event-level missed rebound gains, losses after re-entry, and per-event terminal-wealth counterfactuals.
- Results separately for actual TQQQ-era data and the synthetic pre-inception proxy; never present the proxy as actual TQQQ performance.
- Cost sensitivity and identical-date buy-and-hold control.

## Interpretation rules fixed before seeing results
- The question is whether earlier exposure improves terminal wealth without an unacceptable increase in drawdown/near-ruin risk; a smaller drawdown alone is not a win if terminal wealth collapses.
- Do not select a winner on ending balance alone. Report the full wealth/risk/exposure trade-off.
- A result on the same sample used to invent the candidate is exploratory. No candidate is promoted without chronological holdout or walk-forward validation.
- Do not tune thresholds against individual known events (2018 Q4, February 2020, June/September 2020, 2022, April 2025). Report those episodes as diagnostics, not as a basis to adjust rules after observing P/L.
- B0 remains the control. No paper/live trading approval follows from this experiment alone.

## Implementation review items before running
1. Confirm R2's state machine is explicit for new lows before the +5% trigger and for drawdowns after the 50% tranche has been entered.
2. Confirm signal-to-next-open indexing for both staged transitions with unit tests.
3. Confirm a 0-bps run reproduces the no-cost equity path.
4. Confirm event ledgers and independent daily equity reconcile on frozen identical inputs.
5. Run tests and inspect the actual workflow result/artifact before recording economic conclusions.

## Audit status
- 2026-10-09: specification recorded before implementing/running candidates.
- No R1/R2 backtest has been run by this document's creation.
