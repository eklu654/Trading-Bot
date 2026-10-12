"""Read-only Alpaca reconciliation for fill-backed B0/F75 virtual state.

This program uses GET requests only. It never submits, replaces, or cancels orders.
State is written to a local path; the workflow separately commits it to the
paper-execution-ledger branch only after both portfolio reconciliations pass.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, date, timedelta
from hashlib import sha256
from decimal import Decimal
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from paper_virtual_portfolio import (
    apply_fills, mark_to_market, validate_state, state_json, reconcile_order,
    complete_terminal_intent, LedgerSafetyError,
)

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
NY = ZoneInfo("America/New_York")
SYMBOL = "TQQQ"

class SyncBlocked(RuntimeError):
    pass

def get_json(url, key, secret, allow_404=False):
    request = Request(url, headers={
        "APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret,
        "Accept": "application/json", "User-Agent": "Trading-Bot-paper-ledger-sync/1.0",
    }, method="GET")
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        raise SyncBlocked(f"Alpaca GET returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise SyncBlocked("Alpaca GET failed, timed out, or returned invalid JSON") from None

def iso_dt(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)

def latest_completed_bar(key, secret, now):
    start = (now.astimezone(NY).date() - timedelta(days=14)).isoformat() + "T00:00:00Z"
    end = (now.astimezone(NY).date() + timedelta(days=1)).isoformat() + "T00:00:00Z"
    query = urlencode({"timeframe":"1Day","start":start,"end":end,"limit":"100",
                       "adjustment":"raw","feed":"iex"})
    result = get_json(DATA_URL + "/v2/stocks/TQQQ/bars?" + query, key, secret)
    bars = result.get("bars") if isinstance(result, dict) else None
    if not isinstance(bars, list) or not bars:
        raise SyncBlocked("Alpaca returned no daily TQQQ bars")
    today = now.astimezone(NY).date()
    completed = []
    for bar in bars:
        try:
            d = date.fromisoformat(str(bar["t"])[:10])
            close = Decimal(str(bar["c"]))
        except Exception:
            raise SyncBlocked("daily TQQQ bar has invalid date or close") from None
        if d <= today and close.is_finite() and close > 0:
            completed.append((d, close))
    if not completed:
        raise SyncBlocked("no completed daily TQQQ bar is available")
    return max(completed, key=lambda x: x[0])

def run_sync(portfolio, state_path, report_path):
    portfolio = portfolio.lower()
    suffix = portfolio.upper()
    key = os.environ.get(f"ALPACA_PAPER_API_KEY_{suffix}", "")
    secret = os.environ.get(f"ALPACA_PAPER_API_SECRET_{suffix}", "")
    if not key or not secret:
        raise SyncBlocked(f"required paper credentials missing for {portfolio}")
    state_path = Path(state_path)
    original_state_text = state_path.read_text(encoding="utf-8")
    state = json.loads(original_state_text)
    validate_state(state)
    if state.get("portfolio") != portfolio:
        raise SyncBlocked("virtual ledger portfolio identity mismatch")
    now = datetime.now(timezone.utc)
    account = get_json(PAPER_URL + "/v2/account", key, secret)
    clock = get_json(PAPER_URL + "/v2/clock", key, secret)
    if account.get("status") != "ACTIVE" or account.get("account_blocked") is not False or account.get("trading_blocked") is not False:
        raise SyncBlocked("account is not ACTIVE and unblocked")
    if account.get("currency") != "USD":
        raise SyncBlocked("account currency is not USD")
    account_id=str(account.get("id") or "")
    if not account_id:
        raise SyncBlocked("paper account identity is missing")
    fingerprint=sha256(account_id.encode("utf-8")).hexdigest()
    if state.get("broker_account_fingerprint") and state["broker_account_fingerprint"] != fingerprint:
        raise SyncBlocked("paper account identity does not match durable virtual ledger")
    if clock.get("is_open") is True:
        result = {"status":"SKIPPED_MARKET_OPEN","portfolio":portfolio,
                  "mode":"READ_ONLY_RECONCILIATION_NO_ORDERS",
                  "note":"Market is open; scheduled close reconciliation skipped safely."}
        Path(report_path).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        return result

    positions = get_json(PAPER_URL + "/v2/positions", key, secret)
    open_orders = get_json(PAPER_URL + "/v2/orders?" + urlencode(
        {"status":"open","limit":"500","direction":"desc"}), key, secret)
    recent_orders = get_json(PAPER_URL + "/v2/orders?" + urlencode(
        {"status":"all","limit":"100","direction":"desc"}), key, secret)
    if not isinstance(positions, list) or not isinstance(open_orders, list) or not isinstance(recent_orders, list):
        raise SyncBlocked("broker positions/orders response has unexpected shape")
    if any(p.get("symbol") != SYMBOL for p in positions):
        raise SyncBlocked("unexpected broker position; manual reconciliation required")
    position = next((p for p in positions if p.get("symbol") == SYMBOL), None)
    broker_qty = Decimal(str(position["qty"])) if position else Decimal("0")
    if broker_qty < 0 or (position and str(position.get("side","long")).lower() != "long"):
        raise SyncBlocked("broker has a short TQQQ position")

    pending = state.get("pending_intent")
    if pending:
        broker_order = get_json(
            PAPER_URL + "/v2/orders:by_client_order_id?" + urlencode(
                {"client_order_id":pending["client_order_id"]}),
            key, secret, allow_404=True)
        state = reconcile_order(state, broker_order)
        pending = state.get("pending_intent")
        if any(o.get("client_order_id") != pending["client_order_id"] for o in open_orders):
            raise SyncBlocked("unexpected open order alongside staged intent")
    elif open_orders:
        raise SyncBlocked("unresolved open order exists without a staged virtual-ledger intent")

    used = set(state.get("used_client_order_ids", []))
    for order in recent_orders:
        cid = str(order.get("client_order_id") or "")
        if cid.startswith("tb-") and cid not in used:
            raise SyncBlocked("broker has a bot-tagged order absent from the durable ledger")

    fill_start = state.get("fill_history_start")
    if not fill_start:
        raise SyncBlocked("virtual ledger has no fill-history baseline")
    activity_url = PAPER_URL + "/v2/account/activities/FILL?" + urlencode({
        "after":fill_start, "direction":"asc", "page_size":"100"
    })
    activities = get_json(activity_url, key, secret)
    if not isinstance(activities, list):
        raise SyncBlocked("fill activity response has unexpected shape")
    if len(activities) >= 100:
        raise SyncBlocked("fill activity page limit reached; pagination required before reconciliation")
    baseline = iso_dt(fill_start)
    fills = []
    for activity in activities:
        try:
            if iso_dt(activity["transaction_time"]) < baseline:
                continue
            fills.append({"id":activity["id"], "symbol":activity["symbol"],
                          "side":activity["side"], "qty":activity["qty"],
                          "price":activity["price"]})
        except Exception:
            raise SyncBlocked("fill activity is missing required fields") from None
    old_fill_count = len(state["processed_fill_ids"])
    state = apply_fills(state, fills)
    applied = len(state["processed_fill_ids"]) - old_fill_count
    if abs(Decimal(state["qty"]) - broker_qty) > Decimal("0.001"):
        raise SyncBlocked("broker TQQQ quantity does not reconcile to unique fill activities")

    if state.get("pending_intent"):
        broker_order = get_json(
            PAPER_URL + "/v2/orders:by_client_order_id?" + urlencode(
                {"client_order_id":state["pending_intent"]["client_order_id"]}),
            key, secret, allow_404=True)
        if broker_order is None:
            if state["pending_intent"].get("submission_state") == "REJECTED":
                state = complete_terminal_intent(
                    state, broker_qty=str(broker_qty), broker_status="rejected")
            else:
                state = reconcile_order(state, None)
        else:
            status = str(broker_order.get("status","unknown")).lower()
            if status in ("filled","rejected","canceled","expired"):
                state = complete_terminal_intent(
                    state, broker_qty=str(broker_qty), broker_status=status)
            else:
                state = reconcile_order(state, broker_order)

    if state.get("pending_intent") is None:
        session, close = latest_completed_bar(key, secret, now)
        if state.get("mark_date") and session.isoformat() < state["mark_date"]:
            raise SyncBlocked("latest completed bar predates virtual ledger mark")
        state = mark_to_market(state, session.isoformat(), close)

    validate_state(state)
    serialized = state_json(state) + "\n"
    changed = serialized != original_state_text
    if changed:
        state_path.write_text(serialized, encoding="utf-8")
    result = {
        "status": "SYNCED" if changed else "NO_CHANGE",
        "mode": "READ_ONLY_RECONCILIATION_NO_ORDERS",
        "portfolio": portfolio, "symbol": SYMBOL,
        "account_status": account.get("status"), "currency": account.get("currency"),
        "market_is_open": clock.get("is_open"),
        "open_position_count": len(positions), "open_order_count": len(open_orders),
        "recent_order_count": len(recent_orders), "fill_activities_returned": len(activities),
        "new_fill_ids_applied": applied, "cash": state["cash"], "qty": state["qty"],
        "virtual_equity": state["equity"], "mark_date": state["mark_date"],
        "mark_price": state["mark_price"],
        "pending_submission_state": (state.get("pending_intent") or {}).get("submission_state"),
        "state_changed": changed, "paper_endpoint": PAPER_URL,
        "note": "GET-only reconciliation. No order was submitted, replaced, or canceled.",
    }
    Path(report_path).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--portfolio", choices=("b0","f75"), required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--report", required=True)
    args=parser.parse_args()
    try:
        result=run_sync(args.portfolio,args.state,args.report)
    except Exception as exc:
        result={"status":"BLOCKED","mode":"READ_ONLY_RECONCILIATION_NO_ORDERS",
                "portfolio":args.portfolio,
                "reason":str(exc) if isinstance(exc,(SyncBlocked,LedgerSafetyError)) else f"unexpected sync failure ({type(exc).__name__})",
                "note":"No broker order was submitted."}
        Path(args.report).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))
        raise SystemExit(2)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
