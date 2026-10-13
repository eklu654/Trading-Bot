"""Fail-closed paper-only emergency liquidation primitives.

This module is intentionally not wired to a scheduled broker mutation yet. It
provides the deterministic intent/reconciliation core that must pass tests
before the monitor may invoke it. It never targets a live Alpaca endpoint.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256

PAPER_URL = "https://paper-api.alpaca.markets"
SYMBOL = "TQQQ"
TRIGGER = Decimal("0.045")


class EmergencyExitBlocked(RuntimeError):
    pass


def _positive(value, label):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise EmergencyExitBlocked(f"{label} is invalid") from None
    if not number.is_finite() or number <= 0:
        raise EmergencyExitBlocked(f"{label} must be positive and finite")
    return number


def validate_trigger(session, qqq_price, prior_close, threshold=TRIGGER):
    """Validate session and -4.5% trigger using only timestamped current inputs."""
    try:
        session = date.fromisoformat(str(session)).isoformat()
    except (TypeError, ValueError):
        raise EmergencyExitBlocked("trigger session must be an ISO date") from None
    price = _positive(qqq_price, "QQQ price")
    close = _positive(prior_close, "prior QQQ close")
    limit = _positive(threshold, "trigger threshold")
    change = price / close - Decimal("1")
    return {
        "session": session,
        "qqq_price": str(price),
        "prior_close": str(close),
        "change_pct": str((change * 100).quantize(Decimal("0.001"))),
        "triggered": change <= -limit,
    }


def build_exit_intent(portfolio, session, position_qty, trigger_hash):
    """Create a deterministic full-liquidation intent; never permit shorting."""
    portfolio = str(portfolio).lower()
    if portfolio not in ("b0", "f75"):
        raise EmergencyExitBlocked("portfolio must be b0 or f75")
    try:
        session = date.fromisoformat(str(session)).isoformat()
    except (TypeError, ValueError):
        raise EmergencyExitBlocked("exit session must be an ISO date") from None
    qty = _positive(position_qty, "broker position quantity")
    if not isinstance(trigger_hash, str) or len(trigger_hash) != 64:
        raise EmergencyExitBlocked("trigger hash must be a SHA-256 hex digest")
    try:
        int(trigger_hash, 16)
    except ValueError:
        raise EmergencyExitBlocked("trigger hash is not hexadecimal") from None
    identity = f"emergency-exit|{portfolio}|{SYMBOL}|{session}|{trigger_hash}|{qty}"
    cid = "tb-" + sha256(identity.encode("utf-8")).hexdigest()[:32]
    return {
        "portfolio": portfolio, "symbol": SYMBOL, "side": "sell",
        "qty": str(qty), "signal_session": session,
        "client_order_id": cid, "endpoint": PAPER_URL,
        "mode": "PAPER_ONLY_EMERGENCY_EXIT", "status": "STAGED",
        "trigger_sha256": trigger_hash, "broker_order_id": None,
    }


def transition_exit(state, status, broker_order=None, broker_position_qty=None):
    """Idempotent exit state transitions; terminal state requires position=0."""
    if not isinstance(state, dict) or state.get("mode") != "PAPER_ONLY_EMERGENCY_EXIT":
        raise EmergencyExitBlocked("invalid emergency-exit state")
    out = deepcopy(state)
    allowed = {"STAGED", "SUBMITTING", "UNKNOWN", "SUBMITTED", "FILLED", "BLOCKED"}
    if status not in allowed:
        raise EmergencyExitBlocked("unsupported emergency-exit status")
    if status == "FILLED":
        if broker_order is None or str(broker_order.get("status", "")).lower() != "filled":
            raise EmergencyExitBlocked("cannot mark exit filled without a broker-filled order")
        if broker_position_qty is None or _positive_or_zero(broker_position_qty) != 0:
            raise EmergencyExitBlocked("cannot mark exit filled until broker position is zero")
        out["broker_position_qty_after"] = "0"
    if broker_order is not None:
        if broker_order.get("client_order_id") != out.get("client_order_id"):
            raise EmergencyExitBlocked("broker order client ID does not match durable exit intent")
        if broker_order.get("symbol") != SYMBOL or str(broker_order.get("side", "")).lower() != "sell":
            raise EmergencyExitBlocked("broker order does not match the TQQQ sell intent")
        out["broker_order_id"] = str(broker_order.get("id") or "") or None
        out["broker_status"] = str(broker_order.get("status") or "").lower()
    out["status"] = status
    return out


def _positive_or_zero(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise EmergencyExitBlocked("broker position quantity is invalid") from None
    if not number.is_finite() or number < 0:
        raise EmergencyExitBlocked("broker position quantity must be finite and non-negative")
    return number


def order_payload(intent):
    if not isinstance(intent, dict) or intent.get("endpoint") != PAPER_URL:
        raise EmergencyExitBlocked("only the Alpaca paper endpoint is permitted")
    if intent.get("mode") != "PAPER_ONLY_EMERGENCY_EXIT" or intent.get("symbol") != SYMBOL:
        raise EmergencyExitBlocked("intent is not a paper TQQQ emergency exit")
    if intent.get("side") != "sell":
        raise EmergencyExitBlocked("emergency exit may only sell")
    qty = _positive(intent.get("qty"), "exit quantity")
    cid = str(intent.get("client_order_id") or "")
    if not cid.startswith("tb-") or len(cid) > 48:
        raise EmergencyExitBlocked("client order ID is invalid")
    return {"symbol": SYMBOL, "qty": str(qty), "side": "sell",
            "type": "market", "time_in_force": "day", "client_order_id": cid}
