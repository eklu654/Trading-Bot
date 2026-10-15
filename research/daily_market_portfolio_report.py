#!/usr/bin/env python3
"""Read-only daily market + Alpaca paper portfolio email report.

This script never places, replaces, or cancels orders. It reads market quotes,
paper-account snapshots, and the shared virtual ledgers, then emails a summary.
Missing/stale data is reported as unavailable, never inferred.
"""
from __future__ import annotations

import email.utils
import json
import os
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
TARGETS = {(8, 30): "Market open", (12, 0): "Midday", (15, 0): "Market close"}
DEFAULT_TO = "eklu654@gmail.com"
SYMBOLS = [
    ("SPY", "S&P 500 ETF"), ("QQQ", "Nasdaq-100 ETF"),
    ("DIA", "Dow ETF"), ("IWM", "Russell 2000 ETF"),
    ("^VIX", "VIX"), ("TLT", "Long Treasury ETF"),
    ("GLD", "Gold ETF"),
]
USER_AGENT = "TradingBotDailyReport/1.0 contact=eklu654@gmail.com"


class ReportError(RuntimeError):
    pass


def request_bytes(url: str, headers: dict[str, str] | None = None, timeout: int = 12) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    return json.loads(request_bytes(url, headers).decode("utf-8"))


def money(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "unavailable"


def signed_pct(value) -> str:
    try:
        n = float(value)
        return f"{n:+.2f}%"
    except (TypeError, ValueError):
        return "unavailable"


def fetch_quote(symbol: str, label: str) -> dict:
    encoded = urllib.parse.quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=5d&interval=5m&includePrePost=true"
    payload = get_json(url)
    result = payload.get("chart", {}).get("result") or []
    if not result:
        raise ReportError(f"no quote result for {symbol}")
    meta = result[0].get("meta") or {}
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    regular = meta.get("regularMarketPrice")
    pre = meta.get("preMarketPrice")
    post = meta.get("postMarketPrice")
    chosen = pre if pre is not None and pre > 0 else regular
    chosen_label = "pre-market" if chosen == pre and pre is not None else "regular/latest"
    now_ct = datetime.now(CT)
    if now_ct.hour >= 15 and post is not None and post > 0:
        chosen, chosen_label = post, "after-hours"
    change = (float(chosen) / float(prev) - 1) * 100 if chosen and prev else None
    return {"symbol": symbol, "label": label, "price": chosen, "previous": prev,
            "change_pct": change, "quote_type": chosen_label,
            "asof": meta.get("regularMarketTime")}


def market_section() -> tuple[list[str], list[str]]:
    lines, errors = [], []
    for symbol, label in SYMBOLS:
        try:
            q = fetch_quote(symbol, label)
            pct = signed_pct(q["change_pct"])
            lines.append(f"- {q['symbol']} ({q['label']}): {money(q['price'])}; {pct} vs previous close ({q['quote_type']}).")
        except Exception as exc:
            errors.append(f"{symbol}: {type(exc).__name__}: {exc}")
            lines.append(f"- {symbol} ({label}): quote unavailable.")
    return lines, errors


def fetch_headlines() -> tuple[list[str], list[str]]:
    # Google News RSS search; each item retains its original source and link.
    query = urllib.parse.quote("US stock market OR Federal Reserve OR Treasury yields when:1d")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        root = ET.fromstring(request_bytes(url).decode("utf-8"))
        out = []
        for item in root.findall("./channel/item")[:5]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source = (item.findtext("source") or "").strip()
            if title and link:
                out.append(f"- {title}" + (f" — {source}" if source else "") + f"\n  {link}")
        return (out or ["- No headlines returned by the news feed."], [])
    except Exception as exc:
        return (["- News feed unavailable; no headlines are inferred."],
                [f"news RSS: {type(exc).__name__}: {exc}"])


def alpaca_headers(key: str, secret: str) -> dict[str, str]:
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def account_snapshot(label: str, suffix: str) -> dict:
    key = os.environ.get(f"ALPACA_PAPER_API_KEY_{suffix}", "")
    secret = os.environ.get(f"ALPACA_PAPER_API_SECRET_{suffix}", "")
    if not key or not secret:
        raise ReportError("paper-account credentials are not configured")
    base = "https://paper-api.alpaca.markets"
    headers = alpaca_headers(key, secret)
    account = get_json(base + "/v2/account", headers)
    positions = get_json(base + "/v2/positions", headers)
    orders = get_json(base + "/v2/orders?status=open&limit=100&direction=desc", headers)
    clock = get_json(base + "/v2/clock", headers)
    return {"label": label, "account": account, "positions": positions,
            "open_orders": orders, "clock": clock}


def portfolio_lines() -> tuple[list[str], list[str]]:
    lines, errors = [], []
    for label, suffix in (("B0", "B0"), ("F75", "F75")):
        try:
            s = account_snapshot(label, suffix)
            a = s["account"]
            lines.append(f"**{label} paper account** — status: {a.get('status','unknown')}; equity {money(a.get('equity'))}; cash {money(a.get('cash'))}; buying power {money(a.get('buying_power'))}.")
            positions = s["positions"]
            if positions:
                for p in positions:
                    lines.append(f"  - {p.get('symbol')}: qty {p.get('qty')}; market value {money(p.get('market_value'))}; unrealized P/L {money(p.get('unrealized_pl'))}; last {money(p.get('current_price'))}.")
            else:
                lines.append("  - No open positions reported by broker.")
            orders = s["open_orders"]
            if orders:
                for o in orders:
                    lines.append(f"  - OPEN ORDER: {o.get('side')} {o.get('qty')} {o.get('symbol')}; status {o.get('status')}; id {o.get('id')}.")
            else:
                lines.append("  - No open orders reported by broker.")
            clock = s["clock"]
            lines.append(f"  - Broker clock: {'open' if clock.get('is_open') else 'closed'}; next open {clock.get('next_open','unknown')}; next close {clock.get('next_close','unknown')}.")
        except Exception as exc:
            errors.append(f"{label} paper account: {type(exc).__name__}: {exc}")
            lines.append(f"**{label} paper account** — UNAVAILABLE; broker snapshot failed. No account values inferred.")
    return lines, errors


def ledger_lines() -> list[str]:
    lines = []
    for label, filename in (("B0", "data/paper_execution/b0_state.json"),
                             ("F75", "data/paper_execution/f75_state.json")):
        path = Path(filename)
        if not path.exists():
            lines.append(f"- {label} virtual ledger: unavailable in this run.")
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            pending = state.get("pending_intent")
            latch = state.get("emergency_exit_latch")
            lines.append(
                f"- {label} virtual ledger (not broker-confirmed): cash {money(state.get('cash'))}; "
                f"equity {money(state.get('equity'))}; TQQQ qty {state.get('quantity', state.get('shares', 'unknown'))}; "
                f"pending intent {'yes' if pending else 'no'}; defense latch {'ACTIVE' if latch else 'inactive'}."
            )
        except Exception:
            lines.append(f"- {label} virtual ledger: unreadable; no values inferred.")
    return lines


def latest_executor_run() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        return "Latest executor workflow status unavailable (GitHub API access not configured)."
    try:
        url = f"https://api.github.com/repos/{repo}/actions/workflows/alpaca-paper-order-executor.yml/runs?branch=main&per_page=5"
        data = get_json(url, {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        runs = data.get("workflow_runs") or []
        if not runs:
            return "No executor workflow runs returned by GitHub."
        r = runs[0]
        return f"Latest executor workflow: {r.get('status')} / {r.get('conclusion') or 'in progress'}; started {r.get('created_at')}; {r.get('html_url')}."
    except Exception as exc:
        return f"Latest executor workflow unavailable ({type(exc).__name__}); do not infer bot health."


def build_report(now: datetime | None = None) -> tuple[str, str]:
    now = now or datetime.now(CT)
    minute_now = now.hour * 60 + now.minute
    nearest = min(TARGETS.items(), key=lambda item: abs(minute_now - (item[0][0] * 60 + item[0][1])))
    title = nearest[1] if abs(minute_now - (nearest[0][0] * 60 + nearest[0][1])) <= 20 else "Market update"
    subject = f"Trading Bot {title} Report — {now.strftime('%a %b %d, %Y %I:%M %p CT')}"
    market, market_errors = market_section()
    headlines, news_errors = fetch_headlines()
    portfolios, portfolio_errors = portfolio_lines()
    ledger = ledger_lines()
    status = latest_executor_run()
    body = [
        f"Trading Bot — {title}", f"Generated: {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}",
        "", "MARKET SNAPSHOT (indicative public quotes; delayed/stale values are not treated as live broker data)",
        *market, "", "OVERNIGHT / RECENT HEADLINES", *headlines, "",
        "LIVE ALPACA PAPER ACCOUNTS (read-only snapshot)", *portfolios, "",
        "SHARED VIRTUAL LEDGERS (separate from broker-confirmed positions)", *ledger, "",
        "BOT WORKFLOW", status, "",
        "DATA QUALITY", 
        *(["- One or more data sources failed; affected sections are explicitly marked unavailable."] if market_errors or news_errors or portfolio_errors else ["- All queried data sources responded; timestamps/market-hours still matter."]),
        *([f"- Diagnostic: {e}" for e in (market_errors + news_errors + portfolio_errors)]),
        "", "This report is informational. It does not place, cancel, or modify orders.",
    ]
    return subject, "\n".join(body)


def send_email(subject: str, body: str) -> None:
    host = os.environ.get("REPORT_SMTP_HOST", "")
    port = int(os.environ.get("REPORT_SMTP_PORT") or "587")
    username = os.environ.get("REPORT_SMTP_USERNAME", "")
    password = os.environ.get("REPORT_SMTP_PASSWORD", "")
    sender = os.environ.get("REPORT_EMAIL_FROM", username)
    recipient = os.environ.get("REPORT_EMAIL_TO", DEFAULT_TO)
    if not all((host, username, password, sender, recipient)):
        raise ReportError("email sender is not configured; set REPORT_SMTP_HOST, REPORT_SMTP_USERNAME, REPORT_SMTP_PASSWORD, and REPORT_EMAIL_FROM as GitHub Actions secrets")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email.utils.formataddr(("Trading Bot Daily Report", sender))
    msg["To"] = recipient
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)


def main() -> int:
    now = datetime.now(CT)
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and os.environ.get("REPORT_FORCE_SEND", "false").lower() != "true":
        print("MANUAL_RUN_NO_SEND: workflow_dispatch never sends an email unless REPORT_FORCE_SEND=true.")
        return 0
    if os.environ.get("REPORT_FORCE_SEND", "false").lower() != "true":
        minute_now = now.hour * 60 + now.minute
        distance = min(abs(minute_now - (h * 60 + m)) for h, m in TARGETS)
        if distance > 20:
            print(f"NO_REPORT_SLOT: local Central time is {now:%H:%M}; not within 20 minutes of a target.")
            return 0
    try:
        subject, body = build_report(now)
        send_email(subject, body)
        print(f"REPORT_SENT: slot={now:%H:%M %Z}; recipient={os.environ.get('REPORT_EMAIL_TO', DEFAULT_TO)}")
        return 0
    except Exception as exc:
        print(f"REPORT_FAILED_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
