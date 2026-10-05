from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INITIAL = 5000.0
DMAS = (100, 125, 150, 175, 200, 225, 250, 300)
BELOW = (0.0, 0.25, 0.50, 0.75, 1.0)
COSTS_BPS = (0, 5, 10, 25, 50)

def load_frame():
    x = pd.read_csv(DATA / "tqqq_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()
    x = x.loc["2010-02-11":"2026-10-02"].copy()
    if len(x) < 4180:
        raise RuntimeError(f"Expected full TQQQ history, got only {len(x)} observations")
    x["adj_open"] = x["open"] * x["adj_close"] / x["close"]
    return x

def evaluate(x, dma, below, cost_bps):
    close = x["adj_close"]
    ma = close.rolling(dma).mean().shift(1)
    target = np.where(ma.notna() & (close.shift(1) >= ma), 1.0, below)
    target = np.where(ma.notna(), target, 0.0)

    overnight = np.nan_to_num(
        (x["adj_open"] / x["adj_close"].shift(1) - 1).to_numpy(), nan=0.0
    )
    intraday = np.nan_to_num(
        (x["adj_close"] / x["adj_open"] - 1).to_numpy(), nan=0.0
    )
    prev = np.roll(target, 1)
    prev[0] = 0.0
    daily = (1 + prev * overnight) * (1 + target * intraday) - 1

    turnover = np.abs(target - prev)
    daily -= turnover * (cost_bps / 10000.0)
    daily[0] = 0.0

    equity = INITIAL * np.cumprod(1 + daily)
    peak = np.maximum.accumulate(equity)
    max_dd = float((equity / peak - 1).min())
    years = (x.index[-1] - x.index[0]).days / 365.25

    return {
        "strategy": f"DMA{dma}_BELOW{int(below * 100)}",
        "dma": dma,
        "below_exposure": below,
        "cost_bps": cost_bps,
        "start_date": x.index[0].date().isoformat(),
        "end_date": x.index[-1].date().isoformat(),
        "observations": len(x),
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": max_dd,
        "avg_exposure": float(target.mean()),
        "position_changes": int(np.count_nonzero(np.abs(np.diff(target)) > 1e-12)),
    }

def buy_and_hold(x):
    daily = np.nan_to_num((x["adj_close"] / x["adj_close"].shift(1) - 1).to_numpy(), nan=0.0)
    equity = INITIAL * np.cumprod(1 + daily)
    peak = np.maximum.accumulate(equity)
    years = (x.index[-1] - x.index[0]).days / 365.25
    return {
        "strategy": "BUY_AND_HOLD",
        "dma": np.nan,
        "below_exposure": 1.0,
        "cost_bps": 0,
        "start_date": x.index[0].date().isoformat(),
        "end_date": x.index[-1].date().isoformat(),
        "observations": len(x),
        "final_balance": float(equity[-1]),
        "cagr": float((equity[-1] / INITIAL) ** (1 / years) - 1),
        "max_drawdown": float((equity / peak - 1).min()),
        "avg_exposure": 1.0,
        "position_changes": 0,
    }

def main():
    x = load_frame()
    rows = [
        evaluate(x, dma, below, cost)
        for dma in DMAS
        for below in BELOW
        for cost in COSTS_BPS
    ]
    out = pd.DataFrame(rows)
    out["wealth_rank"] = out.groupby("cost_bps")["final_balance"].rank(
        ascending=False, method="min"
    ).astype(int)
    out["drawdown_rank"] = out.groupby("cost_bps")["max_drawdown"].rank(
        ascending=False, method="min"
    ).astype(int)

    controls = pd.DataFrame([buy_and_hold(x)])
    out.to_csv(DATA / "tqqq_partial_exposure_full_history.csv", index=False)
    controls.to_csv(DATA / "tqqq_partial_exposure_full_history_control.csv", index=False)

    print(controls.to_string(index=False))
    for cost in COSTS_BPS:
        top = out[(out.cost_bps == cost) & (out.below_exposure < 1)].sort_values(
            "final_balance", ascending=False
        ).head(10)
        print(f"\n=== TOP PARTIAL EXPOSURE @ {cost} BPS ===")
        print(top[[
            "dma", "below_exposure", "final_balance", "cagr",
            "max_drawdown", "avg_exposure", "position_changes"
        ]].to_string(index=False))

if __name__ == "__main__":
    main()
