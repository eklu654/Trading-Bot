import numpy as np
import pandas as pd

from research.b0_control_window_cost_reconciliation import (
    COSTS, WARMUP_SESSIONS, reconcile
)


def synthetic_frame(n=320):
    dates = pd.bdate_range("2020-01-01", periods=n)
    # Smooth deterministic series with one qualifying shock/recovery event.
    qqq = np.full(n, 100.0)
    for i in range(1, n):
        qqq[i] = qqq[i - 1] * (0.999 if i < 265 else 1.001)
    qqq[260] = qqq[259] * 0.94
    for i in range(261, n):
        qqq[i] = qqq[i - 1] * 1.004
    t_close = np.linspace(20.0, 45.0, n)
    t_open = t_close * (1.0 + 0.001 * np.sin(np.arange(n)))
    return pd.DataFrame({
        "qqq_adj_close": qqq,
        "tqqq_adj_close": t_close,
        "tqqq_adj_open": t_open,
    }, index=dates)


def test_reconcile_reports_all_costs_and_three_window_views():
    summary, paths, events = reconcile(synthetic_frame())
    assert set(summary.cost_bps) == set(COSTS)
    assert {
        "inception_full", "warmup_reset", "warmup_carried_equity",
        "inception_full_through_2026-10-02",
        "warmup_reset_through_2026-10-02",
        "warmup_carried_equity_through_2026-10-02",
    }.issubset(set(summary.view))
    assert len(summary) == len(COSTS) * 6
    assert set(paths.view) == set(summary.view)
    assert len(events) >= 1


def test_warmup_reset_starts_at_fresh_capital_and_carried_view_matches_full_path():
    frame = synthetic_frame()
    summary, paths, _ = reconcile(frame)
    zero = summary[summary.cost_bps == 0].set_index("view")
    reset_path = paths[(paths.cost_bps == 0) & (paths.view == "warmup_reset")]
    full_path = paths[(paths.cost_bps == 0) & (paths.view == "inception_full")]
    carried_path = paths[(paths.cost_bps == 0) & (paths.view == "warmup_carried_equity")]
    assert reset_path.equity.iloc[0] > 0
    assert np.isclose(reset_path.equity.iloc[0], 5000.0)
    assert np.allclose(
        carried_path.equity.to_numpy(),
        full_path.equity.iloc[WARMUP_SESSIONS - 1:].to_numpy(),
    )
    assert zero.loc["warmup_carried_equity", "ending_balance"] == zero.loc[
        "inception_full", "ending_balance"
    ]


def test_costs_do_not_increase_terminal_wealth_for_same_signal_path():
    summary, _, _ = reconcile(synthetic_frame())
    full = summary[summary.view == "inception_full"].set_index("cost_bps")
    assert full.loc[0, "ending_balance"] >= full.loc[10, "ending_balance"]
    assert full.loc[10, "ending_balance"] >= full.loc[25, "ending_balance"]
    assert full.loc[25, "ending_balance"] >= full.loc[50, "ending_balance"]
