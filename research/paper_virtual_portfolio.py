"""Pure fill-backed virtual portfolio ledger and order-intent state machine.

No HTTP access and no order submission. State is intended to be durably stored
before any future broker mutation; unknown outcomes remain blocked until
reconciled by client order ID and broker position.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_DOWN
import hashlib
import json

SYMBOL = "TQQQ"
INITIAL_EQUITY = Decimal("5000.00")
WEIGHTS = {"b0": (Decimal("0"), Decimal("1")),
           "f75": (Decimal("0"), Decimal("0.75"), Decimal("1"))}

class LedgerSafetyError(ValueError):
    pass

def dec(value, label):
    try:
        x = Decimal(str(value))
    except Exception as exc:
        raise LedgerSafetyError(f"{label} must be numeric") from exc
    if not x.is_finite():
        raise LedgerSafetyError(f"{label} must be finite")
    return x

def new_state(portfolio):
    portfolio = str(portfolio).lower()
    if portfolio not in WEIGHTS:
        raise LedgerSafetyError("unknown portfolio")
    return {
        "schema_version": 1, "mode": "VIRTUAL_LEDGER_NO_SUBMISSION",
        "portfolio": portfolio, "symbol": SYMBOL,
        "initial_equity": str(INITIAL_EQUITY), "cash": str(INITIAL_EQUITY),
        "qty": "0.000", "equity": str(INITIAL_EQUITY),
        "mark_price": None, "mark_date": None,
        "processed_fill_ids": [], "used_client_order_ids": [],
        "pending_intent": None, "last_terminal_order": None,
    }

def validate_state(state):
    if state.get("schema_version") != 1 or state.get("mode") != "VIRTUAL_LEDGER_NO_SUBMISSION":
        raise LedgerSafetyError("unsupported virtual ledger schema or mode")
    if state.get("portfolio") not in WEIGHTS or state.get("symbol") != SYMBOL:
        raise LedgerSafetyError("virtual ledger identity mismatch")
    cash, qty, equity = dec(state.get("cash"), "cash"), dec(state.get("qty"), "qty"), dec(state.get("equity"), "equity")
    if cash < Decimal("-0.01") or qty < 0 or equity <= 0:
        raise LedgerSafetyError("virtual ledger has invalid cash, quantity, or equity")
    fills = state.get("processed_fill_ids")
    ids = state.get("used_client_order_ids")
    if not isinstance(fills, list) or len(fills) != len(set(fills)):
        raise LedgerSafetyError("processed fill IDs must be unique")
    if not isinstance(ids, list) or len(ids) != len(set(ids)):
        raise LedgerSafetyError("used client order IDs must be unique")
    if state.get("pending_intent") is not None and not isinstance(state["pending_intent"], dict):
        raise LedgerSafetyError("pending intent has invalid shape")
    if state.get("mark_date") is not None:
        try: date.fromisoformat(state["mark_date"])
        except Exception: raise LedgerSafetyError("mark date must be ISO date") from None
    return True

def apply_fills(state, fills):
    """Apply unique execution activities once; repeated delivery is idempotent."""
    out = deepcopy(state)
    validate_state(out)
    seen = set(out["processed_fill_ids"])
    cash, qty = dec(out["cash"], "cash"), dec(out["qty"], "qty")
    for fill in fills:
        fill_id = str(fill.get("id", ""))
        if not fill_id:
            raise LedgerSafetyError("fill activity ID is required")
        if fill_id in seen:
            continue
        if fill.get("symbol") != SYMBOL:
            raise LedgerSafetyError("unexpected fill symbol")
        side = str(fill.get("side", "")).lower()
        amount, price = dec(fill.get("qty"), "fill quantity"), dec(fill.get("price"), "fill price")
        if side not in ("buy", "sell") or amount <= 0 or price <= 0:
            raise LedgerSafetyError("fill side, quantity, or price is invalid")
        if side == "buy":
            cash -= amount * price
            qty += amount
            if cash < Decimal("-0.01"):
                raise LedgerSafetyError("fill would make virtual cash negative")
        else:
            if amount > qty:
                raise LedgerSafetyError("sell fill exceeds virtual long quantity")
            qty -= amount
            cash += amount * price
        seen.add(fill_id)
        out["processed_fill_ids"].append(fill_id)
    out["cash"] = str(cash.quantize(Decimal("0.000001")))
    out["qty"] = str(qty.quantize(Decimal("0.001")))
    if out["mark_price"] is not None:
        out["equity"] = str((cash + qty * dec(out["mark_price"], "mark price")).quantize(Decimal("0.01")))
    validate_state(out)
    return out

def mark_to_market(state, session_date, close_price):
    out = deepcopy(state)
    validate_state(out)
    try: d = date.fromisoformat(str(session_date))
    except Exception: raise LedgerSafetyError("mark session must be ISO date") from None
    price = dec(close_price, "close price")
    if price <= 0:
        raise LedgerSafetyError("close price must be positive")
    if out["pending_intent"] is not None:
        raise LedgerSafetyError("cannot mark while an order intent is unresolved")
    if out["mark_date"] is not None:
        prior = date.fromisoformat(out["mark_date"])
        if d < prior:
            raise LedgerSafetyError("mark date cannot move backwards")
        if d == prior:
            if price == dec(out["mark_price"], "prior mark price"):
                return out
            raise LedgerSafetyError("same-session mark price cannot be rewritten")
    cash, qty = dec(out["cash"], "cash"), dec(out["qty"], "qty")
    equity = cash + qty * price
    if equity <= 0:
        raise LedgerSafetyError("marked virtual equity must remain positive")
    out["mark_date"] = d.isoformat()
    out["mark_price"] = str(price)
    out["equity"] = str(equity.quantize(Decimal("0.01")))
    validate_state(out)
    return out

def plan_target(state, *, signal_session, target_weight, reference_price, baseline_weight=None):
    """Build an intent from fill-backed equity; does not mutate state or submit."""
    validate_state(state)
    if state["pending_intent"] is not None:
        raise LedgerSafetyError("unresolved order intent blocks new planning")
    portfolio = state["portfolio"]
    weight, price = dec(target_weight, "target weight"), dec(reference_price, "reference price")
    if weight not in WEIGHTS[portfolio]:
        raise LedgerSafetyError("target weight violates frozen portfolio contract")
    if portfolio == "f75":
        if baseline_weight is None:
            raise LedgerSafetyError("F75 requires the B0 baseline weight")
        baseline = dec(baseline_weight, "baseline weight")
        if baseline not in (Decimal("0"), Decimal("1")) or weight > baseline:
            raise LedgerSafetyError("F75 target violates B0 eligibility")
    if price <= 0:
        raise LedgerSafetyError("reference price must be positive")
    try: session = date.fromisoformat(str(signal_session)).isoformat()
    except Exception: raise LedgerSafetyError("signal session must be ISO date") from None
    equity = dec(state["cash"], "cash") + dec(state["qty"], "qty") * price
    if equity <= 0:
        raise LedgerSafetyError("current virtual equity must be positive")
    target_notional = (equity * weight).quantize(Decimal("0.01"))
    target_qty = (target_notional / price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
    current_qty = dec(state["qty"], "qty")
    delta = target_qty - current_qty
    if delta == 0:
        return None
    quantity = abs(delta).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
    if quantity <= 0:
        raise LedgerSafetyError("rebalance delta is below minimum share precision")
    identity = "|".join((portfolio, SYMBOL, session, str(weight), str(target_qty)))
    client_id = "tb-" + hashlib.sha256(identity.encode()).hexdigest()[:32]
    if client_id in state["used_client_order_ids"]:
        raise LedgerSafetyError("client order ID already used; reconcile rather than resubmit")
    last = state.get("last_terminal_order") or {}
    if last.get("signal_session") == session:
        raise LedgerSafetyError("an order was already completed for this signal session")
    last = state.get("last_terminal_order") or {}
    if last.get("signal_session") == session:
        raise LedgerSafetyError("an order was already completed for this signal session")
    return {
        "portfolio": portfolio, "symbol": SYMBOL, "signal_session": session,
        "target_weight": str(weight), "virtual_equity": str(equity.quantize(Decimal("0.01"))),
        "target_notional": str(target_notional), "current_qty": str(current_qty),
        "target_qty": str(target_qty), "side": "buy" if delta > 0 else "sell",
        "qty": str(quantity), "client_order_id": client_id,
        "endpoint": "https://paper-api.alpaca.markets", "mode": "PLAN_ONLY_NO_SUBMISSION",
    }

def stage_intent(state, intent):
    out = deepcopy(state)
    validate_state(out)
    if out["pending_intent"] is not None:
        raise LedgerSafetyError("another order intent is already unresolved")
    if intent.get("portfolio") != out["portfolio"] or intent.get("symbol") != SYMBOL:
        raise LedgerSafetyError("intent identity does not match ledger")
    cid = intent.get("client_order_id")
    if not cid or cid in out["used_client_order_ids"]:
        raise LedgerSafetyError("client order ID is missing or already used")
    if intent.get("endpoint") != "https://paper-api.alpaca.markets" or intent.get("mode") != "PLAN_ONLY_NO_SUBMISSION":
        raise LedgerSafetyError("intent must be paper-only and plan-only")
    if intent.get("side") not in ("buy", "sell") or dec(intent.get("qty"), "intent quantity") <= 0:
        raise LedgerSafetyError("intent side or quantity is invalid")
    if intent.get("endpoint") != "https://paper-api.alpaca.markets" or intent.get("mode") != "PLAN_ONLY_NO_SUBMISSION":
        raise LedgerSafetyError("intent must be paper-only and plan-only")
    if intent.get("side") not in ("buy", "sell") or dec(intent.get("qty"), "intent quantity") <= 0:
        raise LedgerSafetyError("intent side or quantity is invalid")
    out["used_client_order_ids"].append(cid)
    out["pending_intent"] = {**intent, "submission_state": "STAGED", "broker_order_id": None}
    validate_state(out)
    return out

def mark_submission_outcome(state, outcome, broker_order_id=None):
    out = deepcopy(state)
    validate_state(out)
    pending = out.get("pending_intent")
    if pending is None:
        raise LedgerSafetyError("no staged intent to resolve")
    if outcome not in ("accepted", "unknown", "rejected"):
        raise LedgerSafetyError("submission outcome must be accepted, unknown, or rejected")
    if outcome == "accepted" and not broker_order_id:
        raise LedgerSafetyError("accepted order requires broker order ID")
    pending["submission_state"] = {"accepted":"SUBMITTED", "unknown":"UNKNOWN", "rejected":"REJECTED"}[outcome]
    if broker_order_id:
        pending["broker_order_id"] = str(broker_order_id)
    validate_state(out)
    return out

def reconcile_order(state, broker_order):
    """Reconcile by exact client ID; absence is never permission to retry."""
    out = deepcopy(state)
    validate_state(out)
    pending = out.get("pending_intent")
    if pending is None:
        raise LedgerSafetyError("no pending intent to reconcile")
    if broker_order is None:
        pending["submission_state"] = "UNKNOWN"
        return out
    if broker_order.get("client_order_id") != pending["client_order_id"]:
        raise LedgerSafetyError("broker order client ID does not match staged intent")
    pending["broker_order_id"] = str(broker_order.get("id", ""))
    pending["submission_state"] = str(broker_order.get("status", "unknown")).upper()
    return out

def complete_terminal_intent(state, *, broker_qty, broker_status):
    """Clear a terminal intent only after broker quantity matches fill ledger."""
    out = deepcopy(state)
    validate_state(out)
    pending = out.get("pending_intent")
    if pending is None:
        raise LedgerSafetyError("no pending intent to complete")
    status = str(broker_status).lower()
    if status not in ("filled", "rejected", "canceled", "expired"):
        raise LedgerSafetyError("broker order is not terminal")
    actual = dec(broker_qty, "broker quantity")
    if actual < 0 or abs(actual - dec(out["qty"], "ledger quantity")) > Decimal("0.001"):
        raise LedgerSafetyError("broker position does not reconcile to fill ledger")
    out["last_terminal_order"] = {
        "client_order_id": pending["client_order_id"],
        "broker_order_id": pending.get("broker_order_id"),
        "status": status,
        "signal_session": pending.get("signal_session"),
        "target_weight": pending.get("target_weight"),
    }
    out["pending_intent"] = None
    validate_state(out)
    return out

def state_json(state):
    validate_state(state)
    return json.dumps(state, sort_keys=True, separators=(",", ":"))
