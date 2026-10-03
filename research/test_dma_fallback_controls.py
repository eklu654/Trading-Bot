"""Test simple, predeclared leveraged-ETF fallback controls when a 200-DMA exit fires.

This is a diagnostic, not an optimizer. Signals use the prior session's close and
200-DMA; returns begin on the next session. The fallback choices are fixed in
code so the comparison does not search for the best substitute.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from research.backtest_dynamic_leverage import load

DATA_DIR = ROOT / "data" / "research"
START = pd.Timestamp("2018-01-01")
END = pd.Timestamp("2025-12-31")
MA_WINDOW = 200

# Fixed, predeclared controls. No search/optimization is performed.
CONTROL_PAIRS = {
    "soxl_to_tqqq": ("SOXL", "TQQQ"),
    "soxl_to_spxl": ("SOXL", "SPXL"),
    "tqqq_to_soxl": ("TQQQ", "SOXL"),
    "tqqq_to_spxl": ("TQQQ", "SPXL"),
    "spxl_to_tqqq": ("SPXL", "TQQQ"),
    "spxl_to_soxl": ("SPXL", "SOXL"),
}


def price_and_signal(symbol: str, index: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series]:
    price = load(symbol)["adj_close"].reindex(index)
    prior = price.shift(1)
    ma = price.rolling(MA_WINDOW).mean().shift(1)
    eligible = (prior >= ma).fillna(False)
    return price, eligible


def build_control(target: str, fallback: str, index: pd.DatetimeIndex) -> pd.DataFrame:
    target_price, target_ok = price_and_signal(target, index)
    fallback_price, fallback_ok = price_and_signal(fallback, index)
    target_ret = target_price.pct_change().fillna(0.0)
    fallback_ret = fallback_price.pct_change().fillna(0.0)

    # Hold target whenever its own 200-DMA rule is active. If target is below
    # its DMA, use fallback only when fallback is itself above its DMA.
    held_target = target_ok
    held_fallback = (~target_ok) & fallback_ok
    portfolio_return = target_ret.where(held_target, fallback_ret.where(held_fallback, 0.0))

    return pd.DataFrame(
        {
            "portfolio_return": portfolio_return,
            "target_held": held_target,
            "fallback_held": held_fallback,
        },
        index=index,
    )


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    equity = (1.0 + daily).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    return {
        "strategy": label,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "total_return": equity.iloc[-1] - 1.0,
        "annualized_return": (equity.iloc[-1]) ** (1 / years) - 1.0,
        "annualized_volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252) if daily.std(ddof=1) else np.nan,
        "sortino": daily.mean() / downside * np.sqrt(252) if pd.notna(downside) and downside else np.nan,
        "max_drawdown": drawdown.min(),
        "worst_day": daily.min(),
        "fallback_days": int(frame["fallback_held"].sum()),
        "cash_days": int((~frame["target_held"] & ~frame["fallback_held"]).sum()),
    }


def main() -> None:
    # Use a common index so every control has identical session boundaries.
    symbols = sorted({s for pair in CONTROL_PAIRS.values() for s in pair})
    prices = {s: load(s)["adj_close"] for s in symbols}
    index = pd.concat(prices, axis=1).dropna().index
    index = index[(index >= START) & (index <= END)]

    rows = []
    artifacts: dict[str, pd.DataFrame] = {}
    for name, (target, fallback) in CONTROL_PAIRS.items():
        frame = build_control(target, fallback, index)
        artifacts[name] = frame
        rows.append(summarize(frame, f"{target}_200DMA_{fallback}_fallback"))

    # Add the cash-only baselines for the target ETFs.
    for symbol in ("SOXL", "TQQQ", "SPXL"):
        frame = build_control(symbol, "SPY", index)
        frame["fallback_held"] = False
        frame["portfolio_return"] = load(symbol)["adj_close"].reindex(index).pct_change().fillna(0.0).where(
            frame["target_held"], 0.0
        )
        rows.append(summarize(frame, f"{symbol}_200DMA_cash"))

    summary = pd.DataFrame(rows)
    summary.to_csv(DATA_DIR / "dma_fallback_controls_2018_2025.csv", index=False)

    stress_windows = {
        "covid_crash": ("2020-02-19", "2020-04-30"),
        "2022_rate_hike_bear": ("2022-01-03", "2022-12-30"),
    }
    stress_rows = []
    for name, (target, fallback) in CONTROL_PAIRS.items():
        frame = artifacts[name]
        for window, (start, end) in stress_windows.items():
            segment = frame.loc[start:end]
            stats = summarize(segment, f"{target}_200DMA_{fallback}_fallback")
            stress_rows.append({"window": window, **stats})
    stress = pd.DataFrame(stress_rows)
    stress.to_csv(DATA_DIR / "dma_fallback_stress_2018_2025.csv", index=False)

    annual_rows = []
    for name, frame in artifacts.items():
        for year, segment in frame.loc[START:END].groupby(frame.loc[START:END].index.year):
            daily = segment["portfolio_return"].fillna(0.0)
            annual_rows.append({
                "strategy": name,
                "year": int(year),
                "return": float((1.0 + daily).prod() - 1.0),
                "fallback_days": int(segment["fallback_held"].sum()),
                "cash_days": int((~segment["target_held"] & ~segment["fallback_held"]).sum()),
            })
    pd.DataFrame(annual_rows).to_csv(DATA_DIR / "dma_fallback_annual_returns_2018_2025.csv", index=False)

    print("2018-2025 DMA fallback controls")
    print(summary.to_string(index=False))
    print("\nFixed stress windows")
    print(stress.to_string(index=False))


if __name__ == "__main__":
    main()
