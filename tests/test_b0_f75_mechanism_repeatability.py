"""Fast synthetic guardrails for the fixed episode attribution calculations."""
import numpy as np
import pandas as pd
from research.b0_f75_mechanism_repeatability import _max_dd, _equity_path, EPISODES

def test_fixed_episode_set_is_preregistered_and_includes_fast_and_slow_bears():
    names = [x[0] for x in EPISODES]
    assert names == ["dotcom_2000_2002", "gfc_2007_2009", "2011_stress",
                     "2015_2016_stress", "2018_selloff", "covid_2020",
                     "fed_tightening_2022_2024"]

def test_drawdown_uses_running_peak():
    assert np.isclose(_max_dd([100, 120, 90, 110]), -0.25)

def test_zero_exposure_does_not_accrue_market_returns():
    prices = pd.DataFrame({"tqqq_adj_open":[100, 80, 90],
                           "tqqq_adj_close":[100, 90, 100]})
    eq, exposure = _equity_path(prices, np.zeros(3), 25, initial=5000)
    assert np.allclose(eq, [5000, 5000, 5000])
    assert np.allclose(exposure, [0, 0, 0])

def test_full_exposure_path_is_finite():
    prices = pd.DataFrame({"tqqq_adj_open":[100, 101, 99],
                           "tqqq_adj_close":[100, 102, 100]})
    eq, exposure = _equity_path(prices, np.ones(3), 25, initial=5000)
    assert np.isfinite(eq).all()
    assert np.allclose(exposure, [0, 1, 1])


def test_episode_path_normalizes_to_starting_balance_and_includes_first_session():
    from research.b0_f75_mechanism_repeatability import _episode_path
    full_path = np.array([4000.0, 3600.0, 3800.0])
    episode = _episode_path(full_path, episode_start_index=0)
    assert np.allclose(episode, [5000.0, 4500.0, 4750.0])
    assert np.isclose(episode[-1] / 5000.0 - 1.0, -0.05)
    assert np.isclose(_max_dd(episode), -0.10)

def test_episode_path_excludes_pre_episode_drawdown_but_keeps_starting_balance():
    from research.b0_f75_mechanism_repeatability import _episode_path
    full_path = np.array([8000.0, 4000.0, 4100.0, 4200.0])
    episode = _episode_path(full_path, episode_start_index=1)
    assert np.allclose(episode, [5000.0, 5125.0, 5250.0])
    assert np.isclose(_max_dd(episode), 0.0)


def test_report_accounting_validator_accepts_consistent_episode_and_rejects_mismatch():
    import pytest
    from research.b0_f75_mechanism_repeatability import _validate_report, COSTS
    row = {"episode": "synthetic", "status": "MEASURED"}
    for label in ("b0", "f75"):
        for cost in COSTS:
            row[f"{label}_return_{cost}bps"] = 0.0
            row[f"{label}_terminal_equity_{cost}bps"] = 5000.0
            row[f"{label}_maxdd_{cost}bps"] = 0.0
        for horizon in (20, 60):
            row[f"{label}_exposure_next_{horizon}s"] = 0.5
    for cost in COSTS:
        row[f"incremental_equity_{cost}bps"] = 0.0
        row[f"incremental_return_{cost}bps"] = 0.0
        row[f"incremental_maxdd_{cost}bps"] = 0.0
    row["recovery_sessions_next_20s"] = 20
    row["recovery_sessions_next_60s"] = 60
    frame = pd.DataFrame([row])
    assert _validate_report(frame) == 1
    frame.loc[0, "b0_terminal_equity_25bps"] = 4900.0
    with pytest.raises(RuntimeError, match="return/terminal mismatch"):
        _validate_report(frame)


def test_full_period_comparison_is_compounded_and_cost_sensitive():
    from research.b0_f75_mechanism_repeatability import _full_period_comparison
    prices = pd.DataFrame({
        "tqqq_adj_open": [100.0, 100.0, 90.0, 100.0],
        "tqqq_adj_close": [100.0, 100.0, 100.0, 110.0],
    }, index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"]))
    b0 = np.ones(4)
    f75 = np.array([1.0, 0.0, 0.0, 1.0])
    report = _full_period_comparison(prices, b0, f75, costs=(0, 25))
    assert len(report) == 2
    assert np.allclose(report["b0_terminal_equity"], 5000.0 * (1.0 + report["b0_total_return"]))
    assert np.allclose(report["f75_terminal_equity"], 5000.0 * (1.0 + report["f75_total_return"]))
    assert report.loc[report.cost_bps.eq(25), "b0_terminal_equity"].iloc[0] < report.loc[report.cost_bps.eq(0), "b0_terminal_equity"].iloc[0]
