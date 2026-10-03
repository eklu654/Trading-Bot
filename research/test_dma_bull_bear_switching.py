"""Research bull/cash/bear switching with asymmetric DMA triggers.

Hard portfolio constraint:
    At every modeled session the portfolio has either a bull ETF, a bear ETF,
    or cash. It may NEVER hold a bull and bear ETF simultaneously.

Signals use the prior session's close and benchmark DMA. Returns begin on the
next session. The benchmark index/ETF is used for the signal so the rule does
not depend on the leveraged fund's own path.

This is a research matrix, not a deployment optimizer. Selection must use
chronological train/validation/holdout procedures.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import load

DATA_DIR = ROOT / "data" / "research"
START = pd.Timestamp("2010-01-01")
END = pd.Timestamp("2026-09-25")

PAIRS = {
    "SP500": {"benchmark": "SPY", "bull": "SPXL", "bear": "SPXS"},
    "NASDAQ100": {"benchmark": "QQQ", "bull": "TQQQ", "bear": "SQQQ"},
    "SEMICONDUCTORS": {"benchmark": "SOXX", "bull": "SOXL", "bear": "SOXS"},
    "DOW30": {"benchmark": "DIA", "bull": "UDOW", "bear": "SDOW"},
    "RUSSELL2000": {"benchmark": "IWM", "bull": "TNA", "bear": "TZA"},
}

BULL_DMAS = (100, 150, 200, 250)
BEAR_DMAS = (20, 30, 50, 75, 100)
CONFIRMATIONS = (1, 5)
BEAR_WEIGHTS = (0.25, 0.50, 0.75, 1.00)

HEADLINE_CONTROLS = (
    (200, 200, 1, 1.00),
    (200, 100, 1, 1.00),
    (200, 75, 1, 1.00),
    (200, 50, 1, 1.00),
    (150, 75, 1, 1.00),
    (150, 50, 1, 1.00),
    (100, 50, 1, 1.00),
    (200, 50, 5, 1.00),
    (200, 75, 5, 1.00),
)


def common_index(symbols: list[str]) -> pd.DatetimeIndex:
    frames = [load(symbol)["adj_close"].rename(symbol) for symbol in symbols]
    frame = pd.concat(frames, axis=1).dropna()
    return frame.index[(frame.index >= START) & (frame.index <= END)]


def benchmark_signals(
    benchmark: str,
    index: pd.DatetimeIndex,
    bull_dma: int,
    bear_dma: int,
    confirmation: int,
) -> tuple[pd.Series, pd.Series]:
    price = load(benchmark)["close"].reindex(index)
    bull_ma = price.rolling(bull_dma).mean()
    bear_ma = price.rolling(bear_dma).mean()

    bull_candidate = (price.shift(1) >= bull_ma.shift(1)).fillna(False)
    bear_candidate = (price.shift(1) <= bear_ma.shift(1)).fillna(False)

    bull_ready = bull_candidate.rolling(confirmation).sum().eq(confirmation)
    bear_ready = bear_candidate.rolling(confirmation).sum().eq(confirmation)
    return bull_ready.fillna(False), bear_ready.fillna(False)


def backtest_pair(
    pair_name: str,
    bull_dma: int,
    bear_dma: int,
    confirmation: int,
    bear_weight: float,
) -> pd.DataFrame:
    spec = PAIRS[pair_name]
    index = common_index([spec["benchmark"], spec["bull"], spec["bear"]])
    benchmark = load(spec["benchmark"])["close"].reindex(index)
    bull_price = load(spec["bull"])["adj_close"].reindex(index)
    bear_price = load(spec["bear"])["adj_close"].reindex(index)

    bull_ready, bear_ready = benchmark_signals(
        spec["benchmark"], index, bull_dma, bear_dma, confirmation
    )

    state = "CASH"
    states: list[str] = []
    returns: list[float] = []

    bull_ret = bull_price.pct_change().fillna(0.0)
    bear_ret = bear_price.pct_change().fillna(0.0)

    for i, date in enumerate(index):
        if i == 0:
            states.append(state)
            returns.append(0.0)
            continue

        if state == "BULL":
            if bool(bear_ready.iloc[i]):
                state = "BEAR"
            elif not bool(bull_ready.iloc[i]):
                state = "CASH"
        elif state == "BEAR":
            if bool(bull_ready.iloc[i]):
                state = "BULL"
            elif not bool(bear_ready.iloc[i]):
                state = "CASH"
        else:
            if bool(bull_ready.iloc[i]) and not bool(bear_ready.iloc[i]):
                state = "BULL"
            elif bool(bear_ready.iloc[i]) and not bool(bull_ready.iloc[i]):
                state = "BEAR"

        if state == "BULL":
            daily = float(bull_ret.iloc[i])
        elif state == "BEAR":
            daily = float(bear_ret.iloc[i]) * bear_weight
        else:
            daily = 0.0

        states.append(state)
        returns.append(daily)

    out = pd.DataFrame(
        {
            "benchmark": benchmark,
            "portfolio_return": returns,
            "state": states,
            "bull_ready": bull_ready,
            "bear_ready": bear_ready,
            "bull_weight": [1.0 if s == "BULL" else 0.0 for s in states],
            "bear_weight": [bear_weight if s == "BEAR" else 0.0 for s in states],
        },
        index=index,
    )
    out["portfolio_value"] = (1.0 + out["portfolio_return"]).cumprod()
    out["running_max"] = out["portfolio_value"].cummax()
    out["drawdown"] = out["portfolio_value"] / out["running_max"] - 1.0
    out["bull_symbol"] = spec["bull"]
    out["bear_symbol"] = spec["bear"]
    return out


def summarize(frame: pd.DataFrame, label: str, split: str) -> dict[str, object]:
    if frame.empty:
        return {"strategy": label, "split": split, "observations": 0}

    daily = frame["portfolio_return"].fillna(0.0)
    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    equity = (1.0 + daily).cumprod()
    dd = equity / equity.cummax() - 1.0
    vol = daily.std(ddof=1) * np.sqrt(252)
    downside = daily.where(daily < 0).std(ddof=1)
    return {
        "strategy": label,
        "split": split,
        "start": frame.index.min(),
        "end": frame.index.max(),
        "observations": len(frame),
        "total_return": equity.iloc[-1] - 1.0,
        "cagr": equity.iloc[-1] ** (1 / years) - 1.0,
        "volatility": vol,
        "sharpe": daily.mean() / daily.std(ddof=1) * np.sqrt(252)
        if daily.std(ddof=1)
        else np.nan,
        "sortino": daily.mean() / downside * np.sqrt(252)
        if pd.notna(downside) and downside
        else np.nan,
        "max_drawdown": dd.min(),
        "worst_day": daily.min(),
        "bull_days": int((frame["state"] == "BULL").sum()),
        "bear_days": int((frame["state"] == "BEAR").sum()),
        "cash_days": int((frame["state"] == "CASH").sum()),
    }



def validate_exclusivity(frame: pd.DataFrame) -> None:
    """Validate that one underlying never holds both sides at once."""
    invalid = frame["state"].isin(["BULL+BEAR", "BEAR+BULL"])
    if invalid.any():
        raise AssertionError("Bull and bear states overlapped.")
    if ((frame["bull_weight"] > 0) & (frame["bear_weight"] > 0)).any():
        raise AssertionError("Bull and bear exposure overlapped.")


def backtest_multi_pair(bull_dma: int, bear_dma: int, confirmation: int, bear_weight: float) -> pd.DataFrame:
    """Combine independent sleeves; cross-family bull/bear exposure is allowed."""
    frames = {
        pair: backtest_pair(pair, bull_dma, bear_dma, confirmation, bear_weight)
        for pair in PAIRS
    }
    for frame in frames.values():
        validate_exclusivity(frame)
    index = next(iter(frames.values())).index
    out = pd.DataFrame({
        "portfolio_return": sum(frame["portfolio_return"] for frame in frames.values()) / len(frames)
    }, index=index)
    out["portfolio_value"] = (1.0 + out["portfolio_return"]).cumprod()
    out["running_max"] = out["portfolio_value"].cummax()
    out["drawdown"] = out["portfolio_value"] / out["running_max"] - 1.0
    for pair, frame in frames.items():
        out[f"{pair}_state"] = frame["state"]
        out[f"{pair}_bull_weight"] = frame["bull_weight"] / len(frames)
        out[f"{pair}_bear_weight"] = frame["bear_weight"] / len(frames)
    return out

def main() -> None:
    all_rows: list[dict[str, object]] = []
    annual_rows: list[dict[str, object]] = []
    headline_rows: list[dict[str, object]] = []

    for pair_name in PAIRS:
        configs = [
            (bull_dma, bear_dma, confirmation, weight)
            for bull_dma in BULL_DMAS
            for bear_dma in BEAR_DMAS
            if bear_dma < bull_dma
            for confirmation in CONFIRMATIONS
            for weight in BEAR_WEIGHTS
        ]
        configs.extend(HEADLINE_CONTROLS)
        configs.extend(
            (bull_dma, bear_dma, confirmation, 0.0)
            for bull_dma, bear_dma, confirmation, _ in HEADLINE_CONTROLS
        )

        seen = set()
        for bull_dma, bear_dma, confirmation, weight in configs:
            key = (bull_dma, bear_dma, confirmation, weight)
            if key in seen:
                continue
            seen.add(key)

            frame = backtest_pair(
                pair_name, bull_dma, bear_dma, confirmation, weight
            )
            validate_exclusivity(frame)

            label = (
                f"{pair_name}_{bull_dma}DMA_BEAR{bear_dma}DMA_"
                f"C{confirmation}_BEARW{weight:.2f}"
            )

            splits = {
                "full": frame.loc["2010-01-01":"2026-09-25"],
                "train": frame.loc["2010-01-01":"2019-12-31"],
                "validation": frame.loc["2020-01-01":"2022-12-31"],
                "holdout": frame.loc["2023-01-01":"2026-09-25"],
            }
            for split, segment in splits.items():
                if not segment.empty:
                    all_rows.append(summarize(segment, label, split))

            for year, segment in frame.groupby(frame.index.year):
                daily = segment["portfolio_return"].fillna(0.0)
                annual_rows.append(
                    {
                        "pair": pair_name,
                        "bull_dma": bull_dma,
                        "bear_dma": bear_dma,
                        "confirmation": confirmation,
                        "bear_weight": weight,
                        "year": int(year),
                        "return": float((1.0 + daily).prod() - 1.0),
                        "bull_days": int((segment["state"] == "BULL").sum()),
                        "bear_days": int((segment["state"] == "BEAR").sum()),
                        "cash_days": int((segment["state"] == "CASH").sum()),
                    }
                )

            if (bull_dma, bear_dma, confirmation, weight) in HEADLINE_CONTROLS:
                headline_rows.append(
                    {
                        "pair": pair_name,
                        "bull_dma": bull_dma,
                        "bear_dma": bear_dma,
                        "confirmation": confirmation,
                        "bear_weight": weight,
                        **summarize(splits["holdout"], label, "holdout"),
                    }
                )

    combined_rows: list[dict[str, object]] = []
    for bull_dma, bear_dma, confirmation, weight in HEADLINE_CONTROLS:
        frame = backtest_multi_pair(bull_dma, bear_dma, confirmation, weight)
        holdout = frame.loc["2023-01-01":"2026-09-25"]
        row = summarize(holdout.assign(state="COMBINED"), "ALL_PAIRS", "holdout")
        row.update({"bull_dma": bull_dma, "bear_dma": bear_dma, "confirmation": confirmation, "bear_weight": weight})
        combined_rows.append(row)

    pd.DataFrame(combined_rows).to_csv(DATA_DIR / "dma_bull_bear_switch_combined_holdout.csv", index=False)

    pd.DataFrame(all_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_matrix.csv", index=False
    )
    pd.DataFrame(annual_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_annual_returns.csv", index=False
    )
    pd.DataFrame(headline_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_headline_holdout.csv",
        index=False,
    )

    print("=== DMA BULL/CASH/BEAR SWITCH MATRIX ===")
    print(pd.DataFrame(all_rows).to_string(index=False))
    print("\n=== HEADLINE HOLDOUT CONTROLS ===")
    print(pd.DataFrame(headline_rows).to_string(index=False))
    print("\n=== COMBINED CROSS-FAMILY HOLDOUT CONTROLS ===")
    print(pd.DataFrame(combined_rows).to_string(index=False))


if __name__ == "__main__":
    main()
