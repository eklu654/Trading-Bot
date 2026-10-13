"""Read-only intraday QQQ drawdown monitor for paper research.

Polls the latest Alpaca IEX trade against the most recent completed daily close.
This detects a threshold breach at poll time; it is not a tick-by-tick guarantee
and it never submits orders.
"""
from __future__ import annotations
import argparse, json, os
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
NY = ZoneInfo("America/New_York")
THRESHOLD = Decimal("0.045")

class MonitorError(RuntimeError):
    pass

def get_json(url, key, secret):
    req=Request(url, headers={"APCA-API-KEY-ID":key,"APCA-API-SECRET-KEY":secret,
                              "Accept":"application/json","User-Agent":"Trading-Bot-QQQ-intraday-monitor/1.0"})
    try:
        with urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise MonitorError(f"Alpaca API returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise MonitorError(f"Alpaca API request failed ({type(exc).__name__})") from None

def dec(value, label):
    try:
        result=Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise MonitorError(f"invalid {label}") from None
    if not result.is_finite() or result <= 0:
        raise MonitorError(f"non-positive or non-finite {label}")
    return result

def evaluate(clock, trade, bars, now, threshold=THRESHOLD):
    if not isinstance(clock,dict) or not isinstance(trade,dict) or not isinstance(bars,list):
        raise MonitorError("unexpected API response shape")
    stamp=now.astimezone(NY)
    report={"observed_at_utc":now.astimezone(timezone.utc).isoformat(),
            "symbol":"QQQ","threshold_pct":"4.5","orders_submitted":False}
    if not clock.get("is_open"):
        return {**report,"status":"MARKET_CLOSED"}
    latest=trade.get("trade",trade)
    trade_ts=latest.get("t") or latest.get("timestamp")
    if not trade_ts:
        raise MonitorError("latest QQQ trade timestamp missing")
    try:
        trade_time=datetime.fromisoformat(trade_ts.replace("Z","+00:00"))
        if trade_time.tzinfo is None: raise ValueError()
    except (ValueError, AttributeError):
        raise MonitorError("latest QQQ trade timestamp invalid") from None
    age=(now-trade_time.astimezone(timezone.utc)).total_seconds()
    report["trade_timestamp"]=trade_time.astimezone(timezone.utc).isoformat()
    report["trade_age_seconds"]=round(age,2)
    if age < -30 or age > 180:
        return {**report,"status":"STALE_TRADE_FAIL_CLOSED"}
    price=dec(latest.get("p") or latest.get("price"),"latest trade price")
    today=stamp.date()
    prior=[]
    for bar in bars:
        ts=bar.get("t") or bar.get("timestamp")
        if not ts: continue
        try: dt=datetime.fromisoformat(ts.replace("Z","+00:00"))
        except (ValueError,AttributeError): continue
        if dt.tzinfo is not None and dt.date() < today:
            prior.append((dt,dec(bar.get("c") or bar.get("close"),"daily close")))
    if not prior:
        raise MonitorError("no completed prior-session QQQ daily close available")
    prior.sort(key=lambda x:x[0])
    close_time, prior_close=prior[-1]
    move=price/prior_close-Decimal("1")
    report.update({"status":"THRESHOLD_BREACHED" if move <= -threshold else "MONITORING",
                   "session":today.isoformat(),"qqq_price":str(price),
                   "latest_price":str(price),"prior_completed_session":close_time.date().isoformat(),
                   "prior_close":str(prior_close),"change_from_prior_close_pct":str((move*100).quantize(Decimal("0.001"))),
                   "trigger_threshold_pct":"-4.5","threshold_breached":move <= -threshold})
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",default="qqq-intraday-monitor.json")
    args=parser.parse_args()
    key=os.environ.get("ALPACA_PAPER_API_KEY_B0","")
    secret=os.environ.get("ALPACA_PAPER_API_SECRET_B0","")
    if not key or not secret: raise MonitorError("B0 paper API credentials missing")
    now=datetime.now(timezone.utc)
    clock=get_json(PAPER_URL+"/v2/clock",key,secret)
    if not clock.get("is_open"):
        report={"status":"MARKET_CLOSED","observed_at_utc":now.isoformat(),"symbol":"QQQ",
                "threshold_pct":"4.5","orders_submitted":False}
    else:
        start=(now.astimezone(NY).date()-timedelta(days=10)).isoformat()
        params=urlencode({"timeframe":"1Day","start":start,"limit":"20","feed":"iex","sort":"asc"})
        data=get_json(DATA_URL+"/v2/stocks/QQQ/bars?"+params,key,secret)
        bars=data.get("bars",[]) if isinstance(data,dict) else None
        if not isinstance(bars,list): raise MonitorError("daily bar response missing bars")
        trade=get_json(DATA_URL+"/v2/stocks/QQQ/trades/latest?"+urlencode({"feed":"iex"}),key,secret)
        report=evaluate(clock,trade,bars,now)
    with open(args.report,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps(report,sort_keys=True))
    if report["status"]=="THRESHOLD_BREACHED":
        print("::warning::QQQ has breached the -4.5% intraday threshold versus the last completed daily close. Monitoring only; no order submitted.")

if __name__=="__main__":
    try: main()
    except MonitorError as exc:
        print(json.dumps({"status":"ERROR_FAIL_CLOSED","reason":str(exc),"orders_submitted":False},sort_keys=True))
        raise SystemExit(2)
