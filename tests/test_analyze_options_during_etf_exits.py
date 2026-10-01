from pathlib import Path
import pandas as pd

from research.analyze_options_during_etf_exits import episode_table


def test_episode_table_groups_contiguous_full_exit_days():
    idx = pd.date_range("2023-01-01", periods=7, freq="D")
    state = pd.DataFrame(
        {"full_exit": [True, True, False, True, False, False, True]},
        index=idx,
    )
    out = episode_table(state)
    assert len(out) == 3
    assert out.loc[0, "days"] == 2
    assert out.loc[1, "days"] == 1
    assert out.loc[2, "days"] == 1


def test_episode_table_has_expected_boundaries():
    idx = pd.date_range("2023-01-01", periods=3, freq="D")
    state = pd.DataFrame({"full_exit": [False, True, True]}, index=idx)
    out = episode_table(state)
    assert out.loc[0, "start"] == idx[1]
    assert out.loc[0, "end"] == idx[2]
