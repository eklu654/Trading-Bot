# Daily market + portfolio email report — 2026-10-14

## Request
Send a short report to `eklu654@gmail.com` each trading weekday around 8:30 a.m., noon, and 3:00 p.m. America/Chicago time. Include overnight/recent market headlines, broad-market snapshot, actual Alpaca paper-account balances/positions/open orders, virtual-ledger state, and the latest executor workflow status.

## Implementation added to main
- `research/daily_market_portfolio_report.py`: read-only reporter. Uses public Yahoo Finance chart data for SPY, QQQ, DIA, IWM, VIX, TLT and GLD; Google News RSS headlines; Alpaca paper API snapshots for B0 and F75; shared virtual ledger state; and GitHub Actions API for the latest executor run.
- `.github/workflows/daily-market-portfolio-email.yml`: schedule candidates cover both Central Daylight Time and Central Standard Time. The script sends only when the actual local Central time is within 20 minutes of 8:30, 12:00, or 15:00. Manual dispatch is non-sending by default.
- `research/test_daily_market_portfolio_report.py`: basic safety tests for schedule labels, missing mail configuration, broker-data failures, and distinguishing the virtual ledger from broker-confirmed positions.
- `.github/workflows/paper-emergency-exit-tests.yml`: extended to compile/test the report and parse the report workflow YAML.

## Important safety properties
- Report code is read-only: it does not place, cancel, replace, or modify orders.
- It reads the **Alpaca paper accounts B0/F75**, not any separate real-money brokerage portfolio.
- Virtual ledger numbers are labeled as not broker-confirmed.
- If market data, headlines, account data, or executor status cannot be retrieved, the report labels that section unavailable rather than inventing values.
- User correction on 2026-10-15: SMTP credentials/keys were already added and the email delivery setup had already been working. The earlier statement that SMTP secrets were missing was not verified and must not be treated as an established blocker. Do not ask the user to add the same keys again.

## Required GitHub Actions secrets
Configure these in repository Settings → Secrets and variables → Actions:
- `REPORT_SMTP_HOST` (for Gmail: `smtp.gmail.com`)
- `REPORT_SMTP_USERNAME` (sender email account)
- `REPORT_SMTP_PASSWORD` (for Gmail, use an App Password if the account supports it; never use or paste a normal account password into chat)
- `REPORT_EMAIL_FROM` (verified sender address)

`REPORT_SMTP_PORT` is optional and defaults to 587. Recipient is configured as `eklu654@gmail.com`. Existing `ALPACA_PAPER_API_KEY_B0`, `ALPACA_PAPER_API_SECRET_B0`, `ALPACA_PAPER_API_KEY_F75`, and `ALPACA_PAPER_API_SECRET_F75` secrets are reused.

## Verification state / next steps
- Source, tests, schedule workflow, and this audit note are committed directly to `main`; the initial implementation began at `7742ba8d6f4ae5128f5a306f1605213113ec9a4a`.
- A standalone test-workflow experiment was invalid because an inline Ruby command contained YAML-sensitive colon syntax. It was removed; the established `research-tests` workflow now runs the report tests and validates the email workflow YAML.
- CI run [38663157512](https://github.com/eklu654/Trading-Bot/actions/runs/38663157512) passed the report safety unit tests, parsed the email workflow YAML successfully, and passed the full existing `pytest -q` suite.
- The report tests and workflow YAML passed in [CI run 38663157512](https://github.com/eklu654/Trading-Bot/actions/runs/38663157512). User confirms the mail keys were already configured and delivery was working before the earlier mistaken blocker claim. This GitHub Actions workflow is intended to run independently of ChatGPT; ChatGPT does not need to remain open. The remaining verification is the latest run/delivery evidence for this specific workflow, not re-entering secrets.
- The initial implementation uses public market quote/news feeds, which can be delayed or unavailable; the email includes quote timestamps and source links. It is an informational report, not a trading signal.


## Context correction — 2026-10-15

The user clarified that the email delivery credentials had already been added and the system was already working. The prior note's claim that SMTP setup was blocking delivery was unsupported; retain the implementation and do not ask for keys again. Focus future work on checking this workflow's scheduled execution and delivery outcome, while preserving the read-only report behavior.
