from __future__ import annotations

import pandas as pd

from research.analyze_switch001_regimes import STRESS_WINDOWS, summarize


def test_summarize_reports_each_declared_regime_without_optimization():
    frame = pd.DataFrame(
        {
            "decision_regime": [
                "TRENDING_NORMAL",
                "TRENDING_NORMAL",
                "SIDEWAYS_CHOPPY",
                "TURBULENT_HIGH_VOL",
            ],
            "SPY_fwd1": [0.01, -0.01, 0.002, -0.03],
            "QQQ_fwd1": [0.02, -0.02, 0.001, -0.04],
            "SOXX_fwd1": [0.03, -0.03, 0.003, -0.05],
            "TQQQ_fwd1": [0.03, -0.03, 0.004, -0.09],
            "SPXL_fwd1": [0.03, -0.03, 0.003, -0.08],
            "SOXL_fwd1": [0.05, -0.05, 0.005, -0.15],
        }
    )

    result = summarize(frame)

    assert set(result["decision_regime"]) == {
        "TRENDING_NORMAL",
        "SIDEWAYS_CHOPPY",
        "TURBULENT_HIGH_VOL",
    }
    assert result["observations"].sum() == len(frame)
    assert (result["SPY_win_rate"] >= 0).all()
    assert (result["SPY_win_rate"] <= 1).all()


def test_stress_windows_are_fixed_and_predeclared():
    assert set(STRESS_WINDOWS) == {
        "2018_volatility_shock",
        "2018_q4",
        "covid_crash",
        "2022_rate_hike",
    }
