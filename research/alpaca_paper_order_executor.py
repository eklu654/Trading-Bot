"""Two-phase, paper-only B0/F75 executor.

A staged intent is committed first; SUBMITTING is committed before POST. Only
the scheduled event gets an ephemeral one-run permit. Later runs only reconcile
by client_order_id and never automatically retry an ambiguous submission.
"""
from __future__ import annotations
import argparse, csv, json, os
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from qqq_intraday_monitor import evaluate as evaluate_qqq_monitor, MonitorError

from paper_virtual_portfolio import (
    validate_state, state_json, plan_target, stage_intent, mark_submission_attempting,
    abort_unsubmitted_intent, mark_submission_outcome, reconcile_order, apply_fills, complete_terminal_intent, LedgerSafetyError,
    activate_emergency_exit_latch, update_emergency_exit_latch,
)

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
SYMBOL = "TQQQ"
NY = ZoneInfo("America/New_York")

class ExecutorBlocked(RuntimeError):
    pass

class PaperPostError(ExecutorBlocked):
    def __init__(self, status_code=None):
        self.status_code=status_code
        super().__init__(f"paper order POST outcome not confirmed (HTTP {status_code})" if status_code else "paper order POST outcome unknown")

def get_json(url, key, secret, allow_404=False):
    req=Request(url,headers={"APCA-API-KEY-ID":key,"APCA-API-SECRET-KEY":secret,
        "Accept":"application/json","User-Agent":"Trading-Bot-paper-executor/1.0"},method="GET")
    try:
        with urlopen(req,timeout=15) as r: return json.loads(r.read().decode("utf-8"))
    except HTTPError as exc:
        if allow_404 and exc.code==404: return None
        raise ExecutorBlocked(f"Alpaca GET returned HTTP {exc.code}") from None
    except (URLError,TimeoutError,json.JSONDecodeError,UnicodeDecodeError):
        raise ExecutorBlocked("Alpaca GET failed, timed out, or returned invalid JSON") from None

def post_order(payload,key,secret):
    """The only broker mutation; endpoint is hard-pinned to Alpaca paper."""
    req=Request(PAPER_URL+"/v2/orders",data=json.dumps(payload).encode("utf-8"),
        headers={"APCA-API-KEY-ID":key,"APCA-API-SECRET-KEY":secret,
                 "Accept":"application/json","Content-Type":"application/json",
                 "User-Agent":"Trading-Bot-paper-executor/1.0"},method="POST")
    try:
        with urlopen(req,timeout=15) as r: return json.loads(r.read().decode("utf-8"))
    except HTTPError as exc: raise PaperPostError(exc.code) from None
    except (URLError,TimeoutError,json.JSONDecodeError,UnicodeDecodeError): raise PaperPostError() from None


def account_fingerprint(account_id):
    value=str(account_id or "").strip()
    if not value: raise ExecutorBlocked("paper account identity is missing")
    return sha256(value.encode("utf-8")).hexdigest()

def verify_accounts(a):
    accounts={}
    fingerprints={}
    for portfolio in ("b0","f75"):
        key,secret=credentials(portfolio)
        account=get_json(PAPER_URL+"/v2/account",key,secret)
        if account.get("status")!="ACTIVE" or account.get("account_blocked") is not False or account.get("trading_blocked") is not False:
            raise ExecutorBlocked(f"{portfolio.upper()} paper account is not ACTIVE and unblocked")
        if account.get("currency")!="USD": raise ExecutorBlocked(f"{portfolio.upper()} paper account currency is not USD")
        fp=account_fingerprint(account.get("id"))
        accounts[portfolio]=account
        fingerprints[portfolio]=fp
    if fingerprints["b0"]==fingerprints["f75"]:
        raise ExecutorBlocked("B0 and F75 credentials resolve to the same paper account")
    for portfolio,path in (("b0",a.state_b0),("f75",a.state_f75)):
        state=json.loads(Path(path).read_text(encoding="utf-8"))
        validate_state(state)
        if state.get("portfolio")!=portfolio: raise ExecutorBlocked("state portfolio identity mismatch")
        prior=state.get("broker_account_fingerprint")
        if prior and prior!=fingerprints[portfolio]:
            raise ExecutorBlocked(f"{portfolio.upper()} paper account identity changed")
        state["broker_account_fingerprint"]=fingerprints[portfolio]
        write_state(path,state)
    emit(a.report,{"status":"DISTINCT_PAPER_ACCOUNTS_VERIFIED","accounts_distinct":True,
        "b0_account_active":True,"f75_account_active":True,"currency":"USD",
        "account_fingerprints_persisted":True,
        "note":"Raw account IDs and credentials are not logged."})

def order_payload(intent):
    if intent.get("endpoint")!=PAPER_URL or intent.get("mode")!="PLAN_ONLY_NO_SUBMISSION":
        raise ExecutorBlocked("intent is not explicitly paper-only")
    if intent.get("symbol")!=SYMBOL or intent.get("side") not in ("buy","sell"):
        raise ExecutorBlocked("intent symbol or side is invalid")
    qty=Decimal(str(intent.get("qty","0")))
    if not qty.is_finite() or qty<=0: raise ExecutorBlocked("intent quantity must be positive and finite")
    cid=str(intent.get("client_order_id",""))
    if not cid.startswith("tb-") or len(cid)>48: raise ExecutorBlocked("client order ID is invalid")
    return {"symbol":SYMBOL,"qty":str(qty),"side":intent["side"],"type":"market",
            "time_in_force":"day","client_order_id":cid}

def read_signal(ledger_path,manifest_path,now):
    raw=Path(ledger_path).read_bytes()
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if sha256(raw).hexdigest()!=manifest.get("ledger_sha256"): raise ExecutorBlocked("shadow ledger hash does not match manifest")
    if manifest.get("mode")!="SHADOW_ONLY_NO_ORDERS": raise ExecutorBlocked("shadow ledger is not in no-orders mode")
    with open(ledger_path,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if not rows or manifest.get("ledger_rows_total")!=len(rows): raise ExecutorBlocked("shadow ledger is empty or row count mismatches manifest")
    dates=[r.get("date","") for r in rows]
    if dates!=sorted(dates) or len(dates)!=len(set(dates)): raise ExecutorBlocked("shadow ledger dates are duplicated or unordered")
    source=manifest.get("canonical_input_sha256")
    if any(r.get("source_canonical_sha256")!=source for r in rows): raise ExecutorBlocked("shadow ledger source hash mismatch")
    row=rows[-1]
    try:
        session=date.fromisoformat(row["date"]).isoformat()
        b0=Decimal(row["b0_signal_close"]); f75=Decimal(row["f75_signal_close"])
    except Exception: raise ExecutorBlocked("latest shadow signal row is malformed") from None
    if date.fromisoformat(session)>=now.astimezone(NY).date(): raise ExecutorBlocked("current-session signal is incomplete; refusing lookahead")
    if b0 not in (Decimal("0"),Decimal("1")) or f75 not in (Decimal("0"),Decimal("0.75"),Decimal("1")):
        raise ExecutorBlocked("latest B0/F75 target weights are invalid")
    if f75>b0 or (b0==0 and f75!=0): raise ExecutorBlocked("F75 target violates B0 eligibility")
    return session,b0,f75,source

def qqq_defense_preflight(key, secret, now, state):
    """Fresh QQQ defense check for executor ordering safety; no order mutation."""
    clock=get_json(PAPER_URL+"/v2/clock",key,secret)
    if not isinstance(clock,dict):
        raise ExecutorBlocked("QQQ defense preflight returned invalid broker clock")
    if clock.get("is_open") is not True:
        return {"status":"MARKET_CLOSED","active":bool(state.get("emergency_exit_latch")),"breached":False}
    start=(now.astimezone(NY).date()-timedelta(days=10)).isoformat()
    params=urlencode({"timeframe":"1Day","start":start,"limit":"20","feed":"iex","sort":"asc"})
    data=get_json(DATA_URL+"/v2/stocks/QQQ/bars?"+params,key,secret)
    bars=data.get("bars",[]) if isinstance(data,dict) else None
    if not isinstance(bars,list):
        raise ExecutorBlocked("QQQ defense preflight daily bars response is invalid")
    trade=get_json(DATA_URL+"/v2/stocks/QQQ/trades/latest?"+urlencode({"feed":"iex"}),key,secret)
    try:
        report=evaluate_qqq_monitor(clock,trade,bars,now)
    except MonitorError as exc:
        if state.get("emergency_exit_latch") is not None:
            return {"status":"PREFLIGHT_UNAVAILABLE","active":True,"breached":False,
                    "changed":False,"state":state,"reason":str(exc)}
        raise ExecutorBlocked(f"QQQ defense preflight failed closed: {exc}") from None
    if report.get("status") in ("STALE_TRADE_FAIL_CLOSED","ERROR_FAIL_CLOSED"):
        if state.get("emergency_exit_latch") is not None:
            return {"status":report.get("status"),"active":True,"breached":False,
                    "changed":False,"state":state,"report":report}
        raise ExecutorBlocked("QQQ defense preflight trade is stale or invalid")
    if report.get("status") not in ("THRESHOLD_BREACHED","MONITORING"):
        raise ExecutorBlocked("QQQ defense preflight did not produce a valid live observation")
    changed=False
    if report.get("status")=="THRESHOLD_BREACHED":
        identity={"symbol":"QQQ","session":report["session"],
                  "trade_timestamp":report["trade_timestamp"],
                  "observed_at_utc":report["observed_at_utc"],
                  "qqq_price":str(report["qqq_price"]),"prior_close":str(report["prior_close"]),
                  "threshold_pct":"4.5"}
        digest=sha256(json.dumps(identity,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        if state.get("emergency_exit_latch") is None:
            state=activate_emergency_exit_latch(state,trigger_session=report["session"],
                qqq_price=report["qqq_price"],prior_close=report["prior_close"],trigger_sha256=digest)
            changed=True
        else:
            before=json.dumps(state.get("emergency_exit_latch"),sort_keys=True)
            state=update_emergency_exit_latch(state,current_qqq_price=report["qqq_price"])
            changed=before!=json.dumps(state.get("emergency_exit_latch"),sort_keys=True)
    elif state.get("emergency_exit_latch") is not None:
        before=json.dumps(state.get("emergency_exit_latch"),sort_keys=True)
        state=update_emergency_exit_latch(state,current_qqq_price=report["qqq_price"])
        changed=before!=json.dumps(state.get("emergency_exit_latch"),sort_keys=True)
    return {"status":report["status"],"active":bool(state.get("emergency_exit_latch")),
            "breached":report.get("status")=="THRESHOLD_BREACHED","changed":changed,
            "report":report,"state":state}


def effective_target(portfolio, b0, f75, state):
    """Apply the durable defense latch after validating the ordinary signal."""
    strategy_target = b0 if portfolio == "b0" else f75
    latch = state.get("emergency_exit_latch")
    active = bool(latch and latch.get("active") is True)
    return strategy_target, (Decimal("0") if active else strategy_target), active


def credentials(portfolio):
    suffix=portfolio.upper()
    key=os.environ.get(f"ALPACA_PAPER_API_KEY_{suffix}","")
    secret=os.environ.get(f"ALPACA_PAPER_API_SECRET_{suffix}","")
    if not key or not secret: raise ExecutorBlocked(f"paper credentials missing for {portfolio}")
    return key,secret

def broker_context(portfolio,state,key,secret,now,allow_pending_client_id=None):
    account=get_json(PAPER_URL+"/v2/account",key,secret)
    clock=get_json(PAPER_URL+"/v2/clock",key,secret)
    if account.get("status")!="ACTIVE" or account.get("account_blocked") is not False or account.get("trading_blocked") is not False:
        raise ExecutorBlocked("paper account is not ACTIVE and unblocked")
    if account.get("currency")!="USD": raise ExecutorBlocked("paper account currency is not USD")
    fp=account_fingerprint(account.get("id"))
    if state.get("broker_account_fingerprint")!=fp: raise ExecutorBlocked("paper account identity does not match durable portfolio state")
    if clock.get("is_open") is not True: return None
    positions=get_json(PAPER_URL+"/v2/positions",key,secret)
    opens=get_json(PAPER_URL+"/v2/orders?"+urlencode({"status":"open","limit":"500","direction":"desc"}),key,secret)
    recent=get_json(PAPER_URL+"/v2/orders?"+urlencode({"status":"all","limit":"100","direction":"desc"}),key,secret)
    if not isinstance(positions,list) or not isinstance(opens,list) or not isinstance(recent,list):
        raise ExecutorBlocked("broker positions/orders response has unexpected shape")
    if any(p.get("symbol")!=SYMBOL for p in positions): raise ExecutorBlocked("unexpected broker position; manual reconciliation required")
    pos=next((p for p in positions if p.get("symbol")==SYMBOL),None)
    qty=Decimal(str(pos["qty"])) if pos else Decimal("0")
    if qty<0 or (pos and str(pos.get("side","long")).lower()!="long"): raise ExecutorBlocked("short TQQQ position is not allowed")
    if abs(qty-Decimal(state["qty"]))>Decimal("0.001"): raise ExecutorBlocked("broker TQQQ quantity does not reconcile to fill-backed ledger")
    if any(o.get("client_order_id")!=allow_pending_client_id for o in opens): raise ExecutorBlocked("unresolved unrelated open order exists")
    used=set(state.get("used_client_order_ids",[]))
    if any(str(o.get("client_order_id") or "").startswith("tb-") and o.get("client_order_id") not in used for o in recent):
        raise ExecutorBlocked("bot-tagged broker order is absent from durable ledger")
    trade=get_json(DATA_URL+"/v2/stocks/TQQQ/trades/latest?feed=iex",key,secret)
    trade=trade.get("trade") if isinstance(trade,dict) else None
    if not isinstance(trade,dict) or "p" not in trade or "t" not in trade: raise ExecutorBlocked("latest TQQQ trade response is incomplete")
    try:
        price=Decimal(str(trade["p"]))
        stamp=datetime.fromisoformat(str(trade["t"]).replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception: raise ExecutorBlocked("latest TQQQ trade price/timestamp is invalid") from None
    age=(now-stamp).total_seconds()
    if not price.is_finite() or price<=0 or age < -5 or age>180: raise ExecutorBlocked("latest TQQQ trade is stale or invalid")
    return {"account":account,"clock":clock,"positions":positions,"open_orders":opens,
            "recent_orders":recent,"price":price,"trade_time":stamp,"trade_age":age,"qty":qty}

def write_state(path,state):
    validate_state(state); Path(path).write_text(state_json(state)+"\n",encoding="utf-8")

def emit(path,data):
    Path(path).write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,indent=2))


def reconcile_order_fills(state, broker_order, key, secret):
    """Apply Alpaca FILL activities idempotently; only clear terminal intent after position reconciliation."""
    state = reconcile_order(state, broker_order)
    order_id = str(broker_order.get("id") or "")
    if not order_id:
        raise ExecutorBlocked("broker order has no ID; fill reconciliation blocked")
    activities = []
    page_token = None
    # Alpaca account activities are paginated. Bound the walk to avoid an
    # unbounded job; hitting the bound fails closed rather than clearing intent.
    for _ in range(100):
        params = {"direction": "asc", "page_size": "100"}
        if page_token:
            params["page_token"] = page_token
        url = PAPER_URL + "/v2/account/activities/FILL?" + urlencode(params)
        batch = get_json(url, key, secret)
        if not isinstance(batch, list):
            raise ExecutorBlocked("fill activity response has unexpected shape")
        for activity in batch:
            if str(activity.get("order_id") or "") != order_id:
                continue
            activities.append({
                "id": activity.get("id"),
                "symbol": activity.get("symbol"),
                "side": activity.get("side"),
                "qty": activity.get("qty"),
                "price": activity.get("price"),
            })
        if len(batch) < 100:
            break
        # Alpaca activity pagination uses the last activity ID as page_token.
        page_token = str(batch[-1].get("id") or "")
        if not page_token:
            raise ExecutorBlocked("fill activity pagination token missing")
    else:
        raise ExecutorBlocked("fill activity pagination safety limit reached")
    state = apply_fills(state, activities)
    status = str(broker_order.get("status") or "").lower()
    if status in ("filled", "rejected", "canceled", "expired"):
        # Never infer terminal completion from order status alone. The broker's
        # current position must match the fill-backed ledger first.
        positions = get_json(PAPER_URL + "/v2/positions", key, secret)
        if not isinstance(positions, list):
            raise ExecutorBlocked("broker positions response has unexpected shape during fill reconciliation")
        if any(p.get("symbol") != SYMBOL for p in positions):
            raise ExecutorBlocked("unexpected broker position during fill reconciliation")
        pos = next((p for p in positions if p.get("symbol") == SYMBOL), None)
        broker_qty = Decimal(str(pos.get("qty"))) if pos else Decimal("0")
        try:
            state = complete_terminal_intent(state, broker_qty=broker_qty, broker_status=status)
        except LedgerSafetyError:
            # Persist any newly observed fill IDs and retain the pending intent.
            # A later reconciliation can retry the position comparison; it must
            # never erase an unresolved order merely because quantities disagree.
            pass
    return state

def prepare(a):
    now=datetime.now(timezone.utc)
    sp=Path(a.state); state=json.loads(sp.read_text(encoding="utf-8")); validate_state(state)
    if state.get("portfolio")!=a.portfolio: raise ExecutorBlocked("state portfolio mismatch")
    session,b0,f75,source=read_signal(a.ledger,a.manifest,now)
    # A persisted latch overrides the daily target. Submission-enabled runs independently
    # check QQQ before planning so monitor ordering is not required to block new buys.
    enabled=os.environ.get("ENABLE_PAPER_ORDER_SUBMISSION","false").lower()=="true"
    if enabled:
        key,secret=credentials(a.portfolio)
        preflight=qqq_defense_preflight(key,secret,now,state)
        if preflight.get("status")=="MARKET_CLOSED":
            emit(a.report,{"status":"SKIPPED_MARKET_CLOSED","portfolio":a.portfolio,
                "signal_session":session,"note":"No intent staged; QQQ preflight confirmed market closed."}); return
        state=preflight["state"]
        if preflight.get("changed"):
            write_state(sp,state)
        if preflight.get("status") not in ("THRESHOLD_BREACHED","MONITORING") and not state.get("emergency_exit_latch"):
            raise ExecutorBlocked("QQQ defense preflight did not authorize order planning")
    strategy_target,target,emergency_exit_active=effective_target(a.portfolio,b0,f75,state)
    pending=state.get("pending_intent")
    if pending:
        if pending.get("submission_state")=="STAGED" and enabled:
            if state.get("mark_date")!=session or pending.get("signal_session")!=session or Decimal(pending.get("target_weight"))!=target:
                state=mark_submission_attempting(state)
                state=abort_unsubmitted_intent(state,"staged intent no longer matches current signal/session")
                write_state(sp,state)
                emit(a.report,{"status":"ABORTED_STALE_STAGED_INTENT","portfolio":a.portfolio,"signal_session":session,"note":"No POST attempted."}); return
            ctx=broker_context(a.portfolio,state,*credentials(a.portfolio),now,allow_pending_client_id=pending["client_order_id"])
            if ctx is None:
                emit(a.report,{"status":"SKIPPED_MARKET_CLOSED","portfolio":a.portfolio,"signal_session":session,"note":"Staged intent preserved; no POST."}); return
            ref=Decimal(pending["reference_price"])
            if abs(ctx["price"]-ref)/ref>Decimal("0.0025"):
                state=mark_submission_attempting(state); state=abort_unsubmitted_intent(state,"reference price moved over 0.25% before POST")
                write_state(sp,state)
                emit(a.report,{"status":"ABORTED_STALE_STAGED_INTENT","portfolio":a.portfolio,"signal_session":session,"note":"No POST attempted."}); return
            Path(a.request).write_text(json.dumps(pending,indent=2)+"\n",encoding="utf-8")
            emit(a.report,{"status":"RESUME_STAGED_INTENT","portfolio":a.portfolio,"signal_session":session,"client_order_id":pending["client_order_id"],"note":"Durable staged intent will be armed before POST."}); return
        emit(a.report,{"status":"PENDING_RECONCILIATION","portfolio":a.portfolio,"signal_session":session,"submission_state":pending.get("submission_state"),"note":"No new intent or POST."}); return
    if state.get("mark_date")!=session: raise ExecutorBlocked("fill-backed virtual ledger is not marked through latest signal session")
    ctx=broker_context(a.portfolio,state,*credentials(a.portfolio),now)
    if ctx is None:
        emit(a.report,{"status":"SKIPPED_MARKET_CLOSED","portfolio":a.portfolio,"signal_session":session,"b0_target_weight":str(b0),"f75_target_weight":str(f75),"note":"No intent staged."}); return
    intent=plan_target(state,signal_session=session,target_weight=target,reference_price=ctx["price"],baseline_weight=b0 if a.portfolio=="f75" else None)
    if intent is None:
        emit(a.report,{"status":"NO_ORDER_NEEDED","portfolio":a.portfolio,"signal_session":session,"target_weight":str(target),"note":"Position already matches target."}); return
    summary={"portfolio":a.portfolio,"symbol":SYMBOL,"signal_session":session,"source_sha256":source,
             "strategy_target_weight":str(strategy_target),"target_weight":str(target),
             "emergency_exit_latch_active":emergency_exit_active,
             "reference_price":str(ctx["price"]),"trade_age_seconds":round(ctx["trade_age"],3),
             "intent":intent,"paper_endpoint":PAPER_URL,"mode":"PAPER_ONLY"}
    if not enabled:
        emit(a.report,{"status":"DRY_RUN_INTENT",**summary,"note":"Push/manual run; order submission is schedule-only."}); return
    state=stage_intent(state,intent); write_state(sp,state)
    Path(a.request).write_text(json.dumps(intent,indent=2)+"\n",encoding="utf-8")
    emit(a.report,{"status":"STAGED_FOR_PAPER_SUBMISSION",**summary,"note":"Intent must be committed before arm/POST."})

def arm(a):
    sp=Path(a.state); state=json.loads(sp.read_text(encoding="utf-8")); validate_state(state)
    rp=Path(a.request)
    if not rp.exists():
        emit(a.report,{"status":"NO_ARM_REQUEST","portfolio":a.portfolio,"note":"No staged request; no submission."}); return
    request=json.loads(rp.read_text(encoding="utf-8")); pending=state.get("pending_intent")
    if not pending or pending.get("client_order_id")!=request.get("client_order_id"):
        raise ExecutorBlocked("request does not match durable staged intent")
    if pending.get("submission_state")!="STAGED":
        emit(a.report,{"status":"NO_ARM_NEEDED","portfolio":a.portfolio,"submission_state":pending.get("submission_state")}); return
    state=mark_submission_attempting(state); write_state(sp,state)
    Path(a.permit).write_text(json.dumps({"client_order_id":request["client_order_id"],"permit":"single-run-only"}),"utf-8")
    emit(a.report,{"status":"ARMED","portfolio":a.portfolio,"client_order_id":request["client_order_id"],"note":"SUBMITTING persisted before POST; permit is ephemeral."})

def submit(a):
    sp=Path(a.state); state=json.loads(sp.read_text(encoding="utf-8")); validate_state(state)
    pending=state.get("pending_intent")
    if not pending:
        emit(a.report,{"status":"NO_PENDING_INTENT","portfolio":a.portfolio,"note":"No POST attempted."}); return
    key,secret=credentials(a.portfolio)
    cid=pending["client_order_id"]
    existing=get_json(PAPER_URL+"/v2/orders:by_client_order_id?"+urlencode({"client_order_id":cid}),key,secret,allow_404=True)
    if existing is not None:
        state=reconcile_order_fills(state,existing,key,secret); write_state(sp,state)
        emit(a.report,{"status":"EXISTING_ORDER_RECONCILED","portfolio":a.portfolio,"client_order_id":cid,"broker_order_id":existing.get("id"),"broker_status":existing.get("status"),"note":"No POST sent."}); return
    permit_path=Path(a.permit)
    permit=json.loads(permit_path.read_text(encoding="utf-8")) if permit_path.exists() else None
    has_permit=bool(permit and permit.get("client_order_id")==cid and permit.get("permit")=="single-run-only")
    if not has_permit:
        if pending.get("submission_state") not in ("STAGED","REJECTED"):
            state=reconcile_order(state,None); write_state(sp,state)
        emit(a.report,{"status":"NO_RETRY_WITHOUT_EPHEMERAL_PERMIT","portfolio":a.portfolio,"client_order_id":cid,"submission_state":(state.get("pending_intent") or {}).get("submission_state"),"note":"Order lookup found nothing; no POST without same-run permit."}); return
    try:
        now=datetime.now(timezone.utc)
        session,b0,f75,source=read_signal(a.ledger,a.manifest,now)
        # Last-moment QQQ guard: the monitor's schedule order is not a safety dependency.
        qqq=qqq_defense_preflight(key,secret,now,state)
        if qqq.get("status")=="MARKET_CLOSED":
            raise ExecutorBlocked("market closed during QQQ preflight before POST")
        state=qqq.get("state",state)
        if qqq.get("changed"):
            write_state(sp,state)
        if pending.get("side")=="buy" and qqq.get("status") not in ("THRESHOLD_BREACHED","MONITORING"):
            raise ExecutorBlocked("QQQ preflight failed closed; refusing buy POST")
        if pending.get("side")=="buy" and (qqq.get("breached") or qqq.get("active")):
            state=abort_unsubmitted_intent(state,"QQQ emergency defense active at pre-POST preflight")
            write_state(sp,state)
            emit(a.report,{"status":"ABORTED_BUY_DURING_QQQ_DEFENSE","portfolio":a.portfolio,
                "client_order_id":cid,"note":"No POST attempted; defense latch persisted."}); return
        strategy_target,target,emergency_exit_active=effective_target(a.portfolio,b0,f75,state)
        if session!=pending.get("signal_session") or target!=Decimal(pending.get("target_weight")):
            raise ExecutorBlocked("latest signal changed after intent was staged")
        if state.get("mark_date")!=session: raise ExecutorBlocked("virtual ledger mark date no longer matches signal session")
        opens=get_json(PAPER_URL+"/v2/orders?"+urlencode({"status":"open","limit":"500","direction":"desc"}),key,secret)
        if not isinstance(opens,list): raise ExecutorBlocked("open-order response has unexpected shape")
        same_open=next((o for o in opens if o.get("client_order_id")==cid),None)
        if same_open is not None:
            state=reconcile_order_fills(state,same_open,key,secret); write_state(sp,state)
            emit(a.report,{"status":"EXISTING_OPEN_ORDER_RECONCILED","portfolio":a.portfolio,"client_order_id":cid,"broker_order_id":same_open.get("id"),"note":"No POST sent."}); return
        ctx=broker_context(a.portfolio,state,key,secret,now,allow_pending_client_id=cid)
        if ctx is None: raise ExecutorBlocked("market closed before POST")
        ref=Decimal(pending["reference_price"])
        if abs(ctx["price"]-ref)/ref>Decimal("0.0025"): raise ExecutorBlocked("reference price moved over 0.25% before POST")
        # Final independent QQQ check directly before payload creation / POST.
        qqq_final=qqq_defense_preflight(key,secret,datetime.now(timezone.utc),state)
        if qqq_final.get("status")=="MARKET_CLOSED":
            raise ExecutorBlocked("market closed at final QQQ pre-POST check")
        state=qqq_final.get("state",state)
        if qqq_final.get("changed"):
            write_state(sp,state)
        if pending.get("side")=="buy" and qqq_final.get("status") not in ("THRESHOLD_BREACHED","MONITORING"):
            raise ExecutorBlocked("final QQQ preflight failed closed; refusing buy POST")
        if pending.get("side")=="buy" and (qqq_final.get("breached") or qqq_final.get("active")):
            state=abort_unsubmitted_intent(state,"QQQ emergency defense active at final pre-POST check")
            write_state(sp,state)
            emit(a.report,{"status":"ABORTED_BUY_DURING_QQQ_DEFENSE","portfolio":a.portfolio,
                "client_order_id":cid,"note":"No POST attempted; final defense latch persisted."}); return
        strategy_target,target,emergency_exit_active=effective_target(a.portfolio,b0,f75,state)
        if target!=Decimal(pending.get("target_weight")):
            state=abort_unsubmitted_intent(state,"target changed after final QQQ defense check")
            write_state(sp,state)
            emit(a.report,{"status":"ABORTED_STALE_STAGED_INTENT","portfolio":a.portfolio,
                "client_order_id":cid,"target_weight":str(target),
                "note":"No POST attempted; intent must be replanned against the active defense target."}); return
    except Exception as exc:
        reason=str(exc) if isinstance(exc,(ExecutorBlocked,LedgerSafetyError)) else f"preflight failure ({type(exc).__name__})"
        state=abort_unsubmitted_intent(state,reason); write_state(sp,state)
        emit(a.report,{"status":"ABORTED_BEFORE_POST","portfolio":a.portfolio,"reason":reason,"note":"Preflight failed before any POST; staged intent retired."}); return
    payload=order_payload(pending)
    try:
        result=post_order(payload,key,secret)
        if isinstance(result,dict) and result.get("client_order_id")==cid and result.get("id"):
            state=reconcile_order_fills(state,result,key,secret); status="SUBMITTED"; broker_id=result.get("id")
        else:
            found=get_json(PAPER_URL+"/v2/orders:by_client_order_id?"+urlencode({"client_order_id":cid}),key,secret,allow_404=True)
            if found: state=reconcile_order_fills(state,found,key,secret); status="RECONCILED_AFTER_RESPONSE"; broker_id=found.get("id")
            else: state=mark_submission_outcome(state,"unknown"); status="SUBMISSION_UNKNOWN"; broker_id=None
    except PaperPostError as exc:
        found=get_json(PAPER_URL+"/v2/orders:by_client_order_id?"+urlencode({"client_order_id":cid}),key,secret,allow_404=True)
        if found: state=reconcile_order_fills(state,found,key,secret); status="RECONCILED_AFTER_POST_ERROR"; broker_id=found.get("id")
        elif exc.status_code in (400,401,403,422):
            state=mark_submission_outcome(state,"rejected"); status="ORDER_REJECTED"; broker_id=None
        else: state=mark_submission_outcome(state,"unknown"); status="SUBMISSION_UNKNOWN"; broker_id=None
    write_state(sp,state)
    emit(a.report,{"status":status,"portfolio":a.portfolio,"client_order_id":cid,"broker_order_id":broker_id,
        "submission_state":(state.get("pending_intent") or {}).get("submission_state"),
        "paper_endpoint":PAPER_URL,"note":"Paper endpoint only. Outcome persisted for fill reconciliation; no retry in this run."})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("verify-accounts","prepare","arm","submit"),required=True)
    p.add_argument("--portfolio",choices=("b0","f75"),required=False)
    p.add_argument("--state-b0",default=""); p.add_argument("--state-f75",default="")
    p.add_argument("--state",default=""); p.add_argument("--report",required=True)
    p.add_argument("--ledger",default=""); p.add_argument("--manifest",default="")
    p.add_argument("--request",default=""); p.add_argument("--permit",default="")
    a=p.parse_args()
    if a.mode!="verify-accounts" and not a.portfolio: p.error("--portfolio is required for this mode")
    if a.mode!="verify-accounts" and not a.state: p.error("--state is required for this mode")
    try:
        if a.mode=="verify-accounts": verify_accounts(a)
        elif a.mode=="prepare": prepare(a)
        elif a.mode=="arm": arm(a)
        else: submit(a)
    except Exception as exc:
        emit(a.report,{"status":"BLOCKED","portfolio":a.portfolio,"mode":a.mode,
            "reason":str(exc) if isinstance(exc,(ExecutorBlocked,LedgerSafetyError)) else f"unexpected executor failure ({type(exc).__name__})",
            "note":"Paper-only executor. Any ambiguous outcome must be reconciled before retry."})
        raise SystemExit(2)

if __name__=="__main__": main()
