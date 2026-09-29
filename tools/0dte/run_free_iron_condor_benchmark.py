#!/usr/bin/env python3
"""Run a frozen 0DTESPX SPX 0DTE iron-condor delta comparison.

Prompts for credentials locally; never prints or persists the password/session token.
Writes sanitized aggregate results to artifacts/0dte_iron_condor_benchmark.json.
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
OUT = Path("artifacts/0dte_iron_condor_benchmark.json")

# Symmetric short/long delta pairs. This is a first structural comparison,
# not an optimized or deployment-approved specification.
CONFIGS = [
    {
        "name": "IC_16D_6D_0935_50TP",
        "short_delta": 0.16,
        "long_delta": 0.06,
    },
    {
        "name": "IC_20D_10D_0935_50TP",
        "short_delta": 0.20,
        "long_delta": 0.10,
    },
    {
        "name": "IC_25D_15D_0935_50TP",
        "short_delta": 0.25,
        "long_delta": 0.15,
    },
]


def make_config(short_delta: float, long_delta: float) -> dict[str, Any]:
    return {
        "legs": [
            {"direction": "buy", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
            {"direction": "sell", "type": "put", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "sell", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": short_delta}},
            {"direction": "buy", "type": "call", "qty": 1,
             "strike": {"method": "delta", "value": long_delta}},
        ],
        "entry": {"time": "09:35"},
        "exit": {"profit_target_pct": 50, "time": "15:55"},
    }


def api(method: str, path: str, token: str | None = None, **kwargs: Any) -> Any:
    headers = kwargs.pop("headers", {})
    headers.setdefault("Content-Type", "application/json")
    if token:
        headers["Authorization"] = token
    response = requests.request(method, BASE + path, headers=headers, timeout=60, **kwargs)
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
        "exec_status", "covered_days", "total_sessions", "window_label",
        "source_hash", "results",
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
        "benchmark": "symmetric_defined_risk_iron_condor",
        "configs": [],
    }
    for item in CONFIGS:
        print(f"\nSubmitting {item['name']}...")
        config = make_config(item["short_delta"], item["long_delta"])
        preview = api("POST", "/strategies/preview", token=token,
                      json={"config": config})
        source_hash = preview.get("snapshot", {}).get("source_hash")
        if not source_hash:
            raise RuntimeError(f"No source_hash returned for {item['name']}.")
        print(f"  source_hash={source_hash}")
        result = wait_for_results(token, source_hash)
        output["configs"].append({
            "name": item["name"],
            "config": config,
            "result": sanitize(result),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nDone. Sanitized results written to: {OUT}")
    print("Upload that JSON here; it contains no password or session token.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
