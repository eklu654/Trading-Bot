# QQQ Shock/Recovery Baseline — Structural Robustness Plan

Status: **active research plan**. This plan uses the ~$4.04M actual-TQQQ QQQ shock/recovery strategy as the working baseline, as explicitly authorized by the user. The aim is not to rediscover the baseline; it is to find its failure modes and test whether predeclared structural features can address prolonged bears without giving away V-shaped recoveries.

## A. Baseline identity

Reference the frozen rule in FAILED_BOUNCE_CANONICAL_STRATEGY_SPEC.md: QQQ adjusted-close daily return <= -4.5% triggers zero TQQQ exposure beginning next open; stay defensive until QQQ's adjusted close is at least 10% above the post-shock running low; re-enter next open; otherwise 100% TQQQ. Use $5,000 initial capital and the same aligned dates as buy-and-hold.

Reference output: approximately $4.04M strategy versus $2.095M TQQQ buy-and-hold over the recorded live-TQQQ window, nine events. The result is a working research anchor, not a promise. Do not block new research on the remaining frozen-input curve reconciliation.

## B. What is already known

- The simple shock/recovery rule materially improves the reported terminal balance versus TQQQ buy-and-hold in the tested window.
- The rule is not a full structural regime detector: a gradual decline without a QQQ daily loss of 4.5% may not trigger it.
- It may miss part of a V-shaped rebound because re-entry waits for +10% from the low; measure this explicitly.
- It may produce false-positive exits during modern bull-market corrections; the 2020 June/September and 2025 April event counterfactuals were not uniformly beneficial.
- A previously tested Fed + macro + 200-DMA composite was historically effective on a synthetic pre-2010 leveraged path but over-defensive in 2010–2019 and 2020–2026. Do not promote that composite as the answer or launch another broad DMA-length search.
- The Fed layer remains a relevant hypothesis. The research question is whether a narrow structural trigger can add protection to the $4.04M baseline without suppressing ordinary recoveries.
- The old approximately $3.3M rule included an additional anti-fakeout concept but is not the same rule as the $4.04M simple shock/recovery candidate. Keep their identities separate unless the exact extra rule is recovered.

## C. Experiment order

### Experiment 1 — Baseline stress scorecard (no strategy changes)

Produce an event/period report for the frozen baseline and buy-and-hold. Required periods:

1. COVID acute crash and V-shaped recovery (2020-02 through 2020-07).
2. 2022 tightening-driven decline and recovery (2022 calendar year, with the two recorded shock events shown separately).
3. 2018 Q4 selloff and recovery.
4. 2020 June and September corrections (false-positive/opportunity-cost checks).
5. 2025 April correction.
6. Objective rolling 12-month windows selected by worst QQQ drawdown/return, defined mechanically across the full sample rather than selected from strategy results.

For each period report strategy and buy-and-hold total return, maximum drawdown, start/end wealth, time in cash, exits/re-entries, exit delay, re-entry delay, and rebound return missed while defensive. Use common dates and state whether the local period begins with inherited position/equity or is independently reset; do not mix these accounting conventions.

### Experiment 2 — Slow-bear failure audit

Find periods in which QQQ has a sustained drawdown but never triggers a -4.5% daily loss near the start. Define this mechanically using QQQ drawdown from a rolling peak, not by looking at the TQQQ outcome. Measure how long the baseline remains 100% exposed before the first shock, and how much additional leveraged loss accrues.

Use the 2000–2002 dot-com episode as a signal-regime case study only. TQQQ did not exist; any leveraged portfolio path is synthetic. Do not present it as actual TQQQ performance.

### Experiment 3 — Frozen structural feature family

Keep the feature definitions and source families already used in the repository fixed while testing them as an overlay on the shock/recovery baseline. Do not perform a fresh, unrestricted indicator search.

Candidate families to evaluate separately before any combination:

- Fed lifecycle: the existing live-safe Fed state, including the documented TIGHTENING_PAUSED state. Use only policy actions known by the decision date; never use the eventual final hike date as a real-time signal.
- Market structure: the existing 200-DMA relationship as a state feature, not a new DMA-length sweep.
- Macro regime: the existing frozen macro states MACRO_DETERIORATION, MACRO_CRISIS, and STRUCTURAL_EXPANSION; audit their data publication timing and revisions before allowing live use.

Start with diagnostics: on each day, show whether the feature would have identified a structurally dangerous regime before or during 2022 and whether it would have activated during COVID's rapid recovery and the 2020/2025 false-positive events. Then evaluate one frozen overlay at a time against the baseline.

Do not immediately restore the full prior composite. Its recorded modern-period opportunity cost was too high. Do not search additional DMA lengths or re-entry delays; the prior research explicitly closed those searches.

### Experiment 4 — Overlay candidates, frozen before holdout

Candidate A: baseline only (control).

Candidate B: baseline plus a structural slow-bear state, activated only when QQQ is below its existing 200-DMA AND the existing Fed lifecycle state is TIGHTENING_PAUSED. This is a narrow test of the documented Fed × market interaction, not a claim it is the correct rule.

Candidate C: baseline plus the already-frozen macro deterioration/crisis state, evaluated separately from Candidate B.

Candidate D: combine B and C only if at least one individual feature has shown incremental value in the development segment. Entry/exit persistence must be specified before holdout; do not add a condition after seeing 2022 results.

For every candidate, use the same close-to-next-open execution convention, same price fields, same costs, same dates, and same $5,000 starting capital. Baseline rule remains unchanged beneath the overlay. Report if overlay supersedes or pauses the baseline, and exactly when.

### Experiment 5 — Chronological evaluation

- Development: earliest available actual-TQQQ segment for feature sanity and initial choices.
- Validation: a later segment used to choose among the small frozen candidate set.
- Final live-TQQQ holdout: the latest untouched chronological segment. Do not revise rules after viewing it; if revised, it becomes development data and a new future holdout is required.
- The 2022 episode can be used as development for hypothesis formation only if explicitly labelled; it cannot then also be counted as independent confirmation. Seek earlier independent Fed tightening cycles, while recognizing they are few and differ structurally.
- Use a separate synthetic 1999–2009 test only after the daily-reset 3x proxy is validated on live TQQQ dates. Report proxy assumptions and sensitivity separately from actual-TQQQ results.

## D. Decision gate

An overlay advances only if it:

1. Improves prolonged-bear outcomes in the predeclared development/validation regimes;
2. Preserves most of the baseline's COVID V-shaped recovery capture and does not repeatedly exit ordinary corrections;
3. Does not materially damage long-run terminal wealth versus the $4.04M baseline in the untouched chronological holdout;
4. Survives cost and small-threshold sensitivity checks without a single lucky episode carrying the result;
5. Uses only data actually available at each signal close and trades no earlier than next open.

Do not select on drawdown alone. The user's primary objective remains substantially higher ending wealth than the benchmark, with drawdown and stress survival used to diagnose unacceptable failure modes.

## E. Mandatory audit fields

Every run records: git commit; workflow ID and conclusion; rule ID; input data hash; requested and actual date ranges; signal and execution timestamps; final wealth; CAGR based on actual aligned dates; max drawdown; worst rolling 12-month return; average exposure; event count; cost model; per-period outcomes; and links to raw event/daily curve artifacts.

Every conclusion must be tagged WORKING, SUPPORTED, REJECTED, or UNRESOLVED with a short reason. Never silently overwrite old results.

## F. Next action

Implement Experiment 1 first, without changing the baseline. Then inspect slow-bear trigger misses. Only after those diagnostics should the Fed and macro overlays be tested. Keep the original ~$4.04M baseline as the fixed comparator in every run.