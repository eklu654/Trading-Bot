"""Isolated B0 re-entry experiments; see the preregistration before interpreting results.

Run: python research/reentry_isolation.py
This script downloads QQQ/TQQQ once, aligns and saves the exact inputs, then runs
B0, immediate re-entry (R1), and staged +5%/+10% re-entry (R2) on that snapshot.
Signals are close-known and execute at the next open via causal_execution.py.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from .causal_execution import next_open_daily_returns, next_open_cost_equity
except ImportError:  # Support direct execution as a script from the repository root.
    from causal_execution import next_open_daily_returns, next_open_cost_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "2010-01-01"
END = "2026-10-08"
SHOCK = -0.045
RECOVERY_PARTIAL = 0.05
RECOVERY_FULL = 0.10


def download(symbol):
    frame = yf.download(
        symbol, start=START, end=END, auto_adjust=False,
        progress=False, actions=False,
    )
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index().dropna()


def target_exposure(qqq, candidate):
    """Return close-known target exposure; actual execution occurs next open.

    R1 goes back to 100% at the first close after a shock (unless that close
    itself is another qualifying shock). R2 enters 50% at +5% from the running
    low, then 100% at +10%. The running low continues to update until full
    recovery, including after the half-exposure tranche is active.
    """
    if candidate not in {"B0", "R1", "R2", "R2P"}:
        raise ValueError(f"unknown candidate: {candidate}")
    px = qqq["Adj Close"].astype(float).to_numpy()
    daily = qqq["Adj Close"].astype(float).pct_change().fillna(0).to_numpy()
    weights = np.ones(len(qqq), dtype=float)
    defensive = False
    low = np.nan
    staged = False

    for i in range(1, len(qqq)):
        if not defensive and daily[i] <= SHOCK:
            defensive = True
            low = px[i]
            staged = False
            weights[i] = 0.0
            continue

        if not defensive:
            weights[i] = 1.0
            continue

        # A fresh shock while defensive restarts the recovery clock.
        # R2P is the preregistered behavior: once its 50% tranche has
        # activated, retain that tranche through subsequent declines/new lows.
        # R2 is the guarded exploratory variant that resets to cash.
        if daily[i] <= SHOCK:
            low = px[i]
            if candidate == "R2P" and staged:
                weights[i] = 0.5
            else:
                staged = False
                weights[i] = 0.0
            continue

        low = min(low, px[i])
        rebound = px[i] / low - 1.0

        if candidate == "R1":
            # First close after the trigger ends the defensive state.
            defensive = False
            weights[i] = 1.0
        elif candidate == "B0":
            if rebound >= RECOVERY_FULL:
                defensive = False
                weights[i] = 1.0
            else:
                weights[i] = 0.0
        else:  # R2/R2P staged recovery
            if staged:
                if rebound >= RECOVERY_FULL:
                    defensive = False
                    staged = False
                    weights[i] = 1.0
                else:
                    weights[i] = 0.5
            elif rebound >= RECOVERY_PARTIAL:
                staged = True
                weights[i] = 0.5
            else:
                weights[i] = 0.0

    return pd.Series(weights, index=qqq.index, name=candidate)


def return_legs(tqqq):
    adj_open = (
        tqqq["Open"].astype(float) * tqqq["Adj Close"].astype(float)
        / tqqq["Close"].astype(float)
    ).to_numpy()
    adj_close = tqqq["Adj Close"].astype(float).to_numpy()
    overnight = np.zeros(len(tqqq), dtype=float)
    intraday = adj_close / adj_open - 1.0
    overnight[1:] = adj_open[1:] / adj_close[:-1] - 1.0
    return overnight, intraday


def metrics(dates, weights, overnight, intraday, bps):
    if bps == 0:
        daily = next_open_daily_returns(weights, overnight, intraday)
        equity = INITIAL * np.cumprod(1.0 + daily)
    else:
        equity = next_open_cost_equity(
            weights, overnight, intraday, bps, INITIAL
        )
        daily = np.r_[equity[0] / INITIAL - 1.0, equity[1:] / equity[:-1] - 1.0]

    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    years = (dates[-1] - dates[0]).days / 365.25
    if years <= 0 or equity[-1] <= 0:
        raise ValueError("invalid date span or non-positive terminal equity")
    rolling = pd.Series(daily, index=dates).rolling(252, min_periods=252).apply(
        lambda x: np.prod(1.0 + x) - 1.0, raw=True
    )
    executed = np.roll(np.asarray(weights, dtype=float), 1)
    executed[0] = 0.0
    changes = np.abs(np.diff(executed, prepend=0.0))
    return {
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float(np.min(drawdown)),
        "worst_252_session_return": float(rolling.min()) if rolling.notna().any() else np.nan,
        "minimum_equity": float(np.min(equity)),
        "average_target_exposure": float(np.mean(weights)),
        "days_target_0pct": int(np.sum(np.isclose(weights, 0.0))),
        "days_target_50pct": int(np.sum(np.isclose(weights, 0.5))),
        "days_target_100pct": int(np.sum(np.isclose(weights, 1.0))),
        "exposure_changes": int(np.sum(changes > 1e-12)),
        "cost_bps": int(bps),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = download("QQQ")
    t = download("TQQQ")
    idx = q.index.intersection(t.index)
    q = q.reindex(idx).dropna()
    t = t.reindex(idx).dropna()
    if len(q) == 0 or not q.index.equals(t.index):
        raise RuntimeError("QQQ/TQQQ aligned input is empty or inconsistent")

    # Freeze the exact single-download snapshot used by all candidates.
    q.to_csv(OUT / "reentry_frozen_qqq.csv", index_label="Date", float_format="%.12g")
    t.to_csv(OUT / "reentry_frozen_tqqq.csv", index_label="Date", float_format="%.12g")
    overnight, intraday = return_legs(t)
    all_rows = []
    curve_rows = []
    candidates = {}
    for name in ("B0", "R1", "R2", "R2P"):
        w = target_exposure(q, name)
        candidates[name] = w
        for bps in (0, 10, 25, 50):
            all_rows.append({
                "candidate": name,
                **metrics(t.index, w.to_numpy(), overnight, intraday, bps),
            })
        daily = next_open_daily_returns(w.to_numpy(), overnight, intraday)
        equity = INITIAL * np.cumprod(1.0 + daily)
        curve_rows.append(pd.DataFrame({
            "Date": t.index,
            "candidate": name,
            "target_exposure_at_close": w.to_numpy(),
            "daily_return_0bps": daily,
            "equity_0bps": equity,
        }))

    result = pd.DataFrame(all_rows)
    curves = pd.concat(curve_rows, ignore_index=True)
    result.to_csv(OUT / "reentry_isolation_summary.csv", index=False)
    curves.to_csv(OUT / "reentry_isolation_equity.csv", index=False, float_format="%.12g")
    print("INPUT DATES:", t.index[0].date(), "to", t.index[-1].date(), "sessions:", len(t))
    print("\nRE-ENTRY RESULTS")
    print(result.to_string(index=False))

    # Hard accounting invariant: 0-bps cost helper and ordinary causal returns
    # must agree for every candidate on the same frozen input.
    for name, w in candidates.items():
        plain = INITIAL * np.cumprod(
            1.0 + next_open_daily_returns(w.to_numpy(), overnight, intraday)
        )
        helper = next_open_cost_equity(
            w.to_numpy(), overnight, intraday, 0, INITIAL
        )
        if not np.allclose(plain, helper, rtol=1e-11, atol=1e-7):
            raise AssertionError(f"0-bps equity mismatch for {name}")
    print("\nPASS: 0-bps cost-helper equity reconciles to causal daily returns for B0/R1/R2.")


if __name__ == "__main__":
    main()
