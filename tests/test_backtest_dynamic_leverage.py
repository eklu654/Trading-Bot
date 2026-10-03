from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.backtest_dynamic_leverage import (  # noqa: E402
    FAMILIES,
    choose_family,
    choose_leverage,
)


def test_exposure_ladder_is_explicit():
    assert set(FAMILIES) == {"SPY", "QQQ", "SOXX"}
    for family in FAMILIES.values():
        assert set(family) == {0, 1, 2, 3}
        assert family[0] is None
        assert all(isinstance(family[level], str) for level in (1, 2, 3))


def test_leverage_uses_trend_then_vix():
    base = pd.Series({"SPY": 110.0, "spy_ma": 100.0, "vix_pct": 0.20})
    assert choose_leverage(base) == 3
    assert choose_leverage(base.copy().set_axis(base.index).where(base.index != "vix_pct", 0.70)) == 2
    assert choose_leverage(base.copy().set_axis(base.index).where(base.index != "vix_pct", 0.90)) == 1
    assert choose_leverage(base.copy().set_axis(base.index).where(base.index != "SPY", 99.0)) == 0


def test_family_selection_uses_only_declared_relative_strength():
    row = pd.Series({"SPY_rs": 0.05, "QQQ_rs": 0.12, "SOXX_rs": 0.08})
    assert choose_family(row) == "QQQ"


def test_family_selection_falls_back_when_all_scores_missing():
    row = pd.Series({"SPY_rs": float("nan"), "QQQ_rs": float("nan"), "SOXX_rs": float("nan")})
    assert choose_family(row) == "SPY"



def test_comparison_script_can_be_imported_from_repo_root():
    import research.compare_leverage_benchmarks as comparison
    assert comparison.ROOT == ROOT



def test_summary_uses_segment_returns_not_global_equity_level():
    from research.backtest_dynamic_leverage import summarize
    frame = pd.DataFrame(
        {"portfolio_return": [0.10, -0.05], "portfolio_value": [1.10, 1.045], "leverage": [3, 2]},
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )
    result = summarize(frame, "synthetic")
    assert abs(result["total_return"] - 0.045) < 1e-12



def test_static_hold_is_true_buy_and_hold(monkeypatch):
    import research.compare_leverage_benchmarks as comparison

    idx = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    fake = pd.DataFrame({"adj_close": [100.0, 110.0, 99.0]}, index=idx)
    monkeypatch.setattr(comparison, "load", lambda symbol: fake)
    result = comparison.static_hold("SOXL", idx)
    assert np.allclose(result["portfolio_return"].to_numpy(), [0.0, 0.10, -0.10])


def test_common_comparison_period_is_explicit():
    import research.compare_leverage_benchmarks as comparison
    assert comparison.COMMON_START == pd.Timestamp("2010-01-01")
    assert comparison.COMMON_END == pd.Timestamp("2026-09-25")


def test_2018_2025_comparison_period_is_explicit():
    import research.compare_leverage_benchmarks as comparison
    assert comparison.COMPARISON_START == pd.Timestamp("2018-01-01")
    assert comparison.COMPARISON_END == pd.Timestamp("2025-12-31")


def test_dynamic_benchmark_common_period_is_explicit():
    from research import backtest_dynamic_leverage as dynamic
    assert dynamic.COMMON_START == pd.Timestamp("2010-01-01")
    assert dynamic.COMMON_END == pd.Timestamp("2026-09-25")
