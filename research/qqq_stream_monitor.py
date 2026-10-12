"""Persistent, read-only Alpaca QQQ trade-stream monitor. Never submits orders."""
from __future__ import annotations
import json, os, sqlite3, sys, time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import websocket

NY = ZoneInfo("America/New_York")
DATA_URL = "https://data.alpaca.markets"
STREAM_URL = "wss://stream.data.alpaca.markets/v2/iex"
THRESHOLD = Decimal("0.045")

class MonitorError(RuntimeError):
    pass

def parse_ts(value):
    if not isinstance(value, str):
        raise MonitorError("trade timestamp missing")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise MonitorError("trade timestamp invalid") from None
    if dt.tzinfo is None:
        raise MonitorError("trade timestamp must include timezone")
    return dt.astimezone(timezone.utc)

def evaluate_trade(price, prior_close, trade_ts, now=None, threshold=THRESHOLD):
    """Pure detector. Returns status/session/change; deliberately has no order side effects."""
    now = now or datetime.now(timezone.utc)
    try:
        p, c = Decimal(str(price)), Decimal(str(prior_close))
    except (InvalidOperation, TypeError):
        raise MonitorError("price or prior close invalid") from None
    if not p.is_finite() or not c.is_finite() or p <= 0 or c <= 0:
        raise MonitorError("price and prior close must be positive finite numbers")
    ts = parse_ts(trade_ts)
    age = (now.astimezone(timezone.utc) - ts).total_seconds()
    if age < -30 or age > 180:
        return {"status":"STALE_TRADE_FAIL_CLOSED","trade_age_seconds":round(age,2)}
    local = ts.astimezone(NY)
    if local.weekday() >= 5 or local.hour < 9 or (local.hour == 9 and local.minute < 30) or local.hour > 16 or (local.hour == 16 and local.minute > 0):
        return {"status":"OUTSIDE_REGULAR_SESSION","session":local.date().isoformat()}
    change = p / c - Decimal("1")
    return {"status":"THRESHOLD_BREACHED" if change <= -threshold else "MONITORING",
            "session":local.date().isoformat(),"trade_timestamp":ts.isoformat(),
            "price":str(p),"prior_close":str(c),
            "change_pct":str((change*100).quantize(Decimal("0.001"))),
            "threshold_pct":"-4.5","threshold_breached":change <= -threshold,
            "orders_submitted":False}

def get_json(url, key, secret):
    req=Request(url,headers={"APCA-API-KEY-ID":key,"APCA-API-SECRET-KEY":secret,
                             "Accept":"application/json","User-Agent":"Trading-Bot-QQQ-stream/1.0"})
    try:
        with urlopen(req,timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise MonitorError(f"Alpaca API returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, ValueError) as exc:
        raise MonitorError(f"Alpaca API request failed ({type(exc).__name__})") from None

def latest_completed_close(key, secret, now=None):
    from datetime import date, timedelta
    now = now or datetime.now(timezone.utc)
    start_date = (now.astimezone(NY).date() - timedelta(days=14)).isoformat()
    params=urlencode({"timeframe":"1Day","start":start_date,"limit":"20","feed":"iex","sort":"asc"})
    data=get_json(DATA_URL+"/v2/stocks/QQQ/bars?"+params,key,secret)
    bars=data.get("bars") if isinstance(data,dict) else None
    if not isinstance(bars,list):
        raise MonitorError("daily bar response missing bars")
    today=now.astimezone(NY).date()
    eligible=[]
    for bar in bars:
        try:
            stamp=parse_ts(bar.get("t") or bar.get("timestamp"))
            session=stamp.astimezone(NY).date()
            close=Decimal(str(bar.get("c") or bar.get("close")))
            if session < today and close.is_finite() and close > 0:
                eligible.append((session,close))
        except (MonitorError, InvalidOperation, TypeError):
            continue
    if not eligible:
        raise MonitorError("no completed prior-session QQQ close")
    return max(eligible,key=lambda item:item[0])

class EventStore:
    """SQLite event journal. Unique event keys make reconnect duplicates idempotent."""
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS events(
            event_key TEXT PRIMARY KEY, observed_at TEXT NOT NULL, session TEXT NOT NULL,
            kind TEXT NOT NULL, payload TEXT NOT NULL)""")
        self.db.commit()
    def record_once(self, session, kind, payload, now=None):
        now=now or datetime.now(timezone.utc)
        key=f"{session}:{kind}"
        cur=self.db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,?,?)",
            (key,now.astimezone(timezone.utc).isoformat(),session,kind,json.dumps(payload,sort_keys=True)))
        self.db.commit()
        if cur.rowcount:
            print(json.dumps({"event":"QQQ_"+kind,**payload},sort_keys=True),flush=True)
            return True
        return False
    def has_event(self, session, kind):
        row=self.db.execute("SELECT 1 FROM events WHERE event_key=?",(f"{session}:{kind}",)).fetchone()
        return row is not None
    def close(self):
        self.db.close()

def run():
    key=os.environ.get("ALPACA_PAPER_API_KEY_B0","")
    secret=os.environ.get("ALPACA_PAPER_API_SECRET_B0","")
    if not key or not secret:
        raise MonitorError("B0 paper data credentials missing")
    store=EventStore(os.environ.get("QQQ_STREAM_DB","/data/qqq-stream-events.sqlite3"))
    backoff=1
    try:
        while True:
            try:
                session, close=latest_completed_close(key,secret)
                print(json.dumps({"event":"STREAM_CONNECTING","symbol":"QQQ","baseline_session":session.isoformat(),
                                  "baseline_close":str(close),"threshold_pct":"-4.5","orders_submitted":False}),flush=True)
                state={"authenticated":False,"subscribed":False}
                def on_open(ws):
                    ws.send(json.dumps({"action":"auth","key":key,"secret":secret}))
                def on_message(ws,message):
                    nonlocal backoff, session, close
                    try:
                        rows=json.loads(message)
                        if not isinstance(rows,list): rows=[rows]
                        for row in rows:
                            if row.get("T")=="success":
                                msg=row.get("msg","")
                                print(json.dumps({"event":"STREAM_STATUS","message":msg}),flush=True)
                                if msg=="authenticated" and not state["subscribed"]:
                                    ws.send(json.dumps({"action":"subscribe","trades":["QQQ"]}))
                                    state["authenticated"]=True
                                    state["subscribed"]=True
                                elif msg=="subscribed":
                                    backoff=1
                            elif row.get("T")=="error":
                                print(json.dumps({"event":"STREAM_ERROR","code":row.get("code"),"message":row.get("msg")}),flush=True)
                                ws.close()
                            elif row.get("T")=="t" and row.get("S")=="QQQ":
                                trade_time=parse_ts(row.get("t"))
                                trade_session=trade_time.astimezone(NY).date()
                                if trade_session > session:
                                    session, close=latest_completed_close(key,secret)
                                    print(json.dumps({"event":"BASELINE_REFRESHED","baseline_session":session.isoformat(),"baseline_close":str(close)}),flush=True)
                                result=evaluate_trade(row.get("p"),close,row.get("t"))
                                status=result["status"]
                                if status=="STALE_TRADE_FAIL_CLOSED":
                                    print(json.dumps({"event":status,"trade_age_seconds":result.get("trade_age_seconds")}),flush=True)
                                    continue
                                if status=="OUTSIDE_REGULAR_SESSION":
                                    continue
                                backoff=1
                                if status=="THRESHOLD_BREACHED":
                                    store.record_once(result["session"],"THRESHOLD_BREACHED",result)
                                elif store.has_event(result["session"],"THRESHOLD_BREACHED"):
                                    store.record_once(result["session"],"RECOVERED_ABOVE_THRESHOLD",result)
                    except Exception as exc:
                        print(json.dumps({"event":"MESSAGE_PROCESSING_ERROR","error":type(exc).__name__}),flush=True)
                def on_error(ws,error):
                    print(json.dumps({"event":"STREAM_SOCKET_ERROR","error":str(error)[:200]}),flush=True)
                def on_close(ws,code,msg):
                    print(json.dumps({"event":"STREAM_CLOSED","code":code,"message":str(msg)[:120]}),flush=True)
                ws=websocket.WebSocketApp(STREAM_URL,on_open=on_open,on_message=on_message,on_error=on_error,on_close=on_close)
                ws.run_forever(ping_interval=20,ping_timeout=10)
                print(json.dumps({"event":"STREAM_RECONNECTING","backoff_seconds":backoff}),flush=True)
            except Exception as exc:
                print(json.dumps({"event":"STREAM_LOOP_ERROR","error":type(exc).__name__,"message":str(exc)[:200]}),flush=True)
            time.sleep(backoff)
            backoff=min(backoff*2,60)
    finally:
        store.close()

if __name__=="__main__":
    try: run()
    except MonitorError as exc:
        print(json.dumps({"event":"FATAL_FAIL_CLOSED","reason":str(exc),"orders_submitted":False}),file=sys.stderr,flush=True)
        raise SystemExit(2)
