# Alpaca ChatGPT Integration Plan — 2026-10-15

## Discovery

Alpaca announced ChatGPT integrations on 2026-10-12:
- **Alpaca Paper Trading** connects to a paper Trading API account and Market Data API; the vendor describes account/market monitoring and simulated order submission.
- **Alpaca Live** is for live-account monitoring and does not submit, modify, or cancel live orders.

References:
- Alpaca announcement: https://alpaca.markets/blog/paper-trading-and-live-portfolio-monitoring-now-available-in-chatgpt-with-alpaca/
- OpenAI Alpaca plugin listing: https://openai.com/business/plugins/alpaca/
- Alpaca MCP server docs: https://docs.alpaca.markets/us/docs/alpaca-mcp-server

The available plugin-management catalog exposed no Alpaca connector ID to install programmatically in this session. This is not proof that the app is unavailable in the ChatGPT interface; availability depends on plan, interface, region, and workspace settings. The user must initiate app installation/authorization in ChatGPT if the app is listed.

## Recommended use in this project

1. Prefer the **Alpaca Paper Trading** app for the two existing paper portfolios. Do not connect the Live app for order testing.
2. Authorize the B0 and F75 paper accounts separately and label each connection/account unambiguously. Do not assume one connection grants access to both accounts.
3. First perform read-only checks: account status, equity/cash/buying power, positions, open orders, and recent fills. Compare returned values to the Alpaca dashboard and the repository's paper-execution ledger.
4. If read-only values reconcile, perform a deliberately small paper-only test order through the established test procedure, then retrieve that exact order by ID and verify status, filled quantity, average fill price, and resulting positions/buying power. An order acknowledgment alone is not proof of a fill.
5. Do not use the ChatGPT app as a substitute for the scheduled Trading-Bot executor. The bot still needs GitHub Actions scheduling, independent API credentials per paper account, idempotent order submission, persisted signal/intent IDs, fill-backed reconciliation, retry limits, and emergency-exit tests.
6. Do not store or paste API secrets into conversation or repository docs. Continue using GitHub Actions secrets for the automated executor.

## Acceptance gates

- App access: user explicitly completes authorization.
- Account identity: B0 and F75 are confirmed as distinct paper accounts.
- Read-only reconciliation: account/position/order information matches Alpaca's dashboard.
- Order lifecycle: a test paper order is traced from submit/acknowledgment through terminal status and, if filled, through fill and position reconciliation.
- Executor safety: duplicate/retried workflow runs cannot create duplicate orders; failures stop closed; emergency-exit behavior is tested independently.
- No real-money order placement is part of this test.

## Scope distinction

The ChatGPT Alpaca app is an operator-side inspection/manual workflow. The Trading-Bot's own API integration remains responsible for unattended strategy execution. These are complementary, not interchangeable.
