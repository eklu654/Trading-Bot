"""ETF-031: TQQQ buy-and-hold robustness and structural-regime stress.

This is a benchmark audit, not a parameter-selection sweep.  The purpose is
to make 100% TQQQ buy-and-hold a first-class offensive control and test how
much of its historical result survives changes in start date, era, path,
transaction costs, and assumed future CAGR.

All price-series comparisons use the same dynamically detected common period
for the direct TQQQ/QQQ/SOXL/SPXL controls. No synthetic pre-launch data is used.

Run from repository root:
    python research/backtest_etf031_tqqq_robustness.py
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from research.test_dma_family_rotation import backtest as family_rotation_backtest
from research.test_dma_family_rotation_risk_overlay import base_weights, build_overlay

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
STARTING_CAPITAL = 5000.0
MA_WINDOW = 200
COSTS_BPS = (0, 10, 25, 50)
ROLLING_WINDOWS = {"1y": 252, "3y": 756, "5y": 1260, "10y": 2520}
FORWARD_HORIZONS_YEARS = (5, 10, 20)
SCENARIO_FRACTIONS = (0.0, 1 / 3, 0.5, 2 / 3, 1.0)


def load(symbol: str) -> pd.Series:
    path = DATA / f"{symbol.lower()}_daily.csv"
    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date").sort_index()
    return frame["adj_close"].astype(float)


def daily_returns(price: pd.Series) -> pd.Series:
    return price.pct_change().fillna(0.0)


def equity_from_returns(ret: pd.Series) -> pd.Series:
    return (1.0 + ret.fillna(0.0)).cumprod()


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def recovery_days(equity: pd.Series) -> int:
    """Calendar days from the worst drawdown trough to recovery of its prior peak."""
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    trough = drawdown.idxmin()
    peak_before = running_peak.loc[trough]
    recovered = equity.loc[trough:][equity.loc[trough:] >= peak_before]
    if recovered.empty:
        return -1
    return int((recovered.index[0] - trough).days)


def cagr(equity: pd.Series) -> float:
    if len(equity) < 2 or equity.iloc[-1] <= 0:
        return np.nan
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / 365.25)
    return float(equity.iloc[-1] ** (1.0 / years) - 1.0)


def summarize(ret: pd.Series, label: str, cost_bps: float = 0.0, time_invested: float | None = None) -> dict[str, object]:
    ret = ret.dropna().astype(float)
    equity = equity_from_returns(ret)
    return {
        "strategy": label,
        "start": ret.index.min(),
        "end": ret.index.max(),
        "observations": len(ret),
        "total_return": equity.iloc[-1] - 1.0,
        "ending_balance_5000": STARTING_CAPITAL * equity.iloc[-1],
        "cagr": cagr(equity),
        "annualized_volatility": ret.std(ddof=1) * np.sqrt(252),
        "max_drawdown": max_drawdown(equity),
        "recovery_days": recovery_days(equity),
        "worst_day": ret.min(),
        "cost_bps": cost_bps,
        "time_invested": time_invested,
    }


def dma_returns(price: pd.Series, cost_bps: float) -> pd.Series:
    """200-DMA/cash with prior-close signal and close-to-close returns."""
    ret = daily_returns(price)
    ma = price.rolling(MA_WINDOW).mean()
    held = (price.shift(1) >= ma.shift(1)).fillna(False)
    turnover = held.astype(float).diff().abs().fillna(held.astype(float))
    return ret.where(held, 0.0) - turnover * (cost_bps / 10000.0)


def buy_hold_returns(price: pd.Series, cost_bps: float) -> pd.Series:
    """Buy once at the first available close; cost is charged once."""
    ret = daily_returns(price)
    out = ret.copy()
    if len(out):
        out.iloc[0] -= cost_bps / 10000.0
    return out


def rolling_stats(ret: pd.Series, label: str, window: int) -> pd.DataFrame:
    rows = []
    if len(ret) < window:
        return pd.DataFrame()
    for end_i in range(window - 1, len(ret)):
        segment = ret.iloc[end_i - window + 1 : end_i + 1]
        equity = equity_from_returns(segment)
        rows.append(
            {
                "strategy": label,
                "window": window,
                "start": segment.index[0],
                "end": segment.index[-1],
                "cagr": cagr(equity),
                "max_drawdown": max_drawdown(equity),
                "ending_multiple": equity.iloc[-1],
            }
        )
    return pd.DataFrame(rows)


def start_date_sensitivity(price: pd.Series) -> pd.DataFrame:
    rows = []
    years = sorted(set(price.index.year))
    for year in years:
        start = price.index[price.index.year == year][0]
        segment = price.loc[start:]
        if len(segment) < 252:
            continue
        ret = daily_returns(segment)
        equity = equity_from_returns(ret)
        rows.append(
            {
                "start_year": year,
                "start_date": start,
                "end": segment.index[-1],
                "cagr": cagr(equity),
                "ending_balance_5000": STARTING_CAPITAL * equity.iloc[-1],
                "max_drawdown": max_drawdown(equity),
            }
        )
    return pd.DataFrame(rows)


def era_sensitivity(price: pd.Series) -> pd.DataFrame:
    eras = (
        ("2010_2014", "2010-01-01", "2014-12-31"),
        ("2015_2019", "2015-01-01", "2019-12-31"),
        ("2020_2022", "2020-01-01", "2022-12-31"),
        ("2023_latest", "2023-01-01", "2099-12-31"),
    )
    rows = []
    for name, start, end in eras:
        segment = price.loc[start:end]
        if len(segment) < 2:
            continue
        ret = daily_returns(segment)
        equity = equity_from_returns(ret)
        rows.append(
            {
                "era": name,
                "start": segment.index[0],
                "end": segment.index[-1],
                "cagr": cagr(equity),
                "ending_multiple": equity.iloc[-1],
                "max_drawdown": max_drawdown(equity),
            }
        )
    return pd.DataFrame(rows)


def exceptional_year_removal(price: pd.Series) -> pd.DataFrame:
    """Remove each calendar year's returns one at a time, preserving all others."""
    ret = daily_returns(price)
    rows = []
    for year in sorted(ret.index.year.unique()):
        reduced = ret.loc[ret.index.year != year]
        equity = equity_from_returns(reduced)
        rows.append(
            {
                "removed_year": year,
                "remaining_observations": len(reduced),
                "cagr": cagr(equity),
                "ending_multiple": equity.iloc[-1],
                "ending_balance_5000": STARTING_CAPITAL * equity.iloc[-1],
                "max_drawdown": max_drawdown(equity),
            }
        )
    return pd.DataFrame(rows)


def path_permutation_stress(price: pd.Series, seed: int = 31031) -> pd.DataFrame:
    """Reorder the exact daily log-return distribution; cumulative return is unchanged."""
    ret = daily_returns(price)
    logret = np.log1p(ret)
    rng = np.random.default_rng(seed)
    rows = []

    def record(name: str, values: np.ndarray) -> None:
        shuffled = pd.Series(np.expm1(values), index=ret.index)
        equity = equity_from_returns(shuffled)
        rows.append(
            {
                "path": name,
                "terminal_multiple": equity.iloc[-1],
                "ending_balance_5000": STARTING_CAPITAL * equity.iloc[-1],
                "max_drawdown": max_drawdown(equity),
                "annualized_volatility": shuffled.std(ddof=1) * np.sqrt(252),
            }
        )

    record("original", logret.to_numpy())
    record("losses_first", np.sort(logret.to_numpy()))
    record("gains_first", np.sort(logret.to_numpy())[::-1])

    values = logret.to_numpy().copy()
    for i in range(10):
        rng.shuffle(values)
        record(f"random_{i + 1:02d}", values.copy())

    # Shuffle contiguous one-year blocks: the exact daily return multiset is
    # preserved while serial ordering changes at a coarser regime scale.
    blocks = [
        logret.to_numpy()[i : i + 252]
        for i in range(0, len(logret), 252)
    ]
    rng.shuffle(blocks)
    record("random_annual_blocks", np.concatenate(blocks))

    return pd.DataFrame(rows)


def lower_future_cagr_scenarios(historical_cagr: float) -> pd.DataFrame:
    """Project fixed future horizons at fractions of the observed historical CAGR."""
    rows = []
    for fraction in SCENARIO_FRACTIONS:
        assumed = historical_cagr * fraction
        for years in FORWARD_HORIZONS_YEARS:
            final = STARTING_CAPITAL * (1.0 + assumed) ** years
            rows.append(
                {
                    "historical_cagr_fraction": fraction,
                    "assumed_future_cagr": assumed,
                    "years": years,
                    "ending_balance_5000": final,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    # Use one common empirical range across the direct offensive ETF controls.
    # This prevents inception-date differences from making the comparisons
    # look better simply because one ETF gets a longer history.
    prices = {symbol: load(symbol) for symbol in ("TQQQ", "QQQ", "SOXL", "SPXL")}
    common_start = max(series.index.min() for series in prices.values())
    common_end = min(series.index.max() for series in prices.values())
    prices = {
        symbol: series.loc[common_start:common_end]
        for symbol, series in prices.items()
    }
    tqqq = prices["TQQQ"]
    qqq = prices["QQQ"]
    soxl = prices["SOXL"]
    spxl = prices["SPXL"]

    controls = []
    for cost in COSTS_BPS:
        controls.append(
            summarize(
                buy_hold_returns(tqqq, cost),
                "TQQQ_buy_and_hold",
                cost,
            )
        )
        controls.append(
            summarize(
                buy_hold_returns(qqq, cost),
                "QQQ_buy_and_hold",
                cost,
            )
        )
        controls.append(
            summarize(
                dma_returns(tqqq, cost),
                "TQQQ_200DMA_cash",
                cost,
            )
        )
        controls.append(
            summarize(
                buy_hold_returns(soxl, cost),
                "SOXL_buy_and_hold",
                cost,
            )
        )
        controls.append(
            summarize(
                buy_hold_returns(spxl, cost),
                "SPXL_buy_and_hold",
                cost,
            )
        )

    # Existing frozen family-rotation controls are included on the same common
    # empirical date range. These are imported unchanged; ETF-031 does not
    # optimize them.
    rotation = family_rotation_backtest(250, 2, 5)
    rotation = rotation.loc[common_start:common_end]
    controls.append(summarize(rotation["portfolio_return"], "BASE_ROTATE_DMA250_TOP2_C5", 0))

    base_w, family_returns = base_weights()
    base_w = base_w.loc[common_start:common_end]
    family_returns = family_returns.loc[common_start:common_end]
    for dd in (0.20, 0.25, 0.30):
        overlay = build_overlay(base_w, family_returns, 20, 0.30, dd)
        for cost in COSTS_BPS:
            stressed = overlay["portfolio_return"] - overlay["turnover"] * cost / 10000.0
            controls.append(summarize(stressed, f"RISK_V30_L20_DD{int(dd*100)}", cost))

    summary = pd.DataFrame(controls)
    summary.to_csv(DATA / "etf031_control_summary.csv", index=False)

    rolling = pd.concat(
        [
            rolling_stats(daily_returns(tqqq), "TQQQ_buy_and_hold", window)
            for window in ROLLING_WINDOWS.values()
        ],
        ignore_index=True,
    )
    # Compact worst rolling-period summary required by ETF-031.
    rolling_summary = (
        rolling.groupby(["strategy", "window"], as_index=False)
        .agg(
            worst_rolling_cagr=("cagr", "min"),
            best_rolling_cagr=("cagr", "max"),
            worst_rolling_drawdown=("max_drawdown", "min"),
            best_rolling_drawdown=("max_drawdown", "max"),
        )
    )
    rolling.to_csv(DATA / "etf031_rolling_stats.csv", index=False)
    rolling_summary.to_csv(DATA / "etf031_rolling_summary.csv", index=False)

    starts = start_date_sensitivity(tqqq)
    starts.to_csv(DATA / "etf031_start_date_sensitivity.csv", index=False)

    eras = era_sensitivity(tqqq)
    eras.to_csv(DATA / "etf031_era_sensitivity.csv", index=False)

    removed = exceptional_year_removal(tqqq)
    removed.to_csv(DATA / "etf031_exceptional_year_removal.csv", index=False)

    paths = path_permutation_stress(tqqq)
    paths.to_csv(DATA / "etf031_path_stress.csv", index=False)

    base_cagr = float(
        summary.loc[
            (summary.strategy == "TQQQ_buy_and_hold") & (summary.cost_bps == 0),
            "cagr",
        ].iloc[0]
    )
    scenarios = lower_future_cagr_scenarios(base_cagr)
    scenarios.to_csv(DATA / "etf031_lower_future_cagr_scenarios.csv", index=False)

    print("=== ETF-031 COMMON PERIOD ===")
    print(f"start={common_start.date()} end={common_end.date()}")
    print("\n=== ETF-031 CONTROLS ===")
    print(
        summary[
            [
                "strategy",
                "cost_bps",
                "cagr",
                "ending_balance_5000",
                "max_drawdown",
                "annualized_volatility",
                "recovery_days",
                "time_invested",
            ]
        ].to_string(index=False)
    )
    print("\n=== ETF-031 ROLLING SUMMARY ===")
    print(rolling_summary.to_string(index=False))
    print("\n=== ETF-031 ERA SENSITIVITY ===")
    print(eras.to_string(index=False))
    print("\n=== ETF-031 PATH STRESS ===")
    print(paths.to_string(index=False))
    print("\n=== ETF-031 LOWER-FUTURE-CAGR SCENARIOS ===")
    print(scenarios.to_string(index=False))


if __name__ == "__main__":
    main()
