#!/usr/bin/env python3
"""Run the frozen 0DTE management-timing matrix.

This is a research benchmark, not an optimized strategy search. It keeps
strike deltas and entry time fixed while varying only the mechanical time exit.

The matrix contains:
  * 3 put-credit spreads
  * 3 call-credit spreads
  * 3 iron condors
  * 5 time exits

Total: 45 platform previews.

Prompts for credentials locally; never prints or persists the password/session
token. Writes sanitized aggregate results to
artifacts/0dte_management_timing_matrix.json.
"""

from __future__ import annotations

import getpass
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://api.0dtespx.com"
OUT = Path("artifacts/0dte_management_timing_matrix.json")

STRUCTURES = [
    ("PUT_16D_6D", "put_credit", 0.16, 0.06),
    ("PUT_20D_10D", "put_credit", 0.20, 0.10),
    ("PUT_25D_15D", "put_credit", 0.25, 0.15),
    ("CALL_16D_6D", "call_credit", 0.16, 0.06),
    ("CALL_20D_10D", "call_credit", 0.20, 0.10),
    ("CALL_25D_15D", "call_credit", 0.25, 0.15),
    ("IC_16D_6D", "iron_condor", 0.16, 0.06),
    ("IC_20D_10D", "iron_condor", 0.20, 0.10),
    ("IC_25D_15D", "iron_condor", 0.25, 0.15),
]

EXIT_TIMES = ["11:05", "12:00", "13:30", "15:00", "15:55"]


def make_config(kind: str, short_delta: float, long_delta: float, exit_time: str) -> dict[str, Any]:
    if kind == "put_credit":
        legs = [
            {"direction": "sell", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "buy", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
        ]
    elif kind == "call_credit":
        legs = [
            {"direction": "sell", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "buy", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
        ]
    else:
        legs = [
            {"direction": "buy", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
            {"direction": "sell", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "sell", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "buy", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
        ]

    return {
        "legs": legs,
        "entry": {"time": "09:35"},
        "exit": {"profit_target_pct": 50, "time": exit_time},
    }


def api(method: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
    headers = kwargs.pop("headers", {})
    headers.setdefault("Content-Type", "application/json")
    if token:
        headers["Authorization"] = token
    response = requests.request(
        method, BASE + path, headers=headers, timeout=60, **kwargs
    )
    if not response.ok:
        raise RuntimeError(f"{method} {path} -> HTTP {response.status_code}")
    if not response.content:
        return {}
    return response.json()


def login(email: str, password: str) -> str:
    data = api("POST", "/auth/sessions", json={"email": email, "password": password})
    token = data.get("token")
    if not token:
        raise RuntimeError("Login succeeded but no session token was returned.")
    return token


def wait_for_results(token: str, source_hash: str, timeout_seconds: int = 1800) -> dict[str, Any]:
    started = time.time()
    while True:
        data = api("GET", f"/strategies/preview/{source_hash}/results", token=token)
        status = data.get("exec_status")
        covered = data.get("covered_days")
        total = data.get("total_sessions")
        print(f"  status={status} covered={covered}/{total}", flush=True)

        if status == "idle" and covered == total:
            return data
        if status in {"failed", "error"}:
            return data
        if time.time() - started > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for {source_hash}")
        time.sleep(5)


def sanitize(snapshot: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "exec_status",
        "covered_days",
        "total_sessions",
        "window_label",
        "source_hash",
        "results",
    }
    return {key: snapshot.get(key) for key in allowed if key in snapshot}


def main() -> int:
    email = input("0DTESPX email: ").strip()
    password = getpass.getpass("0DTESPX password (hidden): ")

    print("Logging in...")
    token = login(email, password)
    print("Authenticated. Token will not be printed or saved.")

    output: dict[str, Any] = {
        "platform": "0DTESPX",
        "benchmark": "0dte_management_timing_matrix",
        "entry_time": "09:35",
        "profit_target_pct": 50,
        "exit_times": EXIT_TIMES,
        "configs": [],
    }

    total = len(STRUCTURES) * len(EXIT_TIMES)
    completed = 0

    for name, kind, short_delta, long_delta in STRUCTURES:
        for exit_time in EXIT_TIMES:
            completed += 1
            label = f"{name}_{exit_time.replace(':', '')}"
            print(f"\n[{completed}/{total}] Submitting {label}...")

            config = make_config(kind, short_delta, long_delta, exit_time)
            preview = api(
                "POST",
                "/strategies/preview",
                token=token,
                json={"config": config},
            )
            source_hash = preview.get("snapshot", {}).get("source_hash")
            if not source_hash:
                raise RuntimeError(f"No source_hash returned for {label}.")

            print(f"  source_hash={source_hash}")
            result = wait_for_results(token, source_hash)

            output["configs"].append({
                "name": label,
                "structure": name,
                "kind": kind,
                "short_delta": short_delta,
                "long_delta": long_delta,
                "exit_time": exit_time,
                "config": config,
                "result": sanitize(result),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nDone. Sanitized results written to: {OUT}")
    print("Upload that JSON for analysis; it contains no password or session token.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
