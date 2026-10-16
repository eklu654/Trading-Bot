# Market Report Email Delivery and Formatting Audit — 2026-10-16

## Summary

The report workflow is configured for three emails on weekdays in America/Chicago: market open (08:30), midday (12:00), and market close (15:00). The market-close email received on 2026-10-16 does not prove the other two reports were sent.

## Evidence reviewed

- Workflow: `.github/workflows/daily-market-portfolio-email.yml`
- Sender: `research/daily_market_portfolio_report.py`
- Tests: `research/test_daily_market_portfolio_report.py`
- [Oct 16 run 38940607861](https://github.com/eklu654/Trading-Bot/actions/runs/38940607861): scheduled run started 17:33:35Z (12:33 CDT); sender logged `NO_REPORT_SLOT` because it started 33 minutes after noon, outside the old 20-minute window. No email was sent.
- [Oct 16 run 38957694866](https://github.com/eklu654/Trading-Bot/actions/runs/38957694866): sender logged `REPORT_SENT` at 14:49 CDT and classified the report using wall-clock time. The workflow's previous combined cron expressions did not identify which UTC candidate had triggered, so the run metadata available in the logs cannot establish whether this was a delayed close trigger or a delayed earlier trigger.
- [Oct 15 run 38799899790](https://github.com/eklu654/Trading-Bot/actions/runs/38799899790): email sending failed because `REPORT_SMTP_HOST`, `REPORT_SMTP_USERNAME`, `REPORT_SMTP_PASSWORD`, and `REPORT_EMAIL_FROM` were empty in that run. Later runs succeeded, so this was a historical configuration failure, not evidence those secrets are currently missing.

## Root cause

The old sender selected the report title from the time the runner happened to start and required it to be within 20 minutes of a target. GitHub scheduled runs can start late. That made the midday run at 12:33 CDT skip, and a delayed event could be labeled as a different slot if it happened to start near another report time. A successful Actions run can therefore mean “the script intentionally skipped” rather than “an email was sent.”

## Changes made

1. Split the six UTC cron candidates into separate expressions (three target times, each with daylight/standard-time candidates).
2. Pass `github.event.schedule` into the sender so it can resolve the intended report slot rather than guess from runner start time.
3. Validate the candidate against the date's America/Chicago UTC offset. Suppress wrong-DST candidates and runs more than 55 minutes late or 15 minutes early; stale delayed reports should be skipped rather than mislabelled.
4. Reorganized report headings and section order: market snapshot, top headlines, read-only paper accounts, virtual ledgers, automation status, and data quality.
5. Added a styled HTML alternative while retaining a plain-text fallback. The report remains read-only and never places, replaces, or cancels orders.
6. Added tests for delayed-slot labeling, DST candidate rejection, stale-run suppression, and HTML rendering.

## Verification status

- Code and workflow changes are committed to `main`.
- The repository's `research-tests` workflow was triggered by the commits. Final test results must be checked in [run 38969276346](https://github.com/eklu654/Trading-Bot/actions/runs/38969276346) and the latest follow-up [run 38969315202](https://github.com/eklu654/Trading-Bot/actions/runs/38969315202); do not treat queued/in-progress runs as passed.
- No email was manually sent during this audit, and no broker orders or account state were changed.

## Remaining operational caveat

The new guard makes slot identity more reliable but cannot guarantee that GitHub Actions will start every scheduled job. Monitor the next open, midday, and close runs and confirm each log contains `REPORT_SENT: intended_slot=...`; a green workflow that logs `REPORT_SKIPPED` is not a delivered report.
