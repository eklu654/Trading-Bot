from __future__ import annotations

import numpy as np
import pandas as pd

from research.backtest_dynamic_etf_selection import choose_family


def row(**values: float) -> pd.Series:
    return pd.Series(values, dtype=float)


def test_raw_relative_strength_selects_highest_family():
    features = row(SPY_rs=0.10, QQQ_rs=0.20, SOXX_rs=0.05)
    assert choose_family(features, "raw_60d") == "QQQ"


def test_trend_confirmed_rejects_family_below_200dma():
    features = row(
        SPY_rs=0.10, QQQ_rs=0.20, SOXX_rs=0.05,
        SPY=110.0, QQQ=90.0, SOXX=120.0,
        SPY_ma200=100.0, QQQ_ma200=100.0, SOXX_ma200=100.0,
    )
    assert choose_family(features, "trend_confirmed") == "SPY"


def test_risk_adjusted_selection_penalizes_high_volatility():
    features = row(SPY_rs=0.10, QQQ_rs=0.12, SOXX_rs=0.11, SPY_rv20=0.20, QQQ_rv20=0.80, SOXX_rv20=0.10)
    assert choose_family(features, "risk_adjusted_60d") == "SOXX"


def test_missing_scores_fallback_to_spy():
    features = row(SPY_rs=np.nan, QQQ_rs=np.nan, SOXX_rs=np.nan)
    assert choose_family(features, "raw_60d") == "SPY"

def test_trend_confirmed_prefers_highest_eligible_score():
    features = row(
        SPY_rs=0.10, QQQ_rs=0.20, SOXX_rs=0.05,
        SPY=110.0, QQQ=90.0, SOXX=120.0,
        SPY_ma200=100.0, QQQ_ma200=100.0, SOXX_ma200=100.0,
    )
    assert choose_family(features, "trend_confirmed") == "SPY"
