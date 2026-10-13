"""Persist a verified QQQ emergency-exit latch to the shared paper ledger.

This script mutates only paper-execution-ledger JSON state; it never contacts
Alpaca's trading endpoint and never submits or cancels an order.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from paper_virtual_portfolio import (
    LedgerSafetyError, activate_emergency_exit_latch, state_json, validate_state,
)


def process(report_path: str, state_dir: str) -> dict:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise LedgerSafetyError("monitor report must be an object")
    if (report.get("status") != "THRESHOLD_BREACHED"
            or report.get("threshold_breached") is not True):
        return {"status": "NO_TRIGGER", "latch_activated": False}
    if report.get("symbol") != "QQQ" or str(report.get("threshold_pct")) != "4.5":
        raise LedgerSafetyError("monitor trigger symbol/threshold mismatch")
    session = str(report.get("session") or "")
    observed = str(report.get("observed_at_utc") or "")
    trade_ts = str(report.get("trade_timestamp") or "")
    try:
        observed_dt = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        trade_dt = datetime.fromisoformat(trade_ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if observed_dt.tzinfo is None or trade_dt.tzinfo is None:
            raise ValueError()
        age = (now - trade_dt.astimezone(timezone.utc)).total_seconds()
        report_age = (now - observed_dt.astimezone(timezone.utc)).total_seconds()
        if age < -30 or age > 180 or report_age < -30 or report_age > 180:
            raise LedgerSafetyError("monitor trigger report is stale")
    except (TypeError, ValueError):
        raise LedgerSafetyError("monitor timestamps are invalid") from None
    try:
        price = Decimal(str(report.get("qqq_price")))
        close = Decimal(str(report.get("prior_close")))
    except (InvalidOperation, TypeError, ValueError):
        raise LedgerSafetyError("monitor trigger prices are invalid") from None
    if not price.is_finite() or not close.is_finite() or price <= 0 or close <= 0:
        raise LedgerSafetyError("monitor trigger prices must be positive and finite")
    if price / close > Decimal("0.955"):
        raise LedgerSafetyError("monitor report does not satisfy the -4.5% trigger")
    identity = {
        "symbol": "QQQ", "session": session, "trade_timestamp": trade_ts,
        "observed_at_utc": observed, "qqq_price": str(price),
        "prior_close": str(close), "threshold_pct": "4.5",
    }
    digest = sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    root = Path(state_dir)
    changes = {}
    for portfolio in ("b0", "f75"):
        path = root / f"{portfolio}_state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        validate_state(state)
        if state.get("portfolio") != portfolio:
            raise LedgerSafetyError(f"{portfolio.upper()} state identity mismatch")
        updated = activate_emergency_exit_latch(
            state, trigger_session=session, qqq_price=price,
            prior_close=close, trigger_sha256=digest,
        )
        changes[path] = (state, updated)
    activated = any(old.get("emergency_exit_latch") is None for old, new in changes.values()
                    if new.get("emergency_exit_latch") is not None)
    for path, (old, new) in changes.items():
        if old != new:
            temp = Path(str(path) + ".tmp")
            temp.write_text(state_json(new) + "\n", encoding="utf-8")
            temp.replace(path)
    return {
        "status": "LATCH_ACTIVATED" if activated else "LATCH_ALREADY_ACTIVE",
        "latch_activated": activated, "portfolios": ["b0", "f75"],
        "trigger_session": session, "trigger_sha256": digest,
        "orders_submitted": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--state-dir", required=True)
    args = parser.parse_args()
    result = process(args.report, args.state_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        reason = str(exc) if isinstance(exc, LedgerSafetyError) else f"latch persistence failed ({type(exc).__name__})"
        print(json.dumps({"status": "BLOCKED", "reason": reason,
                          "latch_activated": False, "orders_submitted": False}, sort_keys=True))
        raise SystemExit(2)
