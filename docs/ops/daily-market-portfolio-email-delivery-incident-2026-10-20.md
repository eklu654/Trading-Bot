# Daily Market + Portfolio Email — Delivery Incident Notes

Updated: 2026-10-20 UTC

## Confirmed findings
- Workflow: `.github/workflows/daily-market-portfolio-email-recovery.yml`
- Report script: `research/daily_market_portfolio_report.py`
- The workflow's GitHub Actions runs showed `success`, but that did **not** mean an email was sent: the script deliberately exited successfully on `REPORT_SKIPPED`.
- Run [39333001879](https://github.com/eklu654/Trading-Bot/actions/runs/39333001879) started at 2026-10-19 22:10 UTC and logged `GITHUB_EVENT_SCHEDULE: 0 18 * * 1-5`, then skipped because that cron belongs to the other daylight-saving offset. At that point Central time was 17:10 CDT.
- Run [39339948517](https://github.com/eklu654/Trading-Bot/actions/runs/39339948517) used the correct CDT close candidate `0 20 * * 1-5`, but GitHub started it 191 minutes late; the old 55-minute cutoff suppressed it. The six-hour allowance directly addresses this observed failure.
- Run [39345321017](https://github.com/eklu654/Trading-Bot/actions/runs/39345321017) logged `GITHUB_EVENT_SCHEDULE: 0 21 * * 1-5` and skipped for the same DST-offset reason at 19:03 CDT.
- The schedule recovery workflow has six UTC cron candidates to cover CDT/CST, but delayed or mismatched candidates can complete as green runs without sending an email.

## Changes committed to main
- Commit `660301e`: increase the allowed lateness for a matching schedule candidate from 55 minutes to 360 minutes, to tolerate GitHub Actions scheduling delays while still suppressing reports delayed more than six hours.
- Commit `c0fa864`: an intentional `workflow_dispatch` now sends a clearly titled “Manual market update” email instead of exiting successfully without sending.

## Still to verify
- A run must log `REPORT_SENT` and the recipient must confirm delivery. A green Actions status alone is not proof of delivery.
- No manual dispatch was triggered during this investigation; the GitHub connector available here supports read-only fetch for workflow resources and does not expose an Actions-dispatch operation.
- If the next matching scheduled run still fails to send, inspect its `REPORT_SKIPPED` / `REPORT_FAILED_CLOSED` / `REPORT_SENT` line and address the specific cause.
