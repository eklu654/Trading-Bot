# Resend Market & Portfolio Digest — implementation audit

Date: 2026-10-15
Branch: `ops/resend-market-portfolio-digest`
Status: implementation and unit tests pass; **not yet merged and email delivery not yet verified**.

## Scope

- Added `research/market_portfolio_digest.py`, a read-only digest builder and Resend API sender.
- Added `research/test_market_portfolio_digest.py` (8 unit tests).
- Added `.github/workflows/market-portfolio-email-digest.yml`.
- Reports include SPY/QQQ latest trade and prior-close comparison, Alpaca news headlines when available, both B0/F75 paper account equity/cash/buying power, positions and unrealized P/L, open orders, and active emergency-exit latch snapshots from the shared ledger.
- The digest code does not submit, cancel, or modify broker orders. It uses read-only Alpaca account/data endpoints and Resend's email API.
- A broker-data failure is included in the report as a data-quality warning; a report is still sent if Resend is configured, even if both broker snapshots are unavailable.
- Non-trading dates are skipped after the Alpaca calendar check. When news or quote data is unavailable, the report says so instead of fabricating information.

## Scheduling / daylight saving

GitHub Actions cron uses UTC. Workflow schedules both seasonal UTC candidates and the script checks the actual `America/Chicago` wall clock before sending:
- Market open: 8:35 AM CT
- Midday: 12:00 PM CT
- Market close: 3:05 PM CT

The UTC trigger alternatives are 13:35/14:35, 17:00/18:00, and 20:05/21:05, weekdays. The non-matching seasonal twin is skipped. The local-time match allows up to 40 minutes of scheduler delay; GitHub scheduled runs can still be delayed or dropped.

Manual workflow dispatch has a boolean `send_test_email` input. It defaults to false; setting it true sends a clearly labeled TEST email. Push events run unit tests only and never send email.

## Required GitHub Actions secrets

Set these in the repository's **Settings → Secrets and variables → Actions → New repository secret**:
- `RESEND_API_KEY`: the Resend API key (never commit or paste into chat).
- `RESEND_FROM_EMAIL`: sender address authorized by Resend. Prefer an address on a domain verified in Resend.
- `ALERT_EMAIL`: destination inbox.

The existing Alpaca secrets are also used:
- `ALPACA_PAPER_API_KEY_B0`
- `ALPACA_PAPER_API_SECRET_B0`
- `ALPACA_PAPER_API_KEY_F75`
- `ALPACA_PAPER_API_SECRET_F75`

Do not put secrets in workflow YAML, repo files, command-line arguments, or logs. A successful Resend HTTP acceptance confirms the provider accepted the email request, not that it reached the inbox. Delivery must be verified with the explicit test-email dispatch after secrets are configured.

## Verification / audit

- First test run [38685377834](https://github.com/eklu654/Trading-Bot/actions/runs/38685377834) caught one fixture assertion mismatch (case-only wording); fixed the test rather than weakening report behavior.
- [38685413554](https://github.com/eklu654/Trading-Bot/actions/runs/38685413554) passed after the fixture fix.
- [38685452850](https://github.com/eklu654/Trading-Bot/actions/runs/38685452850) passed after the final report behavior updates, including compilation and all 8 unit tests.
- These were push-triggered test-only runs. No email was sent and no Resend API key was needed for them.

## Next steps / gate

1. Review and merge the PR.
2. Add the three Resend secrets in GitHub settings; confirm the sender address is authorized by Resend.
3. Run the workflow manually with `send_test_email=true` and verify the email is received at the intended inbox.
4. Observe the next scheduled run and inspect its sanitized logs for `EMAIL_ACCEPTED_BY_RESEND`, report slot, portfolio count, and data error count.
5. Verify one full open/midday/close cycle before treating delivery as reliable.

No API key value is recorded in this audit. The service has not yet been configured or delivery verified.
