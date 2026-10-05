from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INITIAL = 5000.0
START = pd.Timestamp("2010-03-11")
END = pd.Timestamp("2026-10-02")
EXPECTED = 4167
DMAS = (100, 125, 150, 175, 200, 225, 250, 300)
BELOW = (0.0, 0.25, 0.50, 0.75, 1.0)
CONFIRM = (0, 1, 3, 5, 10)

def load_frame():
    x = pd.read_csv(DATA / "tqqq_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()
    x = x.loc[START:END].copy()
    if len(x) != EXPECTED:
        raise RuntimeError(f"Expected {EXPECTED} observations, got {len(x)}")
    x["adj_open"] = x["open"] * x["adj_close"] / x["close"]
    return x

def target_weights(close, dma, below, confirm):
    ma = close.rolling(dma).mean()
    above = close >= ma
    out = np.zeros(len(close), dtype=float)
    active = False
    streak = 0
    for i in range(len(close)):
        if i == 0 or pd.isna(ma.iloc[i - 1]):
            continue
        prior_above = bool(above.iloc[i - 1])
        if prior_above:
            streak += 1
        else:
            streak = 0
            active = False
        if confirm == 0:
            active = prior_above
        elif prior_above and streak >= confirm:
            active = True
        if active:
            out[i] = 1.0
        else:
            out[i] = below
    return out

def evaluate(x, dma, below, confirm):
    target = target_weights(x["adj_close"], dma, below, confirm)
    prev = np.roll(target, 1)
    prev[0] = 0.0
    overnight = np.nan_to_num((x["adj_open"] / x["adj_close"].shift(1) - 1).to_numpy(), nan=0.0)
    intraday = np.nan_to_num((x["adj_close"] / x["adj_open"] - 1).to_numpy(), nan=0.0)
    daily = (1 + prev * overnight) * (1 + target * intraday) - 1
    daily[0] = 0.0
    equity = INITIAL * np.cumprod(1 + daily)
    dd = equity / np.maximum.accumulate(equity) - 1
    years = (END - START).days / 365.25
    final = float(equity[-1])
    return {
        "strategy": f"DMA{dma}_BELOW{int(below*100)}_CONFIRM{confirm}",
        "dma": dma,
        "below_exposure": below,
        "confirmation_sessions": confirm,
        "final_balance": final,
        "cagr": (final / INITIAL) ** (1 / years) - 1,
        "max_drawdown": float(dd.min()),
        "avg_exposure": float(target.mean()),
        "position_changes": int(np.count_nonzero(np.diff(target))),
    }

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    x = load_frame()
    rows = [evaluate(x, dma, below, confirm) for dma in DMAS for below in BELOW for confirm in CONFIRM]
    out = pd.DataFrame(rows)
    bh = evaluate(x, 200, 1.0, 0)
    bh["strategy"] = "BUY_AND_HOLD"
    controls = pd.DataFrame([bh])
    out["wealth_rank"] = out["final_balance"].rank(ascending=False, method="min").astype(int)
    out["drawdown_rank"] = out["max_drawdown"].rank(ascending=False, method="min").astype(int)
    out.to_csv(DATA / "tqqq_partial_exposure_reentry_sensitivity.csv", index=False)
    controls.to_csv(DATA / "tqqq_partial_exposure_reentry_control.csv", index=False)
    print(controls.to_string(index=False))
    print(out.sort_values("final_balance", ascending=False).head(30).to_string(index=False))
    print("\nBest by confirmation:")
    print(out.sort_values(["confirmation_sessions","final_balance"], ascending=[True,False]).groupby("confirmation_sessions").head(10).to_string(index=False))

if __name__ == "__main__":
    main()
