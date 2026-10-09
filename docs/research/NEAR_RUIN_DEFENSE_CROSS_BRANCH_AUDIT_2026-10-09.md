# Near-Ruin Defense Gate — Cross-Branch Audit (2026-10-09)

Status: documentation-only continuation; no new strategy backtest is claimed.

## Separation of research branches

The authoritative state ledger `docs/project-state-2026-10-07.md` records a separate TQQQ/60-day/Fed branch and invalidates the old $128B/$204.86B synthetic outputs because of look-ahead. Those results must not be merged with the B0 shock/recovery defense gate. They are different hypotheses and result series.

## Causal accounting invariant

B0 is QQQ adjusted-close daily return <= -4.5% exit, executed at the next TQQQ open; re-entry occurs after QQQ closes >= 10% above the post-trigger running low, executed at the next open. For close-to-next-open decisions, the overnight leg into the next open belongs to the previously held position; the intraday leg belongs to the new position. Applying the new state to both legs fails the causal accounting gate.

## Next experiment — preregistration only

Do not launch a broad grid. First audit one candidate timeline using QQQ trailing 60-session return as a context variable for persistent deterioration, without automatically reinstating a Fed-rate exception. The earlier corrected causal Fed/60-day and three-layer architectures failed their prior actual-TQQQ validation and must not be silently resurrected.

Required first artifact: a state/event timeline for dot-com, 2008–09, 2018 Q4, COVID, 2020 June/September, 2022, and April 2025. Record context values, defense activation, B0 exits/re-entries, next-open state, and whether the candidate blocks a B0 recovery. Use only close-available data and next-open execution. Any recovery escape must be fixed before viewing P/L.

Only if the timeline is plausible, run one frozen causal replay versus B0 and actual TQQQ buy-and-hold. Keep actual TQQQ separate from the synthetic pre-inception proxy. Report ending balance, max drawdown, worst rolling 252-session return, exposure time, event ledger, and 0/10/25/50-bp costs. Already-inspected eras are development diagnostics, not untouched confirmation; require chronological holdout/walk-forward validation before promotion.

## Execution status

No new backtest was executed in this continuation. The current GitHub connector surface exposes file/commit operations and known-run job/artifact retrieval, but no workflow-run listing/dispatch action. This is a tooling limitation, not evidence of a passing test. Do not claim the candidate is implemented, run, or successful until a real workflow run and artifact exist.
