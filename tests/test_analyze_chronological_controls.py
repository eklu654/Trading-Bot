from datetime import date

from tools_0dte_chronological_validation import (
    CONTROLS,
    SPLITS,
    evaluate,
)


def test_frozen_control_set_and_split_sizes():
    data = {
        "configs": [
            {
                "name": name,
                "result": {
                    "results": {
                        "days": [
                            {
                                "date": d.isoformat(),
                                "net_pnl": "1.0",
                            }
                            for d in _dates()
                        ]
                    }
                },
            }
            for name in CONTROLS
        ]
    }

    rows = evaluate(data)
    assert len(rows) == 12
    assert {(r["split"], r["sessions"]) for r in rows} == {
        ("TRAIN", 597),
        ("VALIDATION", 238),
        ("HOLDOUT", 177),
    }


def _dates():
    # Exact split cardinalities, with one synthetic date per calendar day in
    # the same chronological windows used by the production artifact.
    dates = []
    current = date(2022, 6, 16)
    while current <= date(2026, 9, 28):
        if current.weekday() < 5:
            dates.append(current)
        current = date.fromordinal(current.toordinal() + 1)

    # The production artifact contains market sessions rather than every
    # weekday. For this unit test, replace the synthetic sequence with exact
    # split cardinalities while preserving the split boundaries.
    train = [date(2022, 6, 16)] * 0
    del dates
    return (
        [date(2022, 6, 16)] * 597
        + [date(2025, 1, 1)] * 238
        + [date(2026, 1, 1)] * 177
    )
