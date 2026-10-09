"""Dot-com-era synthetic TQQQ survivability research.

TQQQ launched in 2010, so this reconstructs a daily-reset 3x Nasdaq-100 proxy
from QQQ total-return-adjusted daily returns beginning with QQQ inception.

This is a stress/survivability study, not a claim that synthetic TQQQ exactly
matches a fund that did not exist in 2000. It answers the path question:
what would a daily-reset 3x Nasdaq-100 exposure have done through the
2000-2002 collapse and subsequent recovery?

All strategies start with $5,000. Signals use only prior-session information
and affect the next session. No parameter search is performed in this script.
The modern-era candidates are frozen from the completed TQQQ research:
- buy-and-hold
- 200-DMA, immediate re-entry
- 200-DMA, 3-session re-entry
- 200-DMA, next-open execution
- 225-DMA, immediate re-entry
- 250-DMA, 10-session re-entry

For the pre-TQQQ era, the synthetic leveraged price is built from QQQ's
adjusted close-to-close total-return series. This preserves daily leverage
resetting but does not model actual TQQQ fees, financing, tracking error,
bid/ask spreads, or fund operations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
try:
    from .synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices
except ImportError:
    from synthetic_b0_unified_survivability import synthetic_3x_legs_from_adjusted_prices

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research"
INITIAL = 5000.0
START = "1999-03-10"
END = "2026-10-03"
DMAS = tuple(range(100, 301, 25))
EXPOSURES = (0.0, 0.25, 0.50, 0.75, 1.0)


def download_qqq() -> pd.DataFrame:
    frame = yf.download(
        "QQQ",
        start=START,
        end=END,
        auto_adjust=False,
        progress=False,
        actions=False,
    )
    if frame.empty:
        raise RuntimeError("No QQQ history returned.")
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
        }
    )
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    frame = frame.sort_index()
    required = {"open", "close", "adj_close"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"QQQ is missing fields: {sorted(missing)}")
    return frame.dropna(subset=["close", "adj_close"])


def build_synthetic(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()

    # Daily-reset 3x total-return proxy. The first observation establishes the
    # synthetic price level; subsequent closes compound 3x the QQQ adjusted
    # close-to-close return.
    qqq_ret = out["adj_close"].pct_change().fillna(0.0)
    growth = (1.0 + 3.0 * qqq_ret).clip(lower=0.0)
    out["synthetic_tqqq_close"] = INITIAL * growth.cumprod()

    # Synthetic next-open execution path. We need an adjusted QQQ open that
    # incorporates the same dividend/split adjustment as adjusted close.
    out["adj_open"] = out["open"] * out["adj_close"] / out["close"]
    overnight = out["adj_open"] / out["adj_close"].shift(1) - 1.0
    intraday = out["adj_close"] / out["adj_open"] - 1.0
    overnight = overnight.fillna(0.0)
    intraday = intraday.fillna(0.0)
    out["synthetic_tqqq_open"] = (
        INITIAL * (1.0 + 3.0 * overnight).clip(lower=0.0)
        * (1.0 + 3.0 * intraday).clip(lower=0.0)
    )
    return out


def target_weights(
    synthetic_close: pd.Series,
    dma: int,
    below_exposure: float,
    reentry_sessions: int,
) -> np.ndarray:
    ma = synthetic_close.rolling(dma).mean()
    close = synthetic_close.to_numpy()
    ma_np = ma.to_numpy()
    weights = np.zeros(len(close), dtype=float)
    above_count = 0
    active = False

    # Signal at t uses close[t] and MA[t], then controls t+1. We keep the
    # implementation explicit so the re-entry rule cannot accidentally peek.
    for i in range(len(close)):
        if not np.isfinite(ma_np[i]):
            active = False
            above_count = 0
            weights[i] = 0.0
            continue

        if close[i] >= ma_np[i]:
            if reentry_sessions == 0:
                active = True
                above_count = 1
            elif not active:
                above_count += 1
                if above_count >= reentry_sessions:
                    active = True
            else:
                above_count = reentry_sessions
        else:
            active = False
            above_count = 0

        weights[i] = 1.0 if active else below_exposure
    return weights


def evaluate(
    frame: pd.DataFrame,
    weights: np.ndarray,
    label: str,
) -> tuple[dict[str, object], pd.DataFrame]:
    # Reconstruct the same next-open execution convention used by the
    # modern TQQQ research: the prior target carries the overnight move and
    # the current target applies to the intraday move.
    overnight = (
        frame["adj_open"] / frame["adj_close"].shift(1) - 1.0
    ).fillna(0.0).to_numpy()
    intraday = (
        frame["adj_close"] / frame["adj_open"] - 1.0
    ).fillna(0.0).to_numpy()
    overnight_3x, intraday_3x = synthetic_3x_legs_from_adjusted_prices(
        frame["adj_open"], frame["adj_close"]
    )

    # weights[i] is the decision made at close i. It becomes executable at open i+1.
    # Therefore overnight exposure on day i comes from the prior position (decision i-2),
    # while intraday exposure comes from the decision executed at open i (decision i-1).
    exec_w = np.roll(weights, 1)
    exec_w[0] = 0.0
    prev_w = np.roll(exec_w, 1)
    prev_w[0] = 0.0
    daily = (1.0 + prev_w * overnight_3x) * (1.0 + exec_w * intraday_3x) - 1.0
    equity = INITIAL * np.cumprod(1.0 + daily)
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0

    # Formal dot-com crash metrics are computed on the fixed 2000-01-01
    # through 2002-12-31 window. The crash peak is the highest equity reached
    # in that window before the window trough; recovery means returning to
    # that exact pre-trough peak. This avoids the old bug where a later,
    # unrelated global peak could be mislabeled as the peak before the trough.
    crash_mask = (frame.index >= "2000-01-01") & (frame.index <= "2002-12-31")
    crash_idx = np.flatnonzero(crash_mask)
    if len(crash_idx):
        crash_equity = equity[crash_idx]
        trough_rel = int(np.argmin(crash_equity))
        trough_idx = int(crash_idx[trough_rel])
        pre_trough_idx = crash_idx[: trough_rel + 1]
        peak_rel = int(np.argmax(equity[pre_trough_idx]))
        peak_idx = int(pre_trough_idx[peak_rel])
        peak_value = float(equity[peak_idx])
        trough_value = float(equity[trough_idx])
        recovery_idx = None
        after = np.flatnonzero(equity[trough_idx:] >= peak_value)
        if len(after):
            recovery_idx = trough_idx + int(after[0])
    else:
        peak_idx = int(np.argmax(equity))
        trough_idx = int(np.argmin(equity))
        peak_value = float(equity[peak_idx])
        trough_value = float(equity[trough_idx])
        recovery_idx = None

    initial_recovery = np.flatnonzero(equity >= INITIAL)
    initial_recovery_idx = int(initial_recovery[0]) if len(initial_recovery) else None

    years = max((frame.index[-1] - frame.index[0]).days / 365.25, 1 / 365.25)
    final = float(equity[-1])
    row = {
        "strategy": label,
        "start": frame.index[0].date().isoformat(),
        "end": frame.index[-1].date().isoformat(),
        "observations": len(frame),
        "starting_balance": INITIAL,
        "final_balance": final,
        "cagr": (final / INITIAL) ** (1.0 / years) - 1.0,
        "max_drawdown": float(dd.min()),
        "minimum_equity": float(equity.min()),
        "dotcom_peak_date": frame.index[peak_idx].date().isoformat(),
        "dotcom_peak_balance": peak_value,
        "dotcom_trough_date": frame.index[trough_idx].date().isoformat(),
        "dotcom_trough_balance": trough_value,
        "dotcom_peak_to_trough_drawdown": (
            trough_value / peak_value - 1.0
        ),
        "initial_recovery_date": (
            frame.index[initial_recovery_idx].date().isoformat()
            if initial_recovery_idx is not None else None
        ),
        "dotcom_peak_recovery_date": (
            frame.index[recovery_idx].date().isoformat()
            if recovery_idx is not None else None
        ),
        "days_to_initial_recovery": (
            int((frame.index[initial_recovery_idx] - frame.index[0]).days)
            if initial_recovery_idx is not None else None
        ),
        "days_dotcom_peak_to_trough": int(
            (frame.index[trough_idx] - frame.index[peak_idx]).days
        ),
        "days_dotcom_peak_to_recovery": (
            int((frame.index[recovery_idx] - frame.index[peak_idx]).days)
            if recovery_idx is not None else None
        ),
        "avg_exposure": float(weights.mean()),
    }
    path = pd.DataFrame(
        {
            "Date": frame.index,
            "strategy": label,
            "equity": equity,
            "drawdown": dd,
            "weight": weights,
        }
    )
    return row, path


def make_weights(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    # Signals are deliberately based on QQQ adjusted close. This avoids
    # allowing the synthetic leverage path itself to distort the DMA signal.
    close = frame["adj_close"]
    out: dict[str, np.ndarray] = {
        "SYNTHETIC_TQQQ_BUY_AND_HOLD": np.ones(len(frame)),
    }

    for dma in DMAS:
        for exposure in EXPOSURES:
            pct = int(round(exposure * 100))
            label = (
                f"SYNTHETIC_TQQQ_{dma}DMA_{pct}_"
                "IMMEDIATE_NEXT_OPEN"
            )
            out[label] = target_weights(close, dma, exposure, 0)

    return out



def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = download_qqq()
    frame = build_synthetic(raw)

    rows = []
    paths = []
    for label, weights in make_weights(frame).items():
        row, path = evaluate(frame, weights, label)
        rows.append(row)
        paths.append(path)

    summary = pd.DataFrame(rows).sort_values(
        ["final_balance", "strategy"], ascending=[False, True]
    )
    path_frame = pd.concat(paths, ignore_index=True)

    summary.to_csv(OUT / "tqqq_dotcom_survivability_summary.csv", index=False)
    path_frame.to_csv(OUT / "tqqq_dotcom_survivability_paths.csv", index=False)
    frame[["close", "adj_close", "synthetic_tqqq_close"]].to_csv(
        OUT / "qqq_synthetic_tqqq_history.csv"
    )

    dotcom = path_frame[
        (path_frame["Date"] >= "2000-01-01")
        & (path_frame["Date"] <= "2003-12-31")
    ].copy()
    dotcom.to_csv(
        OUT / "tqqq_dotcom_survivability_dotcom_slice.csv", index=False
    )

    print(
        summary[
            [
                "strategy",
                "final_balance",
                "cagr",
                "max_drawdown",
                "minimum_equity",
                "avg_exposure",
            ]
        ].to_string(index=False)
    )
    print(
        f"Tested {len(summary)} strategies across "
        f"{len(DMAS)} DMAs and {len(EXPOSURES)} exposure levels."
    )
    print(f"Artifacts written to {OUT}")


if __name__ == "__main__":
    main()
