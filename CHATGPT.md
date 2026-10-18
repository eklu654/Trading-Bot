# ChatGPT Repository Working Guidelines

These guidelines complement the repository's existing documentation. Prioritize correctness, safe execution, and meaningful progress without unnecessary interruptions.

## Think Before Coding
- Inspect relevant code, tests, and repository guidance before editing.
- Ask a focused question when ambiguity materially affects correctness, safety, or scope.
- For low-risk, reversible details, state a reasonable assumption and proceed.
- Prefer the simplest approach that meets the goal; explain important tradeoffs.

## Simplicity First
- Make the smallest complete change that solves the problem.
- Avoid unrequested features, speculative abstractions, and unnecessary configurability.
- Retain validation, logging, and fail-safe behavior for realistic failures, especially in scheduled workflows, external services, market data, and trading.

## Surgical Changes
- Keep diffs focused; avoid unrelated refactoring and formatting churn.
- Match repository conventions unless there is a concrete reason to change them.
- Remove code made obsolete by your changes, but do not silently remove unrelated code.
- Review the diff for unintended changes before committing.

## Goal-Driven Execution
- Define observable success criteria and verify them with evidence.
- Reproduce bugs with tests where practical, then verify the fix.
- Continue through independent, safe steps without repeatedly asking permission.
- Distinguish focused tests from the full suite, workflow success from actual delivery, and preflight checks from confirmed broker actions.
- Never claim a test, workflow, email, order, or other external action succeeded without evidence.

## Trading-Bot Safety and Research Integrity
- Keep trading paper-only unless the user explicitly authorizes otherwise. Do not place, cancel, or modify orders without explicit authorization.
- Keep B0 frozen during experimental strategy evaluation, and keep B0 and F75 paper accounts separate.
- Treat account access, preflight checks, submitted orders, fills, and reconciled positions as distinct states.
- Record assumptions, data windows, benchmarks, limitations, and meaningful research results.
- Do not fabricate ETF history before inception. Clearly label synthetic proxies and their limitations.
- Consider catastrophic-loss and near-ruin risks; backtest results do not guarantee future performance.

## Completion and Audit Trail
- A task is complete when the requested change and its relevant checks are verified, not merely when code is written or committed.
- Summarize important changes, commit links, test outcomes, and remaining uncertainty.
- Keep repository notes concise and update relevant operational or research notes when changes affect future work.
- Prefer safe targeted tests over test emails, consequential external actions, or broker-state changes.
