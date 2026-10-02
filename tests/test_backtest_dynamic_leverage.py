from pathlib import Path
import sys

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
