# Market Report Email Delivery and Formatting Audit — 2026-10-16

## Summary

The report workflow is configured for three emails on weekdays in America/Chicago: market open (08:30), midday (12:00), and market close (15:00). A successful close email does not prove the open and midday reports were sent.

## Evidence reviewed

- Workflow: `.github/workflows/daily-market-portfolio-email.yml`
- Sender: `research/daily_market_portfolio_report.py`
- Tests: `research/test_daily_market_portfolio_report.py`
- [Oct 16 run 38940607861](https://github.com/eklu654/Trading-Bot/actions/runs/38940607861): scheduled run started 17:33:35Z (12:33 CDT); sender logged `NO_REPORT_SLOT` because it started 33 minutes after noon, outside the old 20-minute window. No email was sent.
- [Oct 16 run 38957694866](https://github.com/eklu654/Trading-Bot/actions/runs/38957694866): sender logged `REPORT_SENT` at 14:49 CDT and classified the report using wall-clock time. The prior combined cron expressions did not identify which UTC candidate triggered.
- [Oct 15 run 38799899790](https://github.com/eklu654/Trading-Bot/actions/runs/38799899790): email delivery failed because SMTP environment values were empty in that run. A later run succeeded, so this is historical evidence, not proof that current secrets are missing.
- On Monday, 2026-10-19, the repository Actions run listing showed no market-report workflow run after Friday, 2026-10-16. As of 15:06Z (10:06 CDT), the expected 13:30Z market-open schedule had not produced a recorded run. This is consistent with the job not being triggered; it is not evidence of an SMTP failure because the sender did not run.

## Root cause and changes

The original sender selected the report title from runner wall-clock time and required it to be within 20 minutes of a target. A delayed run could skip or mislabel a report. Changes made:

1. Split the six UTC cron candidates into separate expressions (three target times, each with daylight/standard-time candidates).
2. Pass `github.event.schedule` into the sender so it resolves the intended slot instead of guessing from runner start time.
3. Validate the candidate against the date's America/Chicago UTC offset. Suppress wrong-DST candidates and runs more than 55 minutes late or 15 minutes early.
4. Reorganized the report into market snapshot, headlines, read-only paper accounts, virtual ledgers, automation status, and data quality.
5. Added a styled HTML alternative while retaining plain-text fallback. The report remains read-only and never places, replaces, or cancels orders.
6. Added tests for delayed-slot labeling, DST candidate rejection, stale-run suppression, and HTML rendering.

## Current operational diagnosis (2026-10-19)

- The workflow file on `main` still contains the six expected weekday cron expressions and passes `GITHUB_EVENT_SCHEDULE` to the sender.
- The two most recent recorded runs for this workflow are still Friday's runs; there is no recorded Monday run at the time checked.
- The Friday close report's sender step completed with `REPORT_SENT`, so SMTP delivery worked on that run.
- The current evidence points first to a missed/disabled schedule trigger, not to a proven SMTP credential problem. The available read-only GitHub Actions listing does not expose the workflow enabled/disabled setting through the connected interface, so that setting still needs direct confirmation in GitHub Actions.
- Do not claim today's email was sent. Do not use a manual dispatch as a delivery test unless the sender has an explicit, safely scoped report-slot override; current manual dispatches do not send by default.

## Verification status and links

- Sender formatting and slot-routing fix: [`17713e57`](https://github.com/eklu654/Trading-Bot/commit/17713e57d026b9170b72bee0029f2fc48a858bc1)
- Six separate cron candidates plus scheduled-expression environment: [`59758c4e`](https://github.com/eklu654/Trading-Bot/commit/59758c4e2751e1849af848baffcb9be0d42bee1e)
- Slot-routing and HTML-layout tests: [`6ce7299b`](https://github.com/eklu654/Trading-Bot/commit/6ce7299b5e51c3dd47d70ce8b43938c57f7a0363); fixture cleanup: [`47d55388`](https://github.com/eklu654/Trading-Bot/commit/47d55388f022d3f29f4333443bb49da3cb78e4f9)
- Focused report tests and YAML validation passed in [run 38969315202](https://github.com/eklu654/Trading-Bot/actions/runs/38969315202), but the repository-wide pytest step was canceled/superseded. Do not label the entire suite passed without a completed passing run.
- No email was manually sent during this audit. No broker orders or account state were changed.

## Operational follow-up

1. In GitHub, open the [market-report workflow](https://github.com/eklu654/Trading-Bot/actions/workflows/daily-market-portfolio-email.yml) and confirm it is enabled.
2. Check whether GitHub recorded the 2026-10-19 scheduled trigger. If it is disabled, re-enable it; if enabled but no run was created, investigate GitHub schedule delivery and consider an independently observable watchdog/alert.
3. For the next open, midday, and close slots, verify the job log contains `REPORT_SENT: intended_slot=...`. A green workflow that logs a skip is not proof of delivery.
