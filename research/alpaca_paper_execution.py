"""Pure, fail-closed planner for B0/F75 Alpaca paper order intents.
This module never performs HTTP requests and never submits orders.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal, ROUND_DOWN
import hashlib
import json

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
SYMBOL = "TQQQ"
VIRTUAL_ALLOCATION = Decimal("5000.00")
PORTFOLIO_WEIGHTS = {"b0": (Decimal("0"), Decimal("1")),
                     "f75": (Decimal("0"), Decimal("0.75"), Decimal("1"))}

class SafetyGateError(ValueError):
    """Raised when a paper order intent cannot be safely planned."""

@dataclass(frozen=True)
class OrderIntent:
    portfolio: str
    symbol: str
    session_date: str
    target_weight: str
    target_notional: str
    current_qty: str
    target_qty: str
    side: str
    qty: str
    client_order_id: str
    endpoint: str = PAPER_BASE_URL
    mode: str = "PLAN_ONLY_NO_SUBMISSION"
    def as_dict(self):
        return asdict(self)

def _decimal(value, name):
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise SafetyGateError(f"{name} must be numeric") from exc
    if not result.is_finite():
        raise SafetyGateError(f"{name} must be finite")
    return result

def plan_order(*, portfolio, endpoint, account_status, account_blocked,
               trading_blocked, currency, market_is_open, session_date,
               latest_bar_date, price, target_weight, current_qty,
               open_order_count, virtual_equity=VIRTUAL_ALLOCATION, max_bar_age_sessions=0):
    """Return a deterministic paper-only intent or None when already aligned."""
    portfolio = str(portfolio).lower()
    if portfolio not in PORTFOLIO_WEIGHTS:
        raise SafetyGateError("unknown portfolio")
    if endpoint != PAPER_BASE_URL:
        raise SafetyGateError("endpoint must exactly match Alpaca paper API")
    if account_status != "ACTIVE" or account_blocked is not False or trading_blocked is not False:
        raise SafetyGateError("account must be ACTIVE and unblocked")
    if currency != "USD":
        raise SafetyGateError("account currency must be USD")
    if market_is_open is not True:
        raise SafetyGateError("market must be open before order planning")
    if int(open_order_count) != 0:
        raise SafetyGateError("unresolved open orders; reconcile before planning")
    try:
        session = date.fromisoformat(str(session_date))
        bar_date = date.fromisoformat(str(latest_bar_date))
    except Exception as exc:
        raise SafetyGateError("session and bar dates must be ISO dates") from exc
    if bar_date != session:
        raise SafetyGateError("signal bar must match latest completed session")
    if int(max_bar_age_sessions) != 0:
        raise SafetyGateError("stale signal data is not permitted")
    px = _decimal(price, "price")
    weight = _decimal(target_weight, "target_weight")
    current = _decimal(current_qty, "current_qty")
    equity = _decimal(virtual_equity, "virtual_equity")
    if px <= 0:
        raise SafetyGateError("price must be positive")
    if equity <= 0:
        raise SafetyGateError("virtual equity must be positive")
    if current < 0:
        raise SafetyGateError("short positions are not allowed")
    if weight not in PORTFOLIO_WEIGHTS[portfolio]:
        raise SafetyGateError("target weight violates frozen portfolio contract")
    target_notional = (equity * weight).quantize(Decimal("0.01"))
    target_qty = (target_notional / px).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
    delta = target_qty - current
    if delta == 0:
        return None
    side = "buy" if delta > 0 else "sell"
    qty = abs(delta).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
    if qty <= 0:
        raise SafetyGateError("rebalance delta is below minimum share precision")
    identity = "|".join((portfolio, SYMBOL, session.isoformat(), str(weight), str(target_qty)))
    client_id = "tb-" + hashlib.sha256(identity.encode()).hexdigest()[:32]
    return OrderIntent(portfolio, SYMBOL, session.isoformat(), str(weight),
                       str(target_notional), str(current), str(target_qty), side,
                       str(qty), client_id)

def canonical_json(intent):
    """Stable JSON representation for a durable, secret-free decision ledger."""
    return json.dumps(intent.as_dict(), sort_keys=True, separators=(",", ":"))
