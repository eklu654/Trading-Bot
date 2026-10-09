"""Unified synthetic 3x QQQ survivability comparison for B0 and buy-and-hold.

This is a pre-TQQQ stress proxy, not actual TQQQ performance. All strategies
use one frozen QQQ download, one set of synthetic leveraged overnight/intraday
returns, and the shared causal close-to-next-open execution engine.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

try:
    from .causal_execution import next_open_daily_returns
    from .reentry_isolation import target_exposure
except ImportError:
    from causal_execution import next_open_daily_returns
    from reentry_isolation import target_exposure

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "1999-03-10"
END = "2026-10-03"
DOTCOM_START = "2000-01-01"
DOTCOM_END = "2002-12-31"


def download_qqq():
    x = yf.download( "QQQ", start=START, end=END, auto_adjust=False,
                     progress=False, actions=False)
    if x.empty:
        raise RuntimeError("No QQQ history returned.")
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x.index = pd.to_datetime(x.index).tz_localize(None)
    x.index.name = "Date"
    x = x.sort_index()
    required = {"Open", "Close", "Adj Close"}
    if not required.issubset(x.columns):
        raise RuntimeError(f"Missing QQQ columns: {sorted(required - set(x.columns))}")
    return x.dropna(subset=["Open", "Close", "Adj Close"])


def synthetic_3x_legs_from_adjusted_prices(adj_open, adj_close):
    """Build causal legs for a daily-reset 3x fund from adjusted QQQ prices."""
    adj_open = pd.Series(adj_open, index=getattr(adj_open, "index", None), dtype=float)
    adj_close = pd.Series(adj_close, index=adj_open.index, dtype=float)
    overnight = (adj_open / adj_close.shift(1) - 1.0).fillna(0.0).to_numpy()
    intraday = (adj_close / adj_open - 1.0).fillna(0.0).to_numpy()
    # The fund has 3x exposure set at the prior close. After the overnight
    # move, its notional-to-NAV ratio changes; do not independently multiply
    # both sub-day returns by 3 (that would effectively reset leverage twice).
    overnight_gross = 1.0 + 3.0 * overnight
    overnight_3x = np.clip(overnight_gross, 0.0, None) - 1.0
    intraday_leverage = np.divide(
        3.0 * (1.0 + overnight), overnight_gross,
        out=np.zeros_like(overnight), where=overnight_gross > 0.0,
    )
    intraday_gross = np.clip(1.0 + intraday_leverage * intraday, 0.0, None)
    # If the synthetic fund was wiped out overnight, it remains at zero.
    intraday_gross[overnight_gross <= 0.0] = 0.0
    intraday_3x = intraday_gross - 1.0
    return overnight_3x, intraday_3x


def synthetic_3x_legs(qqq):
    """Return daily-reset 3x overnight/intraday returns, clipped at -100%."""
    adj_open = (qqq["Open"].astype(float) * qqq["Adj Close"].astype(float)
                / qqq["Close"].astype(float))
    return synthetic_3x_legs_from_adjusted_prices(adj_open, qqq["Adj Close"])


def first_crossing(dates, values, threshold):
    ix = np.flatnonzero(np.asarray(values) <= threshold)
    return dates[int(ix[0])].date().isoformat() if len(ix) else ""


def summarize(dates, weights, daily_returns, equity, label):
    dates = pd.DatetimeIndex(dates)
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    years = (dates[-1] - dates[0]).days / 365.25
    trough_i = int(np.argmin(equity))
    peak_i = int(np.argmax(equity[:trough_i + 1]))
    dot_mask = (dates >= DOTCOM_START) & (dates <= DOTCOM_END)
    dot_ix = np.flatnonzero(dot_mask)
    if not len(dot_ix):
        raise RuntimeError("Input does not cover the dot-com window.")
    dot_trough_i = int(dot_ix[np.argmin(equity[dot_ix])])
    dot_peak_i = int(np.argmax(equity[:dot_trough_i + 1]))
    dot_peak = float(equity[dot_peak_i])
    dot_trough = float(equity[dot_trough_i])
    recovery = np.flatnonzero(equity[dot_trough_i:] >= dot_peak)
    recovery_i = dot_trough_i + int(recovery[0]) if len(recovery) else None
    dot_end_i = int(dot_ix[-1])
    min_i = int(np.argmin(equity))
    return {
        "strategy": label,
        "start": dates[0].date().isoformat(),
        "end": dates[-1].date().isoformat(),
        "observations": len(dates),
        "starting_balance": INITIAL,
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1.0 / years) - 1.0),
        "max_drawdown": float(dd.min()),
        "minimum_equity": float(equity[min_i]),
        "minimum_equity_date": dates[min_i].date().isoformat(),
        "first_crossing_dd_99pct": first_crossing(dates, dd, -0.99),
        "first_crossing_dd_99_9pct": first_crossing(dates, dd, -0.999),
        "first_zero_equity_date": first_crossing(dates, equity, 0.0),
        "average_target_exposure": float(np.mean(weights)),
        "dotcom_window_return": float(equity[dot_end_i] / equity[int(dot_ix[0])] - 1.0),
        "dotcom_peak_date_before_trough": dates[dot_peak_i].date().isoformat(),
        "dotcom_peak_balance_before_trough": dot_peak,
        "dotcom_trough_date": dates[dot_trough_i].date().isoformat(),
        "dotcom_trough_balance": dot_trough,
        "dotcom_drawdown_from_prior_peak": float(dot_trough / dot_peak - 1.0),
        "dotcom_peak_to_trough_sessions": int(dot_trough_i - dot_peak_i),
        "dotcom_recovery_date_to_peak": dates[recovery_i].date().isoformat() if recovery_i is not None else "",
        "dotcom_recovered_peak_by_end": bool(recovery_i is not None),
    }


def run_on_frame(qqq):
    overnight_3x, intraday_3x = synthetic_3x_legs(qqq)
    b0 = target_exposure(qqq, "B0").to_numpy(dtype=float)
    hold = np.ones(len(qqq), dtype=float)
    rows, paths = [], []
    for label, weights in [("B0_QQQ_shock_recovery", b0),
                           ("synthetic_3x_QQQ_buy_hold", hold)]:
        daily = next_open_daily_returns(weights, overnight_3x, intraday_3x)
        equity = INITIAL * np.cumprod(1.0 + daily)
        row = summarize(qqq.index, weights, daily, equity, label)
        rows.append(row)
        peak = np.maximum.accumulate(equity)
        paths.append(pd.DataFrame({
            "Date": qqq.index,
            "strategy": label,
            "target_exposure_at_close": weights,
            "synthetic_3x_overnight_return": overnight_3x,
            "synthetic_3x_intraday_return": intraday_3x,
            "daily_strategy_return": daily,
            "equity": equity,
            "drawdown": equity / peak - 1.0,
        }))
    return pd.DataFrame(rows), pd.concat(paths, ignore_index=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    qqq = download_qqq()
    summary, paths = run_on_frame(qqq)
    qqq.to_csv(OUT / "synthetic_b0_survivability_frozen_qqq.csv",
               index_label="Date", float_format="%.12g")
    summary.to_csv(OUT / "synthetic_b0_survivability_summary.csv", index=False)
    paths.to_csv(OUT / "synthetic_b0_survivability_paths.csv",
                 index=False, float_format="%.12g")
    print("INPUT:", qqq.index[0].date(), "to", qqq.index[-1].date(),
          "sessions:", len(qqq))
    print(summary.to_string(index=False))
    # Shared-engine invariant: all candidates have the same input and return legs.
    assert set(paths["strategy"].unique()) == {
        "B0_QQQ_shock_recovery", "synthetic_3x_QQQ_buy_hold"
    }
    assert summary["first_zero_equity_date"].eq("").all() or (
        summary.loc[summary["first_zero_equity_date"] != "", "first_zero_equity_date"].notna().all()
    )
    print("PASS: B0 and synthetic buy-and-hold share frozen inputs, leverage legs, and causal execution.")


if __name__ == "__main__":
    main()
