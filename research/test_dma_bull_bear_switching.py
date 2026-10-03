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

from functools import lru_cache
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
TRANSACTION_COST_BPS = (0, 10, 25, 50)

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


@lru_cache(maxsize=None)
def common_index(symbols: tuple[str, ...]) -> pd.DatetimeIndex:
    frames = [load(symbol)["adj_close"].rename(symbol) for symbol in symbols]
    frame = pd.concat(frames, axis=1).dropna()
    return frame.index[(frame.index >= START) & (frame.index <= END)]


@lru_cache(maxsize=None)
def pair_market_data(pair_name: str) -> tuple[pd.DatetimeIndex, pd.Series, pd.Series, pd.Series]:
    spec = PAIRS[pair_name]
    index = common_index((spec["benchmark"], spec["bull"], spec["bear"]))
    benchmark = load(spec["benchmark"])["close"].reindex(index)
    bull_ret = load(spec["bull"])["adj_close"].reindex(index).pct_change().fillna(0.0)
    bear_ret = load(spec["bear"])["adj_close"].reindex(index).pct_change().fillna(0.0)
    return index, benchmark, bull_ret, bear_ret


@lru_cache(maxsize=None)
def benchmark_dma(pair_name: str, dma: int) -> pd.Series:
    index, benchmark, _, _ = pair_market_data(pair_name)
    return benchmark.rolling(dma).mean()


@lru_cache(maxsize=None)
def benchmark_signals(
    pair_name: str,
    bull_dma: int,
    bear_dma: int,
    confirmation: int,
) -> tuple[pd.Series, pd.Series]:
    _, benchmark, _, _ = pair_market_data(pair_name)
    bull_ma = benchmark_dma(pair_name, bull_dma)
    bear_ma = benchmark_dma(pair_name, bear_dma)

    bull_candidate = (benchmark.shift(1) >= bull_ma.shift(1)).fillna(False)
    bear_candidate = (benchmark.shift(1) <= bear_ma.shift(1)).fillna(False)

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
    index, benchmark, bull_ret, bear_ret = pair_market_data(pair_name)
    bull_ready, bear_ready = benchmark_signals(
        pair_name, bull_dma, bear_dma, confirmation
    )

    bull_signal = bull_ready.to_numpy(dtype=bool)
    bear_signal = bear_ready.to_numpy(dtype=bool)
    bull_returns = bull_ret.to_numpy(dtype=float)
    bear_returns = bear_ret.to_numpy(dtype=float)
    n = len(index)

    # Integer states: 0=CASH, 1=BULL, 2=BEAR.
    state_codes = np.zeros(n, dtype=np.int8)
    portfolio_returns = np.zeros(n, dtype=float)

    state = 0
    for i in range(1, n):
        bull = bull_signal[i]
        bear = bear_signal[i]

        if state == 1:
            if bear:
                state = 2
            elif not bull:
                state = 0
        elif state == 2:
            if bull:
                state = 1
            elif not bear:
                state = 0
        else:
            if bull and not bear:
                state = 1
            elif bear and not bull:
                state = 2

        state_codes[i] = state
        if state == 1:
            portfolio_returns[i] = bull_returns[i]
        elif state == 2:
            portfolio_returns[i] = bear_returns[i] * bear_weight

    states = np.empty(n, dtype=object)
    states[state_codes == 0] = "CASH"
    states[state_codes == 1] = "BULL"
    states[state_codes == 2] = "BEAR"

    out = pd.DataFrame(
        {
            "benchmark": benchmark.to_numpy(),
            "portfolio_return": portfolio_returns,
            "state": states,
            "bull_ready": bull_signal,
            "bear_ready": bear_signal,
            "bull_weight": np.where(state_codes == 1, 1.0, 0.0),
            "bear_weight": np.where(state_codes == 2, bear_weight, 0.0),
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
    invalid = frame["state"].isin(["BULL+BEAR", "BEAR+BULL"])
    if invalid.any():
        raise AssertionError("Bull and bear states overlapped.")
    if ((frame["bull_weight"] > 0) & (frame["bear_weight"] > 0)).any():
        raise AssertionError("Bull and bear exposure overlapped.")


def backtest_multi_pair(
    bull_dma: int, bear_dma: int, confirmation: int, bear_weight: float
) -> pd.DataFrame:
    frames = {
        pair: backtest_pair(pair, bull_dma, bear_dma, confirmation, bear_weight)
        for pair in PAIRS
    }
    for frame in frames.values():
        validate_exclusivity(frame)
    index = next(iter(frames.values())).index
    out = pd.DataFrame(
        {
            "portfolio_return": sum(
                frame["portfolio_return"] for frame in frames.values()
            )
            / len(frames)
        },
        index=index,
    )
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

    # Combined results intentionally include both bear-enabled and no-bear
    # controls. This is the direct test of whether inverse exposure adds value
    # beyond the corresponding bull/cash rule.
    combined_rows: list[dict[str, object]] = []
    combined_split_rows: list[dict[str, object]] = []
    combined_controls = list(HEADLINE_CONTROLS) + [
        (bull_dma, bear_dma, confirmation, 0.0)
        for bull_dma, bear_dma, confirmation, _ in HEADLINE_CONTROLS
    ]
    for bull_dma, bear_dma, confirmation, weight in combined_controls:
        frame = backtest_multi_pair(bull_dma, bear_dma, confirmation, weight)
        holdout = frame.loc["2023-01-01":"2026-09-25"]
        label = (
            f"ALL_PAIRS_{bull_dma}DMA_BEAR{bear_dma}DMA_"
            f"C{confirmation}_BEARW{weight:.2f}"
        )
        row = summarize(holdout.assign(state="COMBINED"), label, "holdout")
        state_columns = [f"{pair}_state" for pair in PAIRS]
        for split_name, segment in {
            "full": frame.loc["2010-01-01":"2026-09-25"],
            "train": frame.loc["2010-01-01":"2019-12-31"],
            "validation": frame.loc["2020-01-01":"2022-12-31"],
            "holdout": holdout,
        }.items():
            if not segment.empty:
                split_row = summarize(segment.assign(state="COMBINED"), label, split_name)
                split_states = segment[state_columns]
                split_row.update({
                    "bull_dma": bull_dma, "bear_dma": bear_dma,
                    "confirmation": confirmation, "bear_weight": weight,
                    "bear_enabled": bool(weight > 0),
                    "bull_family_days": int((split_states == "BULL").sum().sum()),
                    "bear_family_days": int((split_states == "BEAR").sum().sum()),
                    "cash_family_days": int((split_states == "CASH").sum().sum()),
                    "mixed_direction_days": int(((split_states == "BULL").any(axis=1) & (split_states == "BEAR").any(axis=1)).sum()),
                })
                combined_split_rows.append(split_row)
        state_matrix = holdout[state_columns]
        row.update(
            {
                "bull_dma": bull_dma,
                "bear_dma": bear_dma,
                "confirmation": confirmation,
                "bear_weight": weight,
                "bear_enabled": bool(weight > 0),
                "bull_family_days": int((state_matrix == "BULL").sum().sum()),
                "bear_family_days": int((state_matrix == "BEAR").sum().sum()),
                "cash_family_days": int((state_matrix == "CASH").sum().sum()),
                "mixed_direction_days": int(
                    (
                        (state_matrix == "BULL").any(axis=1)
                        & (state_matrix == "BEAR").any(axis=1)
                    ).sum()
                ),
            }
        )
        combined_rows.append(row)


    # Transaction-cost stress: one side for cash<->position, two sides for
    # direct bull<->bear switches. Costs are applied to each family sleeve.
    cost_rows: list[dict[str, object]] = []
    for bull_dma, bear_dma, confirmation, weight in HEADLINE_CONTROLS:
        frame = backtest_multi_pair(bull_dma, bear_dma, confirmation, weight)
        state_columns = [f"{pair}_state" for pair in PAIRS]
        states = frame[state_columns]
        transitions = pd.DataFrame(index=states.index)
        for pair in PAIRS:
            prev = states[pair].shift(1).fillna("CASH")
            curr = states[pair]
            transitions[pair] = np.where(
                prev.eq(curr), 0,
                np.where(
                    prev.isin(["BULL", "BEAR"]) & curr.isin(["BULL", "BEAR"]),
                    2,
                    1,
                ),
            )
        transaction_count = transitions.sum(axis=1)
        for cost_bps in TRANSACTION_COST_BPS:
            gross = frame["portfolio_return"].fillna(0.0)
            net = gross - (transaction_count / len(PAIRS)) * (cost_bps / 10000.0)
            cost_frame = pd.DataFrame({"portfolio_return": net}, index=frame.index)
            label = (
                f"ALL_PAIRS_{bull_dma}DMA_BEAR{bear_dma}DMA_"
                f"C{confirmation}_BEARW{weight:.2f}"
            )
            for split_name, segment in {
                "full": cost_frame.loc["2010-01-01":"2026-09-25"],
                "train": cost_frame.loc["2010-01-01":"2019-12-31"],
                "validation": cost_frame.loc["2020-01-01":"2022-12-31"],
                "holdout": cost_frame.loc["2023-01-01":"2026-09-25"],
            }.items():
                if segment.empty:
                    continue
                row = summarize(segment.assign(state="COMBINED"), label, split_name)
                row.update({
                    "bull_dma": bull_dma,
                    "bear_dma": bear_dma,
                    "confirmation": confirmation,
                    "bear_weight": weight,
                    "cost_bps_per_side": cost_bps,
                    "transaction_count": int(transitions.loc[segment.index].sum().sum()),
                })
                cost_rows.append(row)

    # Equal-weight always-bull benchmark using the same five leveraged families.
    benchmark_rows: list[dict[str, object]] = []
    benchmark_daily = pd.DataFrame({pair: pair_market_data(pair)[2] for pair in PAIRS}).mean(axis=1)
    benchmark_frame = pd.DataFrame({"portfolio_return": benchmark_daily}, index=benchmark_daily.index)
    for split_name, segment in {
        "full": benchmark_frame.loc["2010-01-01":"2026-09-25"],
        "train": benchmark_frame.loc["2010-01-01":"2019-12-31"],
        "validation": benchmark_frame.loc["2020-01-01":"2022-12-31"],
        "holdout": benchmark_frame.loc["2023-01-01":"2026-09-25"],
    }.items():
        benchmark_rows.append(summarize(segment.assign(state="BULL"), "ALL_PAIRS_ALWAYS_BULL", split_name))

    pd.DataFrame(combined_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_combined_holdout.csv", index=False
    )
    pd.DataFrame(combined_split_rows + benchmark_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_combined_splits.csv", index=False
    )
    pd.DataFrame(cost_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_cost_stress.csv", index=False
    )
    pd.DataFrame(all_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_matrix.csv", index=False
    )
    pd.DataFrame(annual_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_annual_returns.csv", index=False
    )
    pd.DataFrame(headline_rows).to_csv(
        DATA_DIR / "dma_bull_bear_switch_headline_holdout.csv", index=False
    )

    print("=== DMA BULL/CASH/BEAR SWITCH MATRIX ===")
    print(pd.DataFrame(all_rows).to_string(index=False))
    print("\n=== HEADLINE HOLDOUT CONTROLS ===")
    print(pd.DataFrame(headline_rows).to_string(index=False))
    print("\n=== COMBINED CROSS-FAMILY HOLDOUT CONTROLS ===")
    print(pd.DataFrame(combined_rows).to_string(index=False))
    print("\n=== COMBINED CROSS-FAMILY SPLITS + ALWAYS-BULL BENCHMARK ===")
    print(pd.DataFrame(combined_split_rows + benchmark_rows).to_string(index=False))
    print("\n=== TRANSACTION-COST STRESS ===")
    print(pd.DataFrame(cost_rows).to_string(index=False))


if __name__ == "__main__":
    main()
