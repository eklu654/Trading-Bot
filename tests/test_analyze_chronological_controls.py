from datetime import date, timedelta
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "0dte" / "analyze_chronological_controls.py"
SPEC = importlib.util.spec_from_file_location("chronological_controls", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

CONTROLS = MODULE.CONTROLS
evaluate = MODULE.evaluate


def _business_days(start: date, end: date, count: int) -> list[date]:
    result = []
    current = start
    while current <= end and len(result) < count:
        if current.weekday() < 5:
            result.append(current)
        current += timedelta(days=1)
    assert len(result) == count
    return result


def test_frozen_control_set_and_split_sizes():
    dates = (
        _business_days(date(2022, 6, 16), date(2024, 12, 31), 597)
        + _business_days(date(2025, 1, 1), date(2025, 12, 31), 238)
        + _business_days(date(2026, 1, 1), date(2026, 9, 28), 177)
    )
    data = {
        "configs": [
            {
                "name": name,
                "result": {
                    "results": {
                        "days": [
                            {"date": day.isoformat(), "net_pnl": "1.0"}
                            for day in dates
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
    assert all(r["net_pnl"] == r["sessions"] for r in rows)
