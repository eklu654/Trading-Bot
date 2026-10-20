#!/usr/bin/env python3
"""Read-only daily market + Alpaca paper portfolio email report.

This script never places, replaces, or cancels orders. It reads market quotes,
paper-account snapshots, and the shared virtual ledgers, then emails a summary.
Missing/stale data is reported as unavailable, never inferred.
"""
from __future__ import annotations

import email.utils
import html
import json
import re
import os
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
TARGETS = {(8, 30): "Market open", (12, 0): "Midday", (15, 0): "Market close"}
SCHEDULE_SLOTS = {
    "30 13 * * 1-5": ("Market open", (8, 30)),
    "30 14 * * 1-5": ("Market open", (8, 30)),
    "0 17 * * 1-5": ("Midday", (12, 0)),
    "0 18 * * 1-5": ("Midday", (12, 0)),
    "0 20 * * 1-5": ("Market close", (15, 0)),
    "0 21 * * 1-5": ("Market close", (15, 0)),
}
MAX_EARLY_MINUTES = 15
MAX_LATE_MINUTES = 360  # GitHub scheduled workflows can be delayed; still suppress runs delayed beyond six hours.
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
    now_ct = datetime.now(CT)
    before_open = (now_ct.hour, now_ct.minute) < (8, 30)
    after_close = (now_ct.hour, now_ct.minute) >= (15, 0)
    if before_open and pre is not None and pre > 0:
        chosen, chosen_label, asof = pre, "pre-market", meta.get("preMarketTime")
    elif after_close and post is not None and post > 0:
        chosen, chosen_label, asof = post, "after-hours", meta.get("postMarketTime")
    else:
        chosen, chosen_label, asof = regular, "regular/latest", meta.get("regularMarketTime")
    change = (float(chosen) / float(prev) - 1) * 100 if chosen and prev else None
    try:
        asof_text = datetime.fromtimestamp(int(asof), CT).strftime("%I:%M %p CT") if asof else "timestamp unavailable"
    except (TypeError, ValueError, OSError):
        asof_text = "timestamp unavailable"
    return {"symbol": symbol, "label": label, "price": chosen, "previous": prev,
            "change_pct": change, "quote_type": chosen_label, "asof": asof,
            "asof_text": asof_text}


def market_section() -> tuple[list[str], list[str]]:
    lines, errors = [], []
    for symbol, label in SYMBOLS:
        try:
            q = fetch_quote(symbol, label)
            pct = signed_pct(q["change_pct"])
            lines.append(f"- {q['symbol']} ({q['label']}): {money(q['price'])}; {pct} vs previous close ({q['quote_type']}, as of {q['asof_text']}).")
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
                f"equity {money(state.get('equity'))}; {state.get('symbol', 'asset')} qty {state.get('qty', state.get('quantity', state.get('shares', 'unknown')))}; mark date {state.get('mark_date', 'unknown')} at {money(state.get('mark_price'))}; "
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


def market_assessment(market_lines: list[str], headlines: list[str]) -> list[str]:
    """Produce a cautious, evidence-based assessment from the live quote snapshot.

    This is intentionally rules-based (no external LLM/API dependency). It does not
    infer a multi-week trend from one session or treat headlines as verified facts.
    """
    changes: dict[str, float] = {}
    for line in market_lines:
        match = re.search(r"- (SPY|QQQ|DIA|IWM|\\^VIX|TLT|GLD) \\([^)]*\\): .*?; ([+-]?\\d+(?:\\.\\d+)?)%", line)
        if match:
            changes[match.group(1)] = float(match.group(2))
    equity_keys = ["SPY", "QQQ", "DIA", "IWM"]
    available = [changes[k] for k in equity_keys if k in changes]
    if len(available) < 2:
        return [
            "A reliable market read is unavailable because too few major-index quotes were returned.",
            "Treat the outlook as uncertain until fresh, timestamped index data are available; this snapshot alone cannot establish a durable trend or confirm that a defense trigger is active."
        ]
    avg = sum(available) / len(available)
    qqq = changes.get("QQQ")
    spy = changes.get("SPY")
    vix = changes.get("^VIX")
    if avg <= -1.0 and (vix is None or vix >= 3.0):
        tone = "risk-off"
        evidence = "Major equity indexes are broadly lower"
    elif avg >= 0.75 and (vix is None or vix <= 0):
        tone = "risk-on"
        evidence = "Major equity indexes are broadly higher"
    elif avg < -0.15:
        tone = "mildly defensive"
        evidence = "The major-index picture leans negative"
    elif avg > 0.15:
        tone = "constructive"
        evidence = "The major-index picture leans positive"
    else:
        tone = "mixed / range-bound"
        evidence = "Major equity indexes are showing limited net direction"
    details = []
    if qqq is not None and spy is not None:
        relative = "underperforming" if qqq < spy - 0.25 else "outperforming" if qqq > spy + 0.25 else "roughly in line with"
        details.append(f"QQQ is {relative} SPY on the session ({qqq:+.2f}% vs. {spy:+.2f}%).")
    if vix is not None:
        details.append(f"VIX is {vix:+.2f}% versus its previous close.")
    if "TLT" in changes:
        details.append(f"TLT, a Treasury-bond ETF proxy, is {changes['TLT']:+.2f}%; that is a price move, not a direct yield reading.")
    first = f"**Assessment: {tone}.** {evidence} (average change {avg:+.2f}% across the available major indexes). " + " ".join(details)
    if headlines and headlines[0].startswith("- "):
        first += " Headlines below provide context, but their titles alone are not enough to establish causation."
    second = ("For leveraged-equity exposure, today's tape is a short-horizon risk read—not proof of a new bull or bear regime. "
              "A string of modest losses can still create substantial cumulative damage even when QQQ never falls 4.5% in one day; "
              "that risk requires a separate trend/regime defense, not just a daily-shock trigger.")
    return [first, second]


def build_report(now: datetime | None = None, title_override: str | None = None) -> tuple[str, str]:
    now = now or datetime.now(CT)
    minute_now = now.hour * 60 + now.minute
    nearest = min(TARGETS.items(), key=lambda item: abs(minute_now - (item[0][0] * 60 + item[0][1])))
    title = title_override or (nearest[1] if abs(minute_now - (nearest[0][0] * 60 + nearest[0][1])) <= 20 else "Market update")
    subject = f"Trading Bot {title} Report — {now.strftime('%a %b %d, %Y %I:%M %p CT')}"
    market, market_errors = market_section()
    headlines, news_errors = fetch_headlines()
    assessment = market_assessment(market, headlines)
    portfolios, portfolio_errors = portfolio_lines()
    ledger = ledger_lines()
    status = latest_executor_run()
    all_errors = market_errors + news_errors + portfolio_errors
    body = [
        f"Trading Bot — {title}",
        f"Generated {now.strftime('%a, %b %d, %Y at %I:%M:%S %p %Z')}",
        "",
        "MARKET ASSESSMENT",
        *assessment,
        "",
        "MARKET SNAPSHOT",
        "Public market quotes are indicative; use each quote's timestamp to judge freshness.",
        *market,
        "",
        "TOP HEADLINES",
        *headlines,
        "",
        "PAPER ACCOUNTS — READ ONLY",
        *portfolios,
        "",
        "VIRTUAL LEDGERS — NOT BROKER-CONFIRMED",
        *ledger,
        "",
        "AUTOMATION STATUS",
        status,
        "",
        "DATA QUALITY",
        *(["- Some sources failed; affected fields are marked unavailable below."] if all_errors else ["- All queried sources responded. Quote timestamps and market hours still matter."]),
        *([f"- {e}" for e in all_errors]),
        "",
        "No orders are placed, canceled, or modified by this report.",
    ]
    return subject, "\n".join(body)


def render_html(body: str) -> str:
    lines = body.splitlines()
    out = ['<html><body style="font-family:Arial,Helvetica,sans-serif;color:#202124;line-height:1.45;max-width:760px;margin:0 auto;">',
           '<div style="border-bottom:3px solid #24476b;padding:4px 0 12px;margin-bottom:18px;">']
    in_list = False
    for i, line in enumerate(lines):
        safe = html.escape(line)
        if i == 0:
            out.append(f'<h1 style="font-size:23px;margin:0;color:#24476b;">{safe}</h1>')
            continue
        if i == 1:
            out.append(f'<p style="margin:5px 0 0;color:#5f6368;font-size:13px;">{safe}</p></div>')
            continue
        if not line:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if re.fullmatch(r"[A-Z][A-Z0-9 —–-]{2,}", line):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<h2 style="font-size:15px;margin:20px 0 7px;padding-bottom:4px;border-bottom:1px solid #dadce0;color:#24476b;">{safe}</h2>')
        elif line.startswith("- "):
            if not in_list:
                out.append('<ul style="padding-left:22px;margin:5px 0 10px;">')
                in_list = True
            out.append(f'<li style="margin:4px 0;">{safe[2:]}</li>')
        elif line.startswith("  - "):
            if not in_list:
                out.append('<ul style="padding-left:22px;margin:5px 0 10px;">')
                in_list = True
            out.append(f'<li style="margin:4px 0;color:#3c4043;">{safe[4:]}</li>')
        elif line.strip().startswith(("https://", "http://")):
            if in_list:
                out.append("</ul>")
                in_list = False
            url = html.escape(line.strip(), quote=True)
            out.append(f'<p style="margin:0 0 8px 16px;font-size:12px;"><a href="{url}" style="color:#1a73e8;">Open source</a></p>')
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
            out.append(f'<p style="margin:5px 0;">{safe}</p>')
    if in_list:
        out.append("</ul>")
    out.append('<p style="margin-top:22px;padding-top:10px;border-top:1px solid #dadce0;color:#5f6368;font-size:12px;">Automated informational report. It does not trade or change orders.</p></body></html>')
    return "".join(out)


def resolve_scheduled_slot(now: datetime, event_name: str, event_schedule: str) -> tuple[str | None, str]:
    if event_name != "schedule":
        return None, "not a scheduled event"
    candidate = SCHEDULE_SLOTS.get(event_schedule.strip())
    if not candidate:
        return None, "unrecognized schedule expression"
    label, (hour, minute) = candidate
    local_now = now.astimezone(CT)
    target = datetime(local_now.year, local_now.month, local_now.day, hour, minute, tzinfo=CT)
    expected_utc = target.astimezone(timezone.utc)
    try:
        fields = event_schedule.split()
        cron_minute, cron_hour = int(fields[0]), int(fields[1])
    except (ValueError, IndexError):
        return None, "invalid schedule expression"
    if (cron_hour, cron_minute) != (expected_utc.hour, expected_utc.minute):
        return None, "schedule expression is for the other daylight-saving-time offset"
    delta_minutes = (local_now - target).total_seconds() / 60
    if delta_minutes < -MAX_EARLY_MINUTES:
        return None, f"scheduled run started {abs(delta_minutes):.0f} minutes before its intended slot"
    if delta_minutes > MAX_LATE_MINUTES:
        return None, f"scheduled run started {delta_minutes:.0f} minutes late; stale report suppressed"
    return label, f"scheduled slot accepted ({delta_minutes:+.0f} minutes from target)"


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
    msg.add_alternative(render_html(body), subtype="html")
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)


def main() -> int:
    now = datetime.now(CT)
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    force_send = os.environ.get("REPORT_FORCE_SEND", "false").lower() == "true"
    if force_send:
        minute_now = now.hour * 60 + now.minute
        nearest = min(TARGETS.items(), key=lambda item: abs(minute_now - (item[0][0] * 60 + item[0][1])))
        title = nearest[1] if abs(minute_now - (nearest[0][0] * 60 + nearest[0][1])) <= 20 else "Manual market update"
        reason = "explicit force-send override"
    elif event_name == "workflow_dispatch":
        title, reason = "Manual market update", "explicit manual workflow dispatch"
    else:
        title, reason = resolve_scheduled_slot(now, event_name, os.environ.get("GITHUB_EVENT_SCHEDULE", ""))
        if title is None:
            print(f"REPORT_SKIPPED: {reason}; current Central time {now:%Y-%m-%d %H:%M %Z}.")
            return 0
    try:
        subject, body = build_report(now, title_override=title)
        send_email(subject, body)
        print(f"REPORT_SENT: intended_slot={title}; {reason}; generated_at={now:%H:%M %Z}; recipient={os.environ.get('REPORT_EMAIL_TO', DEFAULT_TO)}")
        return 0
    except Exception as exc:
        print(f"REPORT_FAILED_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
