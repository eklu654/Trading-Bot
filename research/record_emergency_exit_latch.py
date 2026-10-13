"""Persist QQQ emergency defense and recovery state to the shared paper ledger.

This script mutates only paper-execution-ledger JSON state. It never contacts
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
    LedgerSafetyError, activate_emergency_exit_latch,
    release_emergency_exit_latches, state_json, update_emergency_exit_latch,
    validate_state,
)


def _fresh_report(report):
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
            raise LedgerSafetyError("monitor report is stale")
    except LedgerSafetyError:
        raise
    except (TypeError, ValueError):
        raise LedgerSafetyError("monitor timestamps are invalid") from None


def process(report_path: str, state_dir: str) -> dict:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise LedgerSafetyError("monitor report must be an object")
    status = report.get("status")
    if status in ("MARKET_CLOSED", "STALE_TRADE_FAIL_CLOSED", "ERROR_FAIL_CLOSED"):
        return {"status": "NO_FRESH_SIGNAL", "latch_changed": False, "orders_submitted": False}
    if status not in ("THRESHOLD_BREACHED", "MONITORING"):
        return {"status": "NO_FRESH_SIGNAL", "latch_changed": False, "orders_submitted": False}
    if report.get("symbol") != "QQQ" or str(report.get("threshold_pct")) != "4.5":
        raise LedgerSafetyError("monitor report symbol/threshold mismatch")
    if (status == "THRESHOLD_BREACHED") != (report.get("threshold_breached") is True):
        raise LedgerSafetyError("monitor status and threshold flag disagree")
    _fresh_report(report)
    session = str(report.get("session") or "")
    try:
        price = Decimal(str(report.get("qqq_price")))
        close = Decimal(str(report.get("prior_close")))
    except (InvalidOperation, TypeError, ValueError):
        raise LedgerSafetyError("monitor prices are invalid") from None
    if not price.is_finite() or not close.is_finite() or price <= 0 or close <= 0:
        raise LedgerSafetyError("monitor prices must be positive and finite")
    breached = price / close <= Decimal("0.955")
    if bool(report.get("threshold_breached")) != breached:
        raise LedgerSafetyError("monitor threshold flag does not match prices")
    if status == "THRESHOLD_BREACHED" and not breached:
        raise LedgerSafetyError("monitor report does not satisfy the -4.5% trigger")

    root = Path(state_dir)
    before, states = {}, {}
    for portfolio in ("b0", "f75"):
        path = root / f"{portfolio}_state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        validate_state(state)
        if state.get("portfolio") != portfolio:
            raise LedgerSafetyError(f"{portfolio.upper()} state identity mismatch")
        before[portfolio] = state
        states[portfolio] = state

    activated = False
    # The executor can detect a breach before the scheduled monitor persists both
    # ledgers. Treat any existing latch as the canonical trigger identity and
    # propagate it to the missing portfolio even if QQQ has already rebounded
    # above -4.5% by the time this monitor report is processed.
    canonical = next((states[p].get("emergency_exit_latch")
                      for p in ("b0", "f75")
                      if states[p].get("emergency_exit_latch") is not None), None)
    if breached:
        if canonical is None:
            identity = {
                "symbol": "QQQ", "session": session,
                "trade_timestamp": report.get("trade_timestamp"),
                "observed_at_utc": report.get("observed_at_utc"),
                "qqq_price": str(price), "prior_close": str(close),
                "threshold_pct": "4.5",
            }
            digest = sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            trigger_session, trigger_price, trigger_close = session, price, close
        else:
            digest = canonical["trigger_sha256"]
            trigger_session = canonical["trigger_session"]
            trigger_price = canonical["qqq_price"]
            trigger_close = canonical["prior_close"]
        for portfolio in ("b0", "f75"):
            old_latch = states[portfolio].get("emergency_exit_latch")
            states[portfolio] = activate_emergency_exit_latch(
                states[portfolio], trigger_session=trigger_session, qqq_price=trigger_price,
                prior_close=trigger_close, trigger_sha256=digest,
            )
            activated = activated or (old_latch is None and states[portfolio].get("emergency_exit_latch") is not None)
    elif canonical is not None:
        # Repair a one-sided latch even when the latest report is monitoring.
        for portfolio in ("b0", "f75"):
            old_latch = states[portfolio].get("emergency_exit_latch")
            if old_latch is None:
                states[portfolio] = activate_emergency_exit_latch(
                    states[portfolio], trigger_session=canonical["trigger_session"],
                    qqq_price=canonical["qqq_price"], prior_close=canonical["prior_close"],
                    trigger_sha256=canonical["trigger_sha256"],
                )
                activated = True

    # Track the lowest observed QQQ price while defense is active. The recovery
    # threshold follows the trough, and both portfolios must be flat before the
    # +10% recovery may clear either latch.
    if any(states[p].get("emergency_exit_latch") is not None for p in ("b0", "f75")):
        for portfolio in ("b0", "f75"):
            if states[portfolio].get("emergency_exit_latch") is not None:
                states[portfolio] = update_emergency_exit_latch(
                    states[portfolio], current_qqq_price=price)
        states = release_emergency_exit_latches(
            states, current_qqq_price=price,
            recovered_at_utc=report.get("observed_at_utc"),
        )

    root.mkdir(parents=True, exist_ok=True)
    for portfolio in ("b0", "f75"):
        if before[portfolio] != states[portfolio]:
            path = root / f"{portfolio}_state.json"
            temp = Path(str(path) + ".tmp")
            temp.write_text(state_json(states[portfolio]) + "\n", encoding="utf-8")
            temp.replace(path)

    was_active = any(before[p].get("emergency_exit_latch") is not None for p in ("b0", "f75"))
    is_active = any(states[p].get("emergency_exit_latch") is not None for p in ("b0", "f75"))
    changed = any(before[p] != states[p] for p in ("b0", "f75"))
    if activated:
        result_status = "LATCH_ACTIVATED"
    elif was_active and not is_active:
        result_status = "LATCH_RELEASED_AFTER_RECOVERY"
    elif is_active and changed:
        result_status = "LATCH_RECOVERY_TRACKED"
    elif is_active:
        result_status = "LATCH_ACTIVE_NO_CHANGE"
    else:
        result_status = "NO_TRIGGER"
    latch = next((states[p].get("emergency_exit_latch") for p in ("b0", "f75")
                  if states[p].get("emergency_exit_latch") is not None), None)
    return {
        "status": result_status, "latch_changed": changed,
        "orders_submitted": False, "portfolios": ["b0", "f75"],
        "trigger_session": latch.get("trigger_session") if latch else session,
        "trigger_sha256": latch.get("trigger_sha256") if latch else None,
        "trough_price": latch.get("trough_price") if latch else None,
        "recovery_threshold": latch.get("recovery_threshold") if latch else None,
        "both_portfolios_flat": all(
            states[p].get("pending_intent") is None and Decimal(str(states[p].get("qty"))) == 0
            for p in ("b0", "f75")),
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
                          "latch_changed": False, "orders_submitted": False}, sort_keys=True))
        raise SystemExit(2)
