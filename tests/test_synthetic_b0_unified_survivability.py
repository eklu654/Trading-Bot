import numpy as np
import pandas as pd

from research.synthetic_b0_unified_survivability import (
    first_crossing,
    run_on_frame,
    synthetic_3x_legs,
)


def test_synthetic_3x_leg_returns_are_floored_at_minus_100_percent():
    idx = pd.bdate_range("2024-01-02", periods=4)
    q = pd.DataFrame({
        "Open": [100.0, 100.0, 10.0, 10.0],
        "Close": [100.0, 100.0, 10.0, 10.0],
        "Adj Close": [100.0, 100.0, 10.0, 10.0],
    }, index=idx)
    overnight, intraday = synthetic_3x_legs(q)
    assert np.all(overnight >= -1.0)
    assert np.all(intraday >= -1.0)
    assert overnight[2] == -1.0


def test_first_crossing_returns_first_date_or_empty_string():
    dates = pd.bdate_range("2024-01-02", periods=4)
    assert first_crossing(dates, [0.0, -0.5, -0.99, -0.999], -0.99) == dates[2].date().isoformat()
    assert first_crossing(dates, [0.0, -0.5, -0.8, -0.9], -0.99) == ""


def test_b0_and_buy_hold_share_one_execution_path_and_summary_schema():
    dates = pd.bdate_range("1999-03-10", "2003-01-10")
    prices = np.full(len(dates), 100.0)
    # Add a gentle decline and recovery through the required dot-com window.
    mask = (dates >= "2000-03-01") & (dates <= "2002-10-01")
    prices[mask] = np.linspace(100.0, 70.0, mask.sum())
    after = dates > "2002-10-01"
    prices[after] = np.linspace(70.0, 90.0, after.sum())
    q = pd.DataFrame({"Open": prices, "Close": prices, "Adj Close": prices}, index=dates)

    summary, paths = run_on_frame(q)
    assert set(summary.strategy) == {"B0_QQQ_shock_recovery", "synthetic_3x_QQQ_buy_hold"}
    assert len(paths) == 2 * len(q)
    assert summary["first_crossing_dd_99pct"].eq("").all()
    assert summary["first_crossing_dd_99_9pct"].eq("").all()
    assert summary["dotcom_trough_date"].notna().all()


def test_synthetic_legs_reconcile_to_three_times_daily_return_without_clipping():
    idx = pd.bdate_range("2024-01-02", periods=3)
    q = pd.DataFrame({
        "Open": [100.0, 110.0, 121.0],
        "Close": [100.0, 121.0, 133.1],
        "Adj Close": [100.0, 121.0, 133.1],
    }, index=idx)
    overnight, intraday = synthetic_3x_legs(q)
    # Day 2: +10% overnight, +10% intraday, +21% QQQ close-to-close.
    # The synthetic daily-reset proxy must return 3 * 21% = 63%, not 69%.
    combined = (1.0 + overnight[1]) * (1.0 + intraday[1]) - 1.0
    assert np.isclose(combined, 3.0 * (121.0 / 100.0 - 1.0), atol=1e-12)


def test_existing_dotcom_builder_uses_same_daily_reset_open_close_path():
    from research.test_tqqq_dotcom_survivability import build_synthetic

    idx = pd.bdate_range("2024-01-02", periods=3)
    q = pd.DataFrame({
        "open": [100.0, 110.0, 121.0],
        "close": [100.0, 121.0, 133.1],
        "adj_close": [100.0, 121.0, 133.1],
    }, index=idx)
    got = build_synthetic(q)
    # +10% overnight and +10% intraday is +21% for QQQ, hence +63% for
    # the synthetic daily-reset 3x fund, not the +69% from double re-levering.
    assert np.isclose(got["synthetic_tqqq_open"].iloc[1], 6500.0, atol=1e-9)
    assert np.isclose(got["synthetic_tqqq_close"].iloc[1], 8150.0, atol=1e-9)
    assert np.isclose(got["synthetic_tqqq_close"].iloc[2] / got["synthetic_tqqq_close"].iloc[1] - 1.0, 0.30, atol=1e-12)


def test_partial_dma_matrix_uses_one_post_warmup_window_and_includes_b0():
    from research.tqqq_partial_dma_matrix import run_matrix

    idx = pd.bdate_range("1999-03-10", periods=300)
    frame = pd.DataFrame({
        "adj_close": np.linspace(100.0, 120.0, len(idx)),
        "on3": np.zeros(len(idx)),
        "in3": np.zeros(len(idx)),
    }, index=idx)
    out, start, end = run_matrix(frame)
    assert start == idx[249]
    assert end == idx[-1]
    assert out["evaluation_start"].nunique() == 1
    assert out["evaluation_end"].nunique() == 1
    assert "B0_SHOCK_RECOVERY" in set(out["strategy"])
    assert set(out["observations"]) == {len(idx) - 249}
    assert set(out["starting_balance"]) == {5000.0}
