#!/usr/bin/env python3
"""Send a scheduled market and Alpaca paper-portfolio digest through Resend.

The workflow invokes this script only on the UTC cron triggers; this script maps
those triggers to Central time and skips the non-matching daylight-saving twin.
It never submits, cancels, or modifies brokerage orders.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
ET = ZoneInfo("America/New_York")
ALPACA_PAPER = "https://paper-api.alpaca.markets"
ALPACA_DATA = "https://data.alpaca.markets"
RESEND_API = "https://api.resend.com/emails"


class DataError(RuntimeError):
    pass


def request_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DataError(f"GET {urllib.parse.urlsplit(url).path}: {exc}") from exc


def alpaca_headers(key: str, secret: str) -> dict[str, str]:
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"}


def get_json_with_headers(url: str, headers: dict[str, str]):
    return request_json(url, headers=headers)


def get_slot(now: dt.datetime) -> str | None:
    local = now.astimezone(CT)
    # GitHub cron is UTC. Both seasonal UTC candidates are configured; only the
    # candidate whose actual Central wall-clock time matches a target may send.
    targets = {"open": (8, 35), "midday": (12, 0), "close": (15, 5)}
    for slot, (hour, minute) in targets.items():
        delta = abs((local.hour * 60 + local.minute) - (hour * 60 + minute))
        if delta <= 40:
            return slot
    return None


def money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "n/a"


def pct(value, *, already_fraction=False) -> str:
    try:
        n = float(value) * (100 if already_fraction else 1)
        return f"{n:+.2f}%"
    except (TypeError, ValueError):
        return "n/a"


def safe_text(value, limit=240) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def market_calendar(headers: dict[str, str], local_date: dt.date) -> bool:
    query = urllib.parse.urlencode({"start": local_date.isoformat(), "end": local_date.isoformat()})
    result = get_json_with_headers(f"{ALPACA_PAPER}/v2/calendar?{query}", headers)
    return isinstance(result, list) and any(row.get("date") == local_date.isoformat() for row in result)


def fetch_market(headers: dict[str, str], now: dt.datetime) -> dict:
    market_date = now.astimezone(ET).date()
    result = {"symbols": {}, "news": [], "errors": []}
    for symbol in ("SPY", "QQQ"):
        try:
            encoded = urllib.parse.quote(symbol)
            trade_data = get_json_with_headers(f"{ALPACA_DATA}/v2/stocks/{encoded}/trades/latest?feed=iex", headers)
            trade = trade_data.get("trade") or {}
            price = trade.get("p")
            stamp = trade.get("t")
            query = urllib.parse.urlencode({
                "timeframe": "1Day",
                "start": (market_date - dt.timedelta(days=12)).isoformat(),
                "end": now.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                "limit": 20,
                "feed": "iex",
                "adjustment": "raw",
            })
            bars_data = get_json_with_headers(f"{ALPACA_DATA}/v2/stocks/{encoded}/bars?{query}", headers)
            bars = bars_data.get("bars") or []
            previous = None
            for bar in bars:
                ts = bar.get("t")
                if not ts:
                    continue
                try:
                    bar_date = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(ET).date()
                except ValueError:
                    continue
                if bar_date < market_date:
                    previous = bar
            prior_close = previous.get("c") if previous else None
            change = ((float(price) / float(prior_close)) - 1.0) * 100 if price and prior_close else None
            result["symbols"][symbol] = {
                "price": price, "prior_close": prior_close, "change_pct": change, "trade_at": stamp
            }
        except (DataError, TypeError, ValueError) as exc:
            result["errors"].append(f"{symbol} quote: {exc}")
    try:
        query = urllib.parse.urlencode({"symbols": "SPY,QQQ,TQQQ", "limit": 8, "sort": "desc"})
        news = get_json_with_headers(f"{ALPACA_DATA}/v1beta1/news?{query}", headers)
        for item in (news.get("news") or [])[:6]:
            result["news"].append({
                "headline": safe_text(item.get("headline"), 180),
                "created_at": safe_text(item.get("created_at"), 40),
                "summary": safe_text(item.get("summary"), 320),
                "url": safe_text(item.get("url"), 500),
            })
    except DataError as exc:
        result["errors"].append(f"News feed unavailable: {exc}")
    return result


def fetch_portfolio(label: str, suffix: str) -> dict:
    key = os.environ.get(f"ALPACA_PAPER_API_KEY_{suffix}", "").strip()
    secret = os.environ.get(f"ALPACA_PAPER_API_SECRET_{suffix}", "").strip()
    if not key or not secret:
        raise DataError(f"{label}: missing GitHub Actions Alpaca credentials")
    headers = alpaca_headers(key, secret)
    account = get_json_with_headers(f"{ALPACA_PAPER}/v2/account", headers)
    positions = get_json_with_headers(f"{ALPACA_PAPER}/v2/positions", headers)
    query = urllib.parse.urlencode({"status": "open", "limit": 100, "direction": "desc"})
    orders = get_json_with_headers(f"{ALPACA_PAPER}/v2/orders?{query}", headers)
    return {
        "label": label,
        "account": {
            "status": account.get("status"),
            "currency": account.get("currency"),
            "equity": account.get("equity"),
            "last_equity": account.get("last_equity"),
            "cash": account.get("cash"),
            "buying_power": account.get("buying_power"),
            "long_market_value": account.get("long_market_value"),
            "pattern_day_trader": account.get("pattern_day_trader"),
            "trading_blocked": account.get("trading_blocked"),
            "account_blocked": account.get("account_blocked"),
        },
        "positions": [{
            "symbol": p.get("symbol"), "qty": p.get("qty"), "side": p.get("side"),
            "market_value": p.get("market_value"), "unrealized_pl": p.get("unrealized_pl"),
            "unrealized_plpc": p.get("unrealized_plpc"), "current_price": p.get("current_price"),
            "avg_entry_price": p.get("avg_entry_price"),
        } for p in (positions if isinstance(positions, list) else [])],
        "open_orders": [{
            "symbol": o.get("symbol"), "side": o.get("side"), "qty": o.get("qty"),
            "status": o.get("status"), "type": o.get("type"), "submitted_at": o.get("submitted_at"),
        } for o in (orders if isinstance(orders, list) else [])],
    }


def load_latch(path: str | None) -> dict | None:
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        state = json.load(handle)
    latch = state.get("emergency_exit_latch")
    return latch if isinstance(latch, dict) else None


def load_latches(path_b0: str | None, path_f75: str | None) -> dict:
    return {"B0": load_latch(path_b0), "F75": load_latch(path_f75)}


def portfolio_delta(account: dict) -> str:
    try:
        equity, prior = float(account["equity"]), float(account["last_equity"])
        return money(equity - prior) + (f" ({(equity / prior - 1) * 100:+.2f}%)" if prior else "")
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return "n/a"


def build_report(slot: str, now: dt.datetime, market: dict, portfolios: list[dict], latches: dict, errors: list[str]) -> tuple[str, str, str]:
    local = now.astimezone(CT)
    labels = {"open": "Market Open", "midday": "Midday", "close": "Market Close", "test": "TEST"}
    label = labels.get(slot, slot.title())
    subject = f"[Trading Bot] {label} — {local:%a %b %d, %I:%M %p CT}"
    lines = [
        f"TRADING BOT — {label.upper()} REPORT",
        f"Generated: {local:%Y-%m-%d %I:%M:%S %p %Z} | Data timestamps are shown where available.",
        "",
        "MARKET SNAPSHOT (Alpaca IEX feed)",
    ]
    for symbol in ("SPY", "QQQ"):
        q = market.get("symbols", {}).get(symbol)
        if q:
            lines.append(f"{symbol}: {money(q.get('price'))}; prior close {money(q.get('prior_close'))}; change vs prior close {pct(q.get('change_pct'))}; last trade {q.get('trade_at') or 'timestamp unavailable'}.")
        else:
            lines.append(f"{symbol}: quote unavailable.")
    lines += ["", "PAPER PORTFOLIOS (live Alpaca paper-account responses)"]
    if not portfolios:
        lines.append("No account snapshots were successfully retrieved.")
    for p in portfolios:
        a = p["account"]
        lines += [
            "",
            f"{p['label']} — account status: {a.get('status') or 'unknown'}; trading blocked: {a.get('trading_blocked')}; account blocked: {a.get('account_blocked')}",
            f"Equity: {money(a.get('equity'))}; change vs prior equity: {portfolio_delta(a)}; cash: {money(a.get('cash'))}; buying power: {money(a.get('buying_power'))}; long market value: {money(a.get('long_market_value'))}.",
            "Positions:",
        ]
        if not p["positions"]:
            lines.append("  No open positions.")
        for pos in p["positions"]:
            lines.append(
                f"  {pos.get('symbol')} {pos.get('qty')} shares ({pos.get('side')}); value {money(pos.get('market_value'))}; unrealized P/L {money(pos.get('unrealized_pl'))} ({pct(pos.get('unrealized_plpc'), already_fraction=True)}); last price {money(pos.get('current_price'))}."
            )
        lines.append("Open orders:")
        if not p["open_orders"]:
            lines.append("  No open orders.")
        for order in p["open_orders"]:
            lines.append(f"  {order.get('side')} {order.get('qty')} {order.get('symbol')} — {order.get('status')} ({order.get('type')}); submitted {order.get('submitted_at')}.")
    lines += ["", "EMERGENCY DEFENSE LATCH (shared paper ledger snapshot)"]
    for portfolio, latch in latches.items():
        if not latch:
            lines.append(f"{portfolio}: no active latch recorded.")
        else:
            lines.append(
                f"{portfolio}: ACTIVE; trigger {money(latch.get('trigger_price'))} vs prior close {money(latch.get('trigger_close'))}; trough {money(latch.get('trough_price'))}; recovery threshold {money(latch.get('recovery_threshold'))}; trigger session {latch.get('trigger_session')}. New buys should remain blocked while latched."
            )
    lines += ["", "RECENT MARKET HEADLINES"]
    news = market.get("news") or []
    if not news:
        lines.append("News headlines unavailable from the configured Alpaca feed; no headlines have been inferred.")
    for item in news[:6]:
        lines.append(f"- {item.get('headline') or 'Untitled'} [{item.get('created_at') or 'time unavailable'}]")
        if item.get("summary"):
            lines.append(f"  {item['summary']}")
        if item.get("url"):
            lines.append(f"  {item['url']}")
    all_errors = errors + market.get("errors", [])
    lines += ["", "DATA QUALITY / NOTES"]
    if all_errors:
        lines += [f"- {e}" for e in all_errors]
        lines.append("- Treat missing fields as unknown; do not infer a healthy account from unavailable data.")
    else:
        lines.append("- Required account and market requests completed without reported errors.")
    lines += [
        "- This is a monitoring report, not a trade recommendation.",
        "- Email generation does not submit, cancel, or modify any broker order.",
    ]
    text_body = "\n".join(lines)
    escaped = html.escape(text_body)
    html_body = "<div style=\"font-family:Arial,sans-serif;white-space:pre-wrap;line-height:1.45\">" + escaped + "</div>"
    return subject, text_body, html_body


def send_resend(subject: str, text_body: str, html_body: str, *, test_mode: bool = False) -> dict:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    recipient = os.environ.get("ALERT_EMAIL", "").strip()
    sender = os.environ.get("RESEND_FROM_EMAIL", "").strip()
    missing = [name for name, value in (("RESEND_API_KEY", api_key), ("ALERT_EMAIL", recipient), ("RESEND_FROM_EMAIL", sender)) if not value]
    if missing:
        raise DataError("Missing required GitHub Actions secrets: " + ", ".join(missing))
    if test_mode:
        subject = "[TEST] " + subject
        text_body = "TEST EMAIL — delivery verification only.\n\n" + text_body
        html_body = "<p><strong>TEST EMAIL — delivery verification only.</strong></p>" + html_body
    payload = json.dumps({"from": sender, "to": [recipient], "subject": subject, "text": text_body, "html": html_body}).encode("utf-8")
    req = urllib.request.Request(
        RESEND_API,
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status < 200 or response.status >= 300 or not result.get("id"):
                raise DataError(f"Resend returned an unexpected response (HTTP {response.status}).")
            return {"id": result["id"], "status": response.status}
    except urllib.error.HTTPError as exc:
        # Do not echo the API key or request headers into the logs.
        detail = safe_text(exc.read().decode("utf-8", errors="replace"), 500)
        raise DataError(f"Resend rejected the request (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DataError(f"Resend request failed: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-b0")
    parser.add_argument("--state-f75")
    parser.add_argument("--test-send", action="store_true", help="Send an explicitly requested test email.")
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    if args.test_send:
        slot = "test"
    else:
        slot = get_slot(now)
        if slot is None:
            print(json.dumps({"status": "SKIP_OUTSIDE_CENTRAL_REPORT_WINDOW", "central_time": now.astimezone(CT).isoformat()}))
            return 0
    errors: list[str] = []
    portfolios = []
    for label, suffix in (("B0", "B0"), ("F75", "F75")):
        try:
            portfolios.append(fetch_portfolio(label, suffix))
        except DataError as exc:
            errors.append(str(exc))
    # Still send a report if both broker snapshots fail: the email must disclose
    # missing account data rather than silently disappearing.
    primary_key = os.environ.get("ALPACA_PAPER_API_KEY_B0", "").strip()
    primary_secret = os.environ.get("ALPACA_PAPER_API_SECRET_B0", "").strip()
    market = {"symbols": {}, "news": [], "errors": []}
    if primary_key and primary_secret:
        headers = alpaca_headers(primary_key, primary_secret)
        if not args.test_send:
            try:
                if not market_calendar(headers, now.astimezone(ET).date()):
                    print(json.dumps({"status": "SKIP_NON_TRADING_DAY", "central_time": now.astimezone(CT).isoformat()}))
                    return 0
            except DataError as exc:
                errors.append(f"Could not verify market calendar: {exc}")
        market = fetch_market(headers, now)
    else:
        errors.append("B0 credentials unavailable; market data/news were not requested.")
    latches = load_latches(args.state_b0, args.state_f75)
    subject, text_body, html_body = build_report(slot, now, market, portfolios, latches, errors)
    try:
        result = send_resend(subject, text_body, html_body, test_mode=args.test_send)
    except DataError as exc:
        print(json.dumps({"status": "EMAIL_FAILED", "error": str(exc), "portfolio_count": len(portfolios)}))
        return 1
    print(json.dumps({"status": "EMAIL_ACCEPTED_BY_RESEND", "slot": slot, "resend_id": result["id"], "http_status": result["status"], "portfolio_count": len(portfolios), "error_count": len(errors) + len(market.get("errors", []))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
