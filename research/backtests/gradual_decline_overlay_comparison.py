#!/usr/bin/env python3
"""Compare gradual-decline overlays against the frozen B0 shock/recovery rule.

Read-only research. No broker, account, or order APIs are used.
Data source: Yahoo Finance chart endpoint (QQQ signals, TQQQ execution prices).
"""
from __future__ import annotations
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

START = "2010-10-07"
INITIAL_CASH = 5000.0
SHOCK_PCT = -0.045
RECOVERY_PCT = 0.10
ROUND_TRIP_COST_BPS_PER_SIDE = 10.0  # conservative placeholder; report prominently
UA = "TradingBot-Research/1.0"


def fetch(symbol: str, start: str, end: str | None = None) -> dict[str, dict]:
    start_ts = int(datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    end_ts = int(datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) if end else int(datetime.now(timezone.utc).timestamp())
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(symbol, safe="")
           + f"?period1={start_ts}&period2={end_ts}&interval=1d&events=div%2Csplits")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8"))
    results = payload.get("chart", {}).get("result") or []
    if not results:
        raise RuntimeError(f"No chart data for {symbol}: {payload.get('chart', {}).get('error')}")
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    adj = (result.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
    rows = {}
    for i, ts in enumerate(timestamps):
        if i >= len(adj) or adj[i] is None:
            continue
        raw_close = quote.get("close", [None] * len(timestamps))[i]
        raw_open = quote.get("open", [None] * len(timestamps))[i]
        if raw_close is None or raw_open is None or raw_close == 0:
            continue
        day = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
        factor = float(adj[i]) / float(raw_close)
        rows[day] = {"open": float(raw_open) * factor, "close": float(adj[i])}
    return rows


def sma(values: list[float], i: int, n: int) -> float | None:
    if i + 1 < n:
        return None
    return sum(values[i - n + 1:i + 1]) / n


def run_variant(days: list[str], qqq: dict, tqqq: dict, variant: str) -> dict:
    cash = INITIAL_CASH
    shares = 0.0
    invested = True
    shock_latched = False
    shock_trough = math.inf
    prev_qqq = None
    qclose = [qqq[d]["close"] for d in days]
    equity_curve = []
    trades = 0
    invested_days = 0
    signals = 0
    cost = ROUND_TRIP_COST_BPS_PER_SIDE / 10000.0
    for i, day in enumerate(days):
        # Signals are evaluated on today's close and executed at next session's open.
        # The final date is marked to close; no impossible next-open trade is assumed.
        close_q = qqq[day]["close"]
        if prev_qqq is not None and close_q / prev_qqq - 1 <= SHOCK_PCT:
            shock_latched = True
            shock_trough = min(shock_trough, close_q)
        if shock_latched:
            shock_trough = min(shock_trough, close_q)
            if close_q >= shock_trough * (1 + RECOVERY_PCT):
                shock_latched = False
                shock_trough = math.inf
        ma100, ma200 = sma(qclose, i, 100), sma(qclose, i, 200)
        ret60 = close_q / qclose[i - 60] - 1 if i >= 60 else None
        if variant == "B0 shock/recovery":
            trend_off = False
        elif variant == "B0 + QQQ 100-DMA":
            trend_off = ma100 is not None and close_q < ma100
        elif variant == "B0 + QQQ 200-DMA":
            trend_off = ma200 is not None and close_q < ma200
        elif variant == "B0 + QQQ 60-session return":
            trend_off = ret60 is not None and ret60 < 0
        else:
            raise ValueError(variant)
        desired = not (shock_latched or trend_off)
        if i < len(days) - 1 and desired != invested:
            next_day = days[i + 1]
            px = tqqq.get(next_day, {}).get("open")
            if px is not None and px > 0:
                if desired:
                    spend = cash * (1 - cost)
                    shares = spend / px
                    cash = 0.0
                else:
                    cash = shares * px * (1 - cost)
                    shares = 0.0
                invested = desired
                trades += 1
                signals += 1
        if invested:
            invested_days += 1
            equity = shares * tqqq[day]["close"] if shares else cash
        else:
            equity = cash
        equity_curve.append(equity)
        prev_qqq = close_q
    peak = -math.inf
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        if peak > 0:
            max_dd = min(max_dd, v / peak - 1)
    return {
        "variant": variant,
        "start": days[0],
        "end": days[-1],
        "initial_cash": INITIAL_CASH,
        "final_equity": round(equity_curve[-1], 2),
        "return_pct": round((equity_curve[-1] / INITIAL_CASH - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "positioned_days_pct": round(invested_days / len(days) * 100, 2),
        "position_changes": trades,
        "estimated_one_way_cost_bps": ROUND_TRIP_COST_BPS_PER_SIDE,
        "note": "QQQ close signals execute next TQQQ open; daily close marks. Results are indicative; validate corporate-action adjustment and execution assumptions before decisions."
    }


def main() -> int:
    print("Downloading QQQ and TQQQ daily bars from Yahoo Finance…", flush=True)
    qqq = fetch("QQQ", START)
    tqqq = fetch("TQQQ", START)
    days = sorted(set(qqq) & set(tqqq))
    days = [d for d in days if d >= START]
    if len(days) < 1000:
        raise RuntimeError(f"Insufficient overlapping daily bars: {len(days)}")
    variants = [
        "B0 shock/recovery",
        "B0 + QQQ 100-DMA",
        "B0 + QQQ 200-DMA",
        "B0 + QQQ 60-session return",
    ]
    results = [run_variant(days, qqq, tqqq, v) for v in variants]
    print(json.dumps({
        "method": "Daily QQQ close signal, next TQQQ adjusted-open execution; adjusted close marking; cash earns zero; no dividends beyond adjusted-price series; no tax; 10 bps estimated cost per transaction.",
        "start": days[0], "end": days[-1], "sessions": len(days),
        "results": results,
        "limitations": [
            "Yahoo adjusted OHLC reconstruction uses adjusted-close/raw-close factor; validate against an independent source.",
            "B0 rule implemented here is the documented QQQ -4.5% daily shock exit and re-entry after a 10% rebound from post-shock low; this is a research reconstruction, not proof of the prior ~$4.04M result.",
            "A trend overlay exits while its signal is off and re-enters once its condition clears; no extra confirmation or optimization.",
            "A defense is not successful unless terminal equity exceeds the same-period B0 control after realistic costs."
        ]
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BACKTEST_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
