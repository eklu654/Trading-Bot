# Near-Ruin Defense Continuation — Feature Audit and CAGR Fix (2026-10-09)

## Work performed
- Inspected completed workflow run [37917295639](https://github.com/eklu654/Trading-Bot/actions/runs/37917295639), job `audit`, including its full log and artifact `11610381396`.
- The failed-bounce feature audit generated only **9 labeled events** over the actual-TQQQ era: 7 labeled successful, 1 failed, and 1 censored under the fixed outcome definition (+20% before -10%, or -10% before +20%, within 252 sessions).
- Walk-forward sample counts were extremely small: F1 train 1 event (1 successful); F1 test 4 (4 successful); F2 train 5 (5 successful); F2 test 4 (2 successful, 1 failed, 1 censored). These counts do not support fitting or validating a reliable classifier. Apparent feature separation, especially the single failed event, is descriptive only and must not be converted into a rule.
- The only failed label in the printed event table is the 2022-05-05 shock / 2022-06-16 low / 2022-07-19 recovery decision; the April 2025 event was labeled successful by this specific 252-session first-touch definition, despite being a damaging exit in the portfolio event counterfactual. This distinction is important: outcome labels are not the same as the event's portfolio counterfactual contribution.
- Inspected `research/failed_bounce_robustness.py`, `research/audit_failed_bounce_canonical_independent.py`, and `research/causal_execution.py`. Confirmed that close-to-next-open accounting must use the previously held weight for the overnight leg and the newly executed weight for the intraday leg.
- Fixed the independent audit's CAGR denominator in commit `28d17bfbeb5b48feb10c0c3b7d3c8a8903c057a6`: it now annualizes over the actual first/last aligned data dates, matching the primary robustness script's convention, and checks date/equity length and positive interval. This corrects a reporting mismatch; it does not change the strategy signal, equity path, or economic result.

## Interpretation
The completed feature audit is **not** evidence that a robust event classifier exists. There are too few independent events and only one failure label. A high-dimensional feature table with one failed observation invites severe overfit. Do not use its single-failure means, rank features, optimize thresholds, or claim walk-forward validation.

The event-level counterfactual results and the event-outcome labels answer different questions:
- outcome label: what QQQ did after the recovery decision under a fixed future first-touch definition;
- portfolio counterfactual: how changing one defense interval affected the strategy's final wealth curve.
These must remain separate in reporting.

## Required next actions
1. Allow the push-triggered independent-audit workflow from the CAGR fix to finish; inspect its conclusion and logs.
2. Confirm both audit implementations report CAGR using the same actual aligned first/last timestamps and that ending equity/max drawdown remain reconciled. Do not claim success until the run artifact/log confirms this.
3. Before any new candidate replay, generate the event-state timeline for the predeclared contexts (dot-com and 2008–09 synthetic proxy separately; actual TQQQ era for 2010–present), including only close-known signals and next-open state.
4. Keep the canonical B0 rule frozen: QQQ adjusted-close daily return <= -4.5% exits TQQQ at next open; re-entry after QQQ closes >= 10% above the post-trigger running low, executed next open.
5. Do not add a recovery escape based on inspecting P/L. Predeclare it before the replay. If the feature timeline cannot distinguish beneficial 2018 Q4 / February 2020 / 2022 protection from damaging June/September 2020 and April 2025 exits without look-ahead, reject the candidate.
6. Any synthetic pre-2010 analysis must be labeled as a hypothetical daily-reset 3x QQQ proxy, not actual TQQQ history. Require chronological holdout/walk-forward validation before promotion.

## Current disposition
- B0 remains the research control; no defense overlay is promoted.
- The feature audit is underpowered and descriptive, not a validated predictor.
- No paper or live trading approval.
- This note documents analysis and a small audit-metric fix; the triggered workflow must be checked separately.


## Follow-up code audit — transaction-cost application

A second source review found that `research/failed_bounce_robustness.py` estimated cost stress by subtracting the cost fraction from the already-compounded daily return. That is not the exact modeled execution order. The shared `next_open_cost_equity` implementation applies the overnight return on the prior position, then the transaction cost at the open, then the intraday return on the newly executed position.

The robustness script now uses that exact equity helper and reconstructs adjusted overnight/intraday legs for its 0/5/10/25/50-bps table. Commit: `5981710d8ff6a542aa9991175b126fd3bf0e35fa`.

This is a cost-accounting correction only; it does not change the B0 signal or no-cost return path. Any prior failed-bounce cost table is superseded by the workflow artifact produced from this commit. Wait for the corresponding workflow and compare its 0-bps result with the headline path before accepting the cost table. The helper's 0-bps output should reconcile to the strategy equity path within numerical tolerance; if it does not, investigate before further interpretation.


## Validation results from commit `5981710d8ff6a542aa9991175b126fd3bf0e35fa`

- Robustness workflow [37917831852](https://github.com/eklu654/Trading-Bot/actions/runs/37917831852) completed successfully and uploaded artifact `11610696744`.
- The corrected 0-bps cost-equity path exactly reproduced the primary no-cost headline: final balance about **$4,040,315**, CAGR **49.4874%**, maximum drawdown **-73.5343%**. This is the key consistency check for the cost helper.
- Updated exact next-open cost sensitivity: 5 bps **$4,002,104**; 10 bps **$3,964,236**; 25 bps **$3,852,657**; 50 bps **$3,673,278**. The rule remains economically sensitive to friction at these high terminal wealth levels; cost modeling should remain explicit.
- Independent audit workflow [37917832008](https://github.com/eklu654/Trading-Bot/actions/runs/37917832008) completed successfully after the CAGR fix. It reports CAGR **49.4874%** and max drawdown **-73.5343%**, matching the primary script's annualization and drawdown. Its final balance was about **$4,040,311**, roughly $4 below the primary script. This tiny residual is not yet a same-input cross-script reconciliation: the independent audit downloads its own data, while the canonical same-input workflow freezes its own one-download file. Do not describe the two different downloads as exact terminal-equity agreement.
- Canonical same-input reconciliation [37917832059](https://github.com/eklu654/Trading-Bot/actions/runs/37917832059) also completed successfully. Its own shared-helper and independent-loop implementations use one frozen input and assert event-ledger, daily-return and equity agreement. This verifies that workflow's internal engines; it does not by itself eliminate the $4 difference between separately downloaded robustness and independent-audit data.

## Workflow scheduling note
Several commits in quick succession caused push-triggered workflow fan-out. A research-tests run on an earlier commit was cancelled while later commit runs queued; this is not a test failure, but neither is it a pass. The latest research-tests run on commit `420429a12ec69f159aee964ba7a9aeb8e02619a0` must reach a completed conclusion before the code changes are called fully test-verified. Avoid further documentation-only commits until that run is checked, to reduce unnecessary duplicate workflow churn.
