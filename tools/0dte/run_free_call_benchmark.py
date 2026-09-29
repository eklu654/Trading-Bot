#!/usr/bin/env python3
"""Run a frozen 0DTESPX SPX 0DTE call-credit-spread comparison.

Prompts for credentials locally; never prints or persists the password/session token.
Writes sanitized aggregate results to artifacts/0dte_call_benchmark.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from auth import get_credentials

import requests

BASE = "https://api.0dtespx.com"
OUT = Path("artifacts/0dte_call_benchmark.json")

# Mirrored delta pairs and timing/exits from the first put-spread benchmark.
CONFIGS = [
    {
        "name": "CALL_16D_0935_50TP",
        "config": {
            "legs": [
                {"direction": "sell", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.16}},
                {"direction": "buy", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.06}},
            ],
            "entry": {"time": "09:35"},
            "exit": {"profit_target_pct": 50, "time": "15:55"},
        },
    },
    {
        "name": "CALL_20D_0935_50TP",
        "config": {
            "legs": [
                {"direction": "sell", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.20}},
                {"direction": "buy", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.10}},
            ],
            "entry": {"time": "09:35"},
            "exit": {"profit_target_pct": 50, "time": "15:55"},
        },
    },
    {
        "name": "CALL_25D_0935_50TP",
        "config": {
            "legs": [
                {"direction": "sell", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.25}},
                {"direction": "buy", "type": "call", "qty": 1,
                 "strike": {"method": "delta", "value": 0.15}},
            ],
            "entry": {"time": "09:35"},
            "exit": {"profit_target_pct": 50, "time": "15:55"},
        },
    },
]


def api(method: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
    headers = kwargs.pop("headers", {})
    headers.setdefault("Content-Type", "application/json")
    if token:
        headers["Authorization"] = token
    response = requests.request(method, BASE + path, headers=headers, timeout=60, **kwargs)
    if not response.ok:
        # Do not include request headers or credentials in diagnostics.
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
        "exec_status", "covered_days", "total_sessions", "window_label",
        "source_hash", "results",
    }
    return {key: snapshot.get(key) for key in allowed if key in snapshot}


def main() -> int:
    email, password = get_credentials()
    print("Logging in...")
    token = login(email, password)
    print("Authenticated. Token will not be printed or saved.")

    output: dict[str, Any] = {
        "platform": "0DTESPX",
        "benchmark": "mirrored_defined_risk_call_credit_spread",
        "configs": [],
    }
    for item in CONFIGS:
        print(f"\nSubmitting {item['name']}...")
        preview = api("POST", "/strategies/preview", token=token,
                      json={"config": item["config"]})
        source_hash = preview.get("snapshot", {}).get("source_hash")
        if not source_hash:
            raise RuntimeError(f"No source_hash returned for {item['name']}.")
        print(f"  source_hash={source_hash}")
        result = wait_for_results(token, source_hash)
        output["configs"].append({
            "name": item["name"],
            "config": item["config"],
            "result": sanitize(result),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nDone. Sanitized results written to: {OUT}")
    print("Sanitized result is ready for analysis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
