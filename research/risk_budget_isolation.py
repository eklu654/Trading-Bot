"""Bounded structural risk-budget test: B0 at 100%, 95%, and 90% target exposure."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import yfinance as yf

from research.causal_execution import next_open_daily_returns, next_open_cost_equity
from research.reentry_isolation import INITIAL, START, END, target_exposure, return_legs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
COSTS = (0, 10, 25, 50)
CAPS = {"B0": 1.00, "RB95": 0.95, "RB90": 0.90}


def download(symbol):
    frame = yf.download(symbol, start=START, end=END, auto_adjust=False,
                        progress=False, actions=False)
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index().dropna()


def apply_cap(b0_weights, cap):
    """Scale invested B0 exposure; preserve B0 cash states exactly."""
    w = np.asarray(b0_weights, dtype=float)
    if not 0.0 < cap <= 1.0:
        raise ValueError("cap must be in (0, 1]")
    return np.where(w == 0.0, 0.0, w * cap)


def measure(dates, weights, overnight, intraday, bps):
    if bps == 0:
        daily = next_open_daily_returns(weights, overnight, intraday)
        equity = INITIAL * np.cumprod(1.0 + daily)
        helper = next_open_cost_equity(weights, overnight, intraday, 0, INITIAL)
        if not np.allclose(equity, helper, rtol=1e-11, atol=1e-7):
            raise AssertionError("zero-cost equity does not reconcile to causal execution helper")
    else:
        equity = next_open_cost_equity(weights, overnight, intraday, bps, INITIAL)
        daily = np.r_[equity[0] / INITIAL - 1.0, equity[1:] / equity[:-1] - 1.0]
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    rolling = pd.Series(daily, index=dates).rolling(252, min_periods=252).apply(
        lambda x: np.prod(1.0 + x) - 1.0, raw=True
    )
    years = (dates[-1] - dates[0]).days / 365.25
    exec_w = np.roll(weights, 1)
    exec_w[0] = 0.0
    return {
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float(dd.min()),
        "worst_252_session_return": float(rolling.min()),
        "minimum_equity": float(equity.min()),
        "average_target_exposure": float(np.mean(weights)),
        "days_cash": int(np.isclose(weights, 0.0).sum()),
        "days_at_cap": int(np.isclose(weights, weights.max()).sum()),
        "days_partial_exposure": int(((weights > 0.0) & (weights < 1.0)).sum()),
        "exposure_changes": int((np.abs(np.diff(exec_w, prepend=0.0)) > 1e-12).sum()),
        "cost_bps": int(bps),
    }, equity, daily


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q, t = download("QQQ"), download("TQQQ")
    idx = q.index.intersection(t.index)
    q, t = q.reindex(idx).dropna(), t.reindex(idx).dropna()
    if len(q) == 0 or not q.index.equals(t.index):
        raise RuntimeError("QQQ/TQQQ aligned input is empty or inconsistent")
    q.to_csv(OUT / "risk_budget_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    t.to_csv(OUT / "risk_budget_frozen_tqqq.csv", index_label="Date", float_format="%.12g")

    b0 = target_exposure(q, "B0").to_numpy(dtype=float)
    overnight, intraday = return_legs(t)
    rows, curves = [], []
    base_zero = None
    for name, cap in CAPS.items():
        w = b0.copy() if name == "B0" else apply_cap(b0, cap)
        for bps in COSTS:
            row, equity, daily = measure(t.index, w, overnight, intraday, bps)
            rows.append({"candidate": name, "cap": cap, **row})
            if bps == 0:
                curves.append(pd.DataFrame({
                    "Date": t.index, "candidate": name,
                    "target_exposure_at_close": w,
                    "daily_return_0bps": daily, "equity_0bps": equity,
                }))
                if name == "B0":
                    base_zero = equity.copy()
    summary = pd.DataFrame(rows)
    curve = pd.concat(curves, ignore_index=True)
    summary.to_csv(OUT / "risk_budget_summary.csv", index=False)
    curve.to_csv(OUT / "risk_budget_equity.csv", index=False, float_format="%.12g")

    # Independent identity: the control curve must match a direct B0 replay.
    direct = INITIAL * np.cumprod(1.0 + next_open_daily_returns(
        b0, overnight, intraday
    ))
    if not np.allclose(base_zero, direct, rtol=1e-11, atol=1e-7):
        raise AssertionError("B0 control identity failed")
    manifest = {
        "start": t.index[0].date().isoformat(),
        "end": t.index[-1].date().isoformat(),
        "sessions": int(len(t)),
        "initial": INITIAL,
        "costs_bps": list(COSTS),
        "caps": CAPS,
        "b0_identity": True,
        "qqq_sha256": hashlib.sha256((OUT / "risk_budget_frozen_qqq.csv").read_bytes()).hexdigest(),
        "tqqq_sha256": hashlib.sha256((OUT / "risk_budget_frozen_tqqq.csv").read_bytes()).hexdigest(),
    }
    import json
    (OUT / "risk_budget_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("RISK-BUDGET RESULTS")
    print(summary.to_string(index=False))
    print("PASS: B0 zero-cost equity identity and all causal accounting checks.")
    print("MANIFEST:", json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
