"""Download only the data required by ETF-018.

This avoids the full historical research universe when iterating on the
multi-signal transition experiment. The files use the same schema as the
canonical historical dataset builder.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "research"
START = "2010-01-01"
END = "2026-09-28"

SYMBOLS = (
    "TQQQ", "SQQQ", "SPXL", "SPXS", "SOXL", "SOXS",
    "QQQ", "SPY", "SOXX", "DIA", "IWM",
)


def download(symbol: str) -> pd.DataFrame:
    frame = yf.download(
        symbol,
        start=START,
        end=END,
        auto_adjust=False,
        progress=False,
        actions=False,
    )
    if frame.empty:
        raise RuntimeError(f"No price history returned for {symbol}")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Adj Close": "adj_close", "Volume": "volume",
    })
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    return frame.sort_index()


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for symbol in SYMBOLS:
        download(symbol).assign(symbol=symbol).to_csv(DATA / f"{symbol.lower()}_daily.csv")

    vix = download("^VIX")[["close"]].rename(columns={"close": "vix"})
    vix.to_csv(DATA / "vix_daily.csv")
    print(f"ETF-018 dataset ready: {len(SYMBOLS)} ETFs/underlyings plus VIX")


if __name__ == "__main__":
    main()
