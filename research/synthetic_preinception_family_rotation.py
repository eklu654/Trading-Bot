"""Synthetic pre-inception family-rotation stress test (not actual leveraged ETF history).

Fixed daily-reset model: 3x benchmark return minus financing drag on extra 2x notional
and a 0.95% annual fee. Selector is frozen DMA250/top-2/rebalance every 5 sessions.
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
INPUTS = DATA / "synthetic_preinception_inputs"
INPUTS.mkdir(parents=True, exist_ok=True)

DOWNLOAD_START = "1998-01-01"
DOWNLOAD_END = "2003-01-03"
EVAL_END = "2002-12-31"
INITIAL = 5000.0
DMA = 250
TOP_N = 2
CADENCE = 5
FEE_ANNUAL = 0.0095
COSTS_BPS = (0, 25)
FAMILIES = {
    "SP500": {"symbol": "SPY", "kind": "etf"},
    "NASDAQ100": {"symbol": "QQQ", "kind": "etf"},
    "SEMICONDUCTORS": {"symbol": "^SOX", "kind": "index"},
    "DOW30": {"symbol": "DIA", "kind": "etf"},
    "RUSSELL2000": {"symbol": "^RUT", "kind": "index"},
}
FUNDING_SYMBOL = "^IRX"


def download_symbol(symbol: str) -> pd.DataFrame:
    frame = yf.download(
        symbol, start=DOWNLOAD_START, end=DOWNLOAD_END, auto_adjust=False,
        progress=False, actions=False, threads=False
    )
    if frame.empty:
        raise RuntimeError(f"No Yahoo Finance observations returned for {symbol}")
    if isinstance(frame.columns, pd.MultiIndex):
        matched = False
        for level in range(frame.columns.nlevels):
            if symbol in frame.columns.get_level_values(level):
                frame = frame.xs(symbol, axis=1, level=level)
                matched = True
                break
        if not matched and isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
    rename = {
        "Open": "open", "High": "high", "Low": "low", "Close": "close",
        "Adj Close": "adj_close", "Volume": "volume"
    }
    frame = frame.rename(columns=rename)
    if "close" not in frame:
        raise RuntimeError(f"Close column missing for {symbol}: {list(frame.columns)}")
    if "adj_close" not in frame:
        frame["adj_close"] = frame["close"]
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    frame = frame.sort_index()
    frame.to_csv(INPUTS / f"{symbol.replace('^','').lower()}_daily.csv", index_label="Date")
    return frame[["close", "adj_close"]].astype(float)


def synthetic_3x_daily_returns(benchmark_returns: pd.Series, annual_yield_pct: pd.Series,
                               annual_fee: float = FEE_ANNUAL) -> tuple[pd.Series, pd.Series]:
    """Return synthetic daily returns and absorbing proxy wealth, both starting at first session."""
    # The financing rate applied to session t is the prior session's close-known yield.
    lagged_yield = annual_yield_pct.astype(float).shift(1)
    if len(lagged_yield):
        lagged_yield.iloc[0] = float(annual_yield_pct.iloc[0])
    funding_daily = lagged_yield / 100.0 / 252.0
    raw = 3.0 * benchmark_returns.astype(float) - 2.0 * funding_daily - annual_fee / 252.0
    raw = raw.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    daily = pd.Series(0.0, index=raw.index, dtype=float, name="synthetic_3x_return")
    wealth = pd.Series(1.0, index=raw.index, dtype=float, name="synthetic_3x_wealth")
    value = 1.0
    for i, (date, ret) in enumerate(raw.items()):
        if i == 0:
            daily.loc[date] = 0.0
            wealth.loc[date] = value
            continue
        if value <= 0.0:
            daily.loc[date] = 0.0
            wealth.loc[date] = 0.0
            continue
        r = max(-1.0, float(ret))
        value = max(0.0, value * (1.0 + r))
        daily.loc[date] = r
        wealth.loc[date] = value
    return daily, wealth


def selector_weights(benchmarks: pd.DataFrame, proxy_wealth: pd.DataFrame,
                     dma: int = DMA, top_n: int = TOP_N,
                     cadence: int = CADENCE) -> pd.DataFrame:
    """Prior-close signal, equal-weight top-N eligible families, fixed rebalance cadence."""
    if not benchmarks.index.equals(proxy_wealth.index) or not benchmarks.columns.equals(proxy_wealth.columns):
        raise ValueError("benchmark and proxy wealth panels must have identical axes")
    scores, eligible = {}, {}
    for family in benchmarks.columns:
        close = benchmarks[family].astype(float)
        prior_close = close.shift(1)
        prior_dma = close.rolling(dma, min_periods=dma).mean().shift(1)
        score = prior_close / prior_dma - 1.0
        scores[family] = score
        eligible[family] = (prior_close >= prior_dma) & score.notna() & (proxy_wealth[family].shift(1) > 0)
    scores = pd.DataFrame(scores, index=benchmarks.index)
    eligible = pd.DataFrame(eligible, index=benchmarks.index)

    weights = pd.DataFrame(0.0, index=benchmarks.index, columns=benchmarks.columns)
    current = pd.Series(0.0, index=benchmarks.columns, dtype=float)
    last_rebalance = -cadence
    for i, date in enumerate(benchmarks.index):
        if i - last_rebalance >= cadence:
            candidates = scores.loc[date].where(eligible.loc[date]).dropna()
            current[:] = 0.0
            if len(candidates):
                selected = candidates.nlargest(min(top_n, len(candidates))).index
                current.loc[selected] = 1.0 / len(selected)
            last_rebalance = i
        weights.loc[date] = current
    return weights


def first_crossing(equity: pd.Series, threshold: float) -> str:
    hits = equity.index[equity <= threshold]
    return hits[0].date().isoformat() if len(hits) else ""


def summarize_returns(returns: pd.Series, label: str, cost_bps: int,
                      turnover: pd.Series | None = None) -> dict:
    net = returns.astype(float).copy()
    if turnover is not None:
        net = net - turnover.reindex(net.index).fillna(0.0) * cost_bps / 10000.0
    equity = INITIAL * (1.0 + net).cumprod()
    peak = equity.cummax()
    dd = equity / peak - 1.0
    rolling = (1.0 + net).rolling(252, min_periods=252).apply(np.prod, raw=True) - 1.0
    trough_date = dd.idxmin()
    peak_value = peak.loc[trough_date]
    peak_candidates = equity.loc[:trough_date]
    peak_date = peak_candidates.index[peak_candidates.eq(peak_value)][-1]
    def equity_at_or_before(day):
        subset = equity.loc[:day]
        return float(subset.iloc[-1]) if len(subset) else np.nan
    return {
        "strategy": label, "cost_bps": cost_bps,
        "start": equity.index[0].date().isoformat(), "end": equity.index[-1].date().isoformat(),
        "sessions": int(len(equity)), "ending_equity": float(equity.iloc[-1]),
        "max_drawdown": float(dd.min()), "max_drawdown_peak_date": peak_date.date().isoformat(),
        "max_drawdown_trough_date": trough_date.date().isoformat(),
        "max_drawdown_peak_equity": float(peak_value), "max_drawdown_trough_equity": float(equity.loc[trough_date]),
        "equity_2000_year_end": equity_at_or_before("2000-12-31"),
        "equity_2001_year_end": equity_at_or_before("2001-12-31"),
        "equity_2002_year_end": equity_at_or_before("2002-12-31"),
        "minimum_equity": float(equity.min()),
        "worst_252_session_return": float(rolling.min()) if rolling.notna().any() else np.nan,
        "first_below_1pct_initial": first_crossing(equity, INITIAL * 0.01),
        "first_below_0_1pct_initial": first_crossing(equity, INITIAL * 0.001),
        "first_zero_equity": first_crossing(equity, 1e-10),
        "average_exposure": np.nan,
    }


def main():
    symbols = [v["symbol"] for v in FAMILIES.values()] + [FUNDING_SYMBOL]
    raw = {symbol: download_symbol(symbol) for symbol in symbols}
    index = raw[symbols[0]].index
    for symbol in symbols[1:]:
        index = index.intersection(raw[symbol].index)
    index = index.sort_values()
    if len(index) < DMA + 252:
        raise RuntimeError(f"Insufficient common history ({len(index)} sessions) for warm-up and stress window")

    benchmark_close = pd.DataFrame({
        family: raw[spec["symbol"]]["close"].reindex(index)
        for family, spec in FAMILIES.items()
    }, index=index)
    # Use close-to-close price returns for every family so ETF and index
    # benchmarks share one convention; dividends are intentionally excluded.
    benchmark_return_price = benchmark_close.copy()
    benchmark_returns = benchmark_return_price.pct_change().fillna(0.0)
    funding_yield = raw[FUNDING_SYMBOL]["close"].reindex(index).ffill()
    if funding_yield.isna().any():
        raise RuntimeError("Funding yield contains missing observations after alignment")

    proxy_returns, proxy_wealth = {}, {}
    for family in FAMILIES:
        proxy_returns[family], proxy_wealth[family] = synthetic_3x_daily_returns(
            benchmark_returns[family], funding_yield
        )
    proxy_returns = pd.DataFrame(proxy_returns, index=index)
    proxy_wealth = pd.DataFrame(proxy_wealth, index=index)
    weights = selector_weights(benchmark_close, proxy_wealth)
    # Begin only when all benchmark DMAs are warmed up; this is mechanical, not tuned.
    first_valid = None
    for family in benchmark_close.columns:
        # Signals on session t use the prior close and prior-close DMA.
        valid_dates = benchmark_close[family].rolling(DMA, min_periods=DMA).mean().shift(1).dropna().index
        if len(valid_dates) == 0:
            raise RuntimeError(f"No valid prior-close DMA for {family}")
        first_valid = valid_dates[0] if first_valid is None else max(first_valid, valid_dates[0])
    eval_index = index[(index >= first_valid) & (index <= EVAL_END)]
    if len(eval_index) < 252:
        raise RuntimeError(f"Evaluation window too short after warm-up: {len(eval_index)} sessions")

    benchmark_close = benchmark_close.loc[eval_index]
    benchmark_returns = benchmark_returns.loc[eval_index]
    proxy_returns = proxy_returns.loc[eval_index]
    proxy_wealth = proxy_wealth.loc[eval_index]
    weights = weights.loc[eval_index]
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()
    gross = (weights * proxy_returns).sum(axis=1)
    rows, equity_rows = [], []
    for cost in COSTS_BPS:
        row = summarize_returns(gross, "SYNTHETIC_FAMILY_ROTATE_DMA250_TOP2_C5", cost, turnover)
        row["average_exposure"] = float(weights.sum(axis=1).mean())
        rows.append(row)
        net = gross - turnover * cost / 10000.0
        equity = INITIAL * (1 + net).cumprod()
        for date in eval_index:
            equity_rows.append({
                "Date": date, "strategy": "SYNTHETIC_FAMILY_ROTATE_DMA250_TOP2_C5",
                "cost_bps": cost, "equity": float(equity.loc[date]),
                "net_return": float(net.loc[date]), "gross_return": float(gross.loc[date]),
                "exposure": float(weights.loc[date].sum()), "turnover": float(turnover.loc[date]),
                **{f"{fam}_weight": float(weights.loc[date, fam]) for fam in FAMILIES},
                **{f"{fam}_proxy_return": float(proxy_returns.loc[date, fam]) for fam in FAMILIES},
            })

    qqq_proxy = proxy_returns["NASDAQ100"]
    # Buy-and-hold controls charge a one-time entry cost on the first scored session.
    for cost in COSTS_BPS:
        bh = qqq_proxy.copy()
        bh.iloc[0] = (1.0 + float(bh.iloc[0])) * (1.0 - cost / 10000.0) - 1.0
        row = summarize_returns(bh, "SYNTHETIC_TQQQ_PROXY_BUY_HOLD", cost)
        row["average_exposure"] = 1.0
        rows.append(row)
        eq = INITIAL * (1 + bh).cumprod()
        for date in eval_index:
            equity_rows.append({
                "Date": date, "strategy": "SYNTHETIC_TQQQ_PROXY_BUY_HOLD",
                "cost_bps": cost, "equity": float(eq.loc[date]),
                "net_return": float(bh.loc[date]), "gross_return": float(qqq_proxy.loc[date]),
                "exposure": 1.0, "turnover": 1.0 if date == eval_index[0] else 0.0,
            })

    # Unleveraged static 20% initial capital in each underlying benchmark.
    normalized = benchmark_return_price.loc[eval_index] / benchmark_return_price.loc[eval_index].iloc[0]
    basket_equity = INITIAL * normalized.mean(axis=1)
    basket_returns = basket_equity.pct_change().fillna(0.0)
    row = summarize_returns(basket_returns, "UNLEVERAGED_STATIC_EQUAL_WEIGHT_BENCHMARK_BASKET", 0)
    row["average_exposure"] = 1.0
    rows.append(row)
    for date in eval_index:
        equity_rows.append({
            "Date": date, "strategy": "UNLEVERAGED_STATIC_EQUAL_WEIGHT_BENCHMARK_BASKET",
            "cost_bps": 0, "equity": float(basket_equity.loc[date]),
            "net_return": float(basket_returns.loc[date]), "gross_return": float(basket_returns.loc[date]),
            "exposure": 1.0, "turnover": 0.0,
        })

    summary = pd.DataFrame(rows)
    equity_frame = pd.DataFrame(equity_rows)
    summary.to_csv(DATA / "synthetic_preinception_family_summary.csv", index=False)
    equity_frame.to_csv(DATA / "synthetic_preinception_family_equity.csv", index=False, float_format="%.12g")
    weights.to_csv(DATA / "synthetic_preinception_family_weights.csv", index_label="Date")
    proxy_returns.to_csv(DATA / "synthetic_preinception_proxy_returns.csv", index_label="Date")
    proxy_wealth.to_csv(DATA / "synthetic_preinception_proxy_wealth.csv", index_label="Date")
    benchmark_close.to_csv(DATA / "synthetic_preinception_benchmark_close.csv", index_label="Date")

    input_hashes = {
        f: hashlib.sha256((INPUTS / f).read_bytes()).hexdigest()
        for f in sorted(p.name for p in INPUTS.glob("*_daily.csv"))
    }
    manifest = {
        "model": "synthetic 3x daily reset; r3x=3*r-2*(prior_close_IRX_yield/100)/252-0.0095/252; wealth absorbing at zero",
        "not_actual_leveraged_etf_history": True,
        "download_start": DOWNLOAD_START, "download_end_exclusive": DOWNLOAD_END,
        "evaluation_start": eval_index[0].date().isoformat(), "evaluation_end": eval_index[-1].date().isoformat(),
        "sessions": int(len(eval_index)), "initial_equity": INITIAL, "dma": DMA, "top_n": TOP_N,
        "cadence": CADENCE, "cost_bps": list(COSTS_BPS), "fee_annual": FEE_ANNUAL,
        "funding_proxy": FUNDING_SYMBOL, "benchmark_symbols": {k: v["symbol"] for k, v in FAMILIES.items()},
        "input_sha256": input_hashes,
        "summary_sha256": hashlib.sha256((DATA / "synthetic_preinception_family_summary.csv").read_bytes()).hexdigest(),
        "equity_sha256": hashlib.sha256((DATA / "synthetic_preinception_family_equity.csv").read_bytes()).hexdigest(),
        "weights_sha256": hashlib.sha256((DATA / "synthetic_preinception_family_weights.csv").read_bytes()).hexdigest(),
        "proxy_returns_sha256": hashlib.sha256((DATA / "synthetic_preinception_proxy_returns.csv").read_bytes()).hexdigest(),
    }
    (DATA / "synthetic_preinception_family_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("SYNTHETIC PRE-INCEPTION FAMILY ROTATION — NOT ACTUAL ETF HISTORY")
    print(summary.to_string(index=False))
    print("\nPROXY RUIN CHECK")
    print(pd.DataFrame({
        "family": list(FAMILIES),
        "proxy_final_wealth": [float(proxy_wealth[f].iloc[-1]) for f in FAMILIES],
        "proxy_min_wealth": [float(proxy_wealth[f].min()) for f in FAMILIES],
        "proxy_max_drawdown": [float((proxy_wealth[f] / proxy_wealth[f].cummax() - 1.0).min()) for f in FAMILIES],
        "proxy_first_below_1pct": [first_crossing(proxy_wealth[f], 0.01) for f in FAMILIES],
        "proxy_first_below_0_1pct": [first_crossing(proxy_wealth[f], 0.001) for f in FAMILIES],
        "proxy_zero_date": [first_crossing(proxy_wealth[f], 1e-10) for f in FAMILIES],
    }).to_string(index=False))
    print("\nMANIFEST")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
