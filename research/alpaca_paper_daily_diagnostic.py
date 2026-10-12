"""Read-only daily B0/F75 signal-to-Alpaca diagnostic. Never submits orders."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from alpaca_paper_execution import PAPER_BASE_URL, plan_order, SafetyGateError

DATA_URL = "https://data.alpaca.markets"
SYMBOL = "TQQQ"
NY = ZoneInfo("America/New_York")

class DiagnosticBlocked(RuntimeError):
    pass

def get_json(url, key, secret):
    req = Request(url, headers={
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
        "Accept": "application/json",
        "User-Agent": "Trading-Bot-paper-diagnostic/1.0",
    }, method="GET")
    try:
        with urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise DiagnosticBlocked(f"Alpaca GET returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise DiagnosticBlocked("Alpaca GET failed, timed out, or returned invalid JSON") from None

def read_latest_signal(ledger_path, state_path, now):
    raw = Path(ledger_path).read_bytes()
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != state.get("ledger_sha256"):
        raise DiagnosticBlocked("shadow ledger hash does not match state manifest")
    if state.get("mode") != "SHADOW_ONLY_NO_ORDERS":
        raise DiagnosticBlocked("shadow state mode is not the expected no-orders mode")
    with open(ledger_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise DiagnosticBlocked("shadow ledger is empty")
    if state.get("ledger_rows_total") != len(rows):
        raise DiagnosticBlocked("ledger row count disagrees with state manifest")
    dates = [r.get("date", "") for r in rows]
    if len(set(dates)) != len(dates) or dates != sorted(dates):
        raise DiagnosticBlocked("ledger dates are duplicated or not strictly ordered")
    expected_hash = state.get("canonical_input_sha256")
    if any(r.get("source_canonical_sha256") != expected_hash for r in rows):
        raise DiagnosticBlocked("ledger rows do not share the manifest source hash")
    row = rows[-1]
    session = row.get("date", "")
    try:
        signal_date = datetime.strptime(session, "%Y-%m-%d").date()
        b0 = Decimal(row["b0_signal_close"])
        f75 = Decimal(row["f75_signal_close"])
    except Exception:
        raise DiagnosticBlocked("latest ledger row has invalid date or signal") from None
    if session != state.get("last_observation"):
        raise DiagnosticBlocked("ledger tail date disagrees with state manifest")
    if signal_date >= now.astimezone(NY).date():
        raise DiagnosticBlocked("ledger contains current-session data; refusing incomplete-bar signal")
    if row.get("source_canonical_sha256") != state.get("canonical_input_sha256"):
        raise DiagnosticBlocked("latest signal source hash disagrees with manifest")
    if b0 not in (Decimal("0"), Decimal("1")):
        raise DiagnosticBlocked("B0 signal is not binary")
    if f75 not in (Decimal("0"), Decimal("0.75"), Decimal("1")):
        raise DiagnosticBlocked("F75 signal violates frozen target weights")
    if f75 > b0 or (b0 == 0 and f75 != 0):
        raise DiagnosticBlocked("F75 signal violates B0 eligibility")
    return session, b0, f75, state.get("canonical_input_sha256")

def run(portfolio, ledger, state_path):
    portfolio = portfolio.lower()
    suffix = portfolio.upper()
    key = os.environ.get(f"ALPACA_PAPER_API_KEY_{suffix}", "")
    secret = os.environ.get(f"ALPACA_PAPER_API_SECRET_{suffix}", "")
    if not key or not secret:
        raise DiagnosticBlocked(f"required paper credentials missing for {portfolio}")
    now = datetime.now(timezone.utc)
    session, b0, f75, source_hash = read_latest_signal(ledger, state_path, now)
    account = get_json(PAPER_BASE_URL + "/v2/account", key, secret)
    clock = get_json(PAPER_BASE_URL + "/v2/clock", key, secret)
    positions = get_json(PAPER_BASE_URL + "/v2/positions", key, secret)
    open_orders = get_json(PAPER_BASE_URL + "/v2/orders?" + urlencode({
        "status": "open", "limit": "500", "direction": "desc"
    }), key, secret)
    recent_orders = get_json(PAPER_BASE_URL + "/v2/orders?" + urlencode({
        "status": "all", "limit": "50", "direction": "desc"
    }), key, secret)
    if account.get("status") != "ACTIVE" or account.get("account_blocked") is not False or account.get("trading_blocked") is not False:
        raise DiagnosticBlocked("account is not ACTIVE and unblocked")
    if account.get("currency") != "USD":
        raise DiagnosticBlocked("account currency is not USD")
    if clock.get("is_open") is not True:
        raise DiagnosticBlocked("Alpaca market clock reports market closed; no decision emitted")
    if not isinstance(positions, list) or not isinstance(open_orders, list) or not isinstance(recent_orders, list):
        raise DiagnosticBlocked("broker positions/orders response has unexpected shape")
    if open_orders:
        raise DiagnosticBlocked("unresolved open orders exist; reconcile before planning")
    unexpected = [p.get("symbol", "unknown") for p in positions if p.get("symbol") != SYMBOL]
    if unexpected:
        raise DiagnosticBlocked("unexpected open positions exist; manual reconciliation required")
    position = next((p for p in positions if p.get("symbol") == SYMBOL), None)
    current_qty = Decimal(position["qty"]) if position else Decimal("0")
    if current_qty < 0 or (position and str(position.get("side", "long")).lower() != "long"):
        raise DiagnosticBlocked("short TQQQ position is not allowed")
    trade_response = get_json(DATA_URL + "/v2/stocks/TQQQ/trades/latest?feed=iex", key, secret)
    trade = trade_response.get("trade") if isinstance(trade_response, dict) else None
    if not isinstance(trade, dict) or "p" not in trade or "t" not in trade:
        raise DiagnosticBlocked("latest TQQQ trade response is incomplete")
    try:
        price = Decimal(str(trade["p"]))
        trade_time = datetime.fromisoformat(str(trade["t"]).replace("Z", "+00:00"))
    except Exception:
        raise DiagnosticBlocked("latest TQQQ trade price/timestamp is invalid") from None
    age = (now - trade_time.astimezone(timezone.utc)).total_seconds()
    if not price.is_finite() or price <= 0 or age < -5 or age > 180:
        raise DiagnosticBlocked("latest TQQQ trade is invalid or older than 180 seconds")
    target = b0 if portfolio == "b0" else f75
    intent = plan_order(
        portfolio=portfolio, endpoint=PAPER_BASE_URL,
        account_status=account.get("status"),
        account_blocked=account.get("account_blocked"),
        trading_blocked=account.get("trading_blocked"),
        currency=account.get("currency"), market_is_open=clock.get("is_open"),
        session_date=session, latest_bar_date=session, price=price,
        target_weight=target, current_qty=current_qty,
        open_order_count=len(open_orders), max_bar_age_sessions=0,
    )
    return {
        "status": "READY_FOR_REVIEW",
        "mode": "READ_ONLY_PLAN_NO_SUBMISSION",
        "portfolio": portfolio,
        "symbol": SYMBOL,
        "signal_session": session,
        "signal_source_canonical_sha256": source_hash,
        "b0_target_weight": str(b0),
        "f75_target_weight": str(f75),
        "selected_target_weight": str(target),
        "virtual_allocation_usd": "5000.00",
        "paper_endpoint": PAPER_BASE_URL,
        "account_status": account.get("status"),
        "account_blocked": account.get("account_blocked"),
        "trading_blocked": account.get("trading_blocked"),
        "currency": account.get("currency"),
        "market_is_open": clock.get("is_open"),
        "latest_trade_timestamp": trade_time.isoformat(),
        "latest_trade_age_seconds": round(age, 3),
        "reference_price": str(price),
        "current_tqqq_qty": str(current_qty),
        "open_order_count": len(open_orders),
        "recent_order_count": len(recent_orders),
        "intent": intent.as_dict() if intent else None,
        "note": "Read-only diagnostic. No order was submitted.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portfolio", choices=("b0", "f75"), required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--output", default="paper-diagnostic.json")
    args = parser.parse_args()
    try:
        result = run(args.portfolio, args.ledger, args.state)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, (DiagnosticBlocked, SafetyGateError)) else f"unexpected diagnostic failure ({type(exc).__name__})"
        result = {"status": "BLOCKED", "mode": "READ_ONLY_PLAN_NO_SUBMISSION",
                  "portfolio": args.portfolio, "reason": reason,
                  "note": "No order was submitted."}
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        raise SystemExit(2)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
