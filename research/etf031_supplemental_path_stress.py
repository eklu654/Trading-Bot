"""ETF-031 supplemental path stress: individual observations and severe bear/recovery paths."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
STARTING_CAPITAL = 5000.0


def load_tqqq() -> pd.Series:
    frame = pd.read_csv(DATA / "tqqq_daily.csv", parse_dates=["Date"]).set_index("Date").sort_index()
    return frame["adj_close"].astype(float)


def equity(ret: pd.Series) -> pd.Series:
    return (1.0 + ret).cumprod()


def cagr(eq: pd.Series) -> float:
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    return float(eq.iloc[-1] ** (1.0 / years) - 1.0)


def max_drawdown(eq: pd.Series) -> float:
    return float((eq / eq.cummax() - 1.0).min())


def remove_observation_stress(price: pd.Series) -> pd.DataFrame:
    ret = price.pct_change().fillna(0.0)
    rows = []

    cases = {
        "baseline": ret,
        "remove_largest_positive_day": ret.drop(ret.idxmax()),
        "remove_largest_negative_day": ret.drop(ret.idxmin()),
    }

    # Remove each of the five largest absolute-return observations individually.
    for rank, idx in enumerate(ret.abs().nlargest(5).index, start=1):
        cases[f"remove_extreme_day_{rank}"] = ret.drop(idx)

    for name, series in cases.items():
        eq = equity(series)
        rows.append(
            {
                "scenario": name,
                "removed_date": "" if name == "baseline" else str(
                    next((idx.date() for idx in ret.index if idx not in series.index), "")
                ),
                "ending_balance_5000": STARTING_CAPITAL * eq.iloc[-1],
                "cagr": cagr(eq),
                "max_drawdown": max_drawdown(eq),
            }
        )

    return pd.DataFrame(rows)


def geometric_segment(start: float, end: float, sessions: int) -> np.ndarray:
    return np.full(sessions, (end / start) ** (1.0 / sessions) - 1.0)


def severe_bear_recovery_scenarios() -> pd.DataFrame:
    """Deterministic shock paths; parameters are stress cases, not forecasts.

    Each path starts at $5,000, rises at 13.81% annualized until a shock,
    falls to a specified drawdown, then recovers the lost capital over the
    specified number of years and resumes 13.81% growth.
    """
    annual = 0.1381
    rows = []

    for drawdown in (0.50, 0.70, 0.80, 0.90):
        for recovery_years in (2, 3, 5):
            pre_years = 3
            post_years = 10
            sessions_per_year = 252
            values = [STARTING_CAPITAL]
            growth_daily = (1.0 + annual) ** (1.0 / sessions_per_year) - 1.0

            for _ in range(pre_years * sessions_per_year):
                values.append(values[-1] * (1.0 + growth_daily))

            peak = values[-1]
            trough = peak * (1.0 - drawdown)
            down = geometric_segment(peak, trough, sessions_per_year)
            for r in down:
                values.append(values[-1] * (1.0 + r))

            recovery = geometric_segment(trough, peak, recovery_years * sessions_per_year)
            for r in recovery:
                values.append(values[-1] * (1.0 + r))

            for _ in range(post_years * sessions_per_year):
                values.append(values[-1] * (1.0 + growth_daily))

            idx = pd.date_range("2027-01-04", periods=len(values), freq="B")
            eq = pd.Series(values, index=idx)
            rows.append(
                {
                    "scenario": f"DD{int(drawdown*100)}_recovery_{recovery_years}y",
                    "assumed_baseline_cagr": annual,
                    "shock_drawdown": -drawdown,
                    "recovery_years": recovery_years,
                    "ending_balance_5000": eq.iloc[-1],
                    "max_drawdown": max_drawdown(eq),
                    "calendar_years": (eq.index[-1] - eq.index[0]).days / 365.25,
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    observation = remove_observation_stress(load_tqqq())
    observation.to_csv(DATA / "etf031_individual_observation_stress.csv", index=False)

    bear = severe_bear_recovery_scenarios()
    bear.to_csv(DATA / "etf031_severe_bear_recovery_stress.csv", index=False)

    print("=== INDIVIDUAL OBSERVATION STRESS ===")
    print(observation.to_string(index=False))
    print("\n=== SEVERE BEAR / RECOVERY STRESS ===")
    print(bear.to_string(index=False))


if __name__ == "__main__":
    main()
