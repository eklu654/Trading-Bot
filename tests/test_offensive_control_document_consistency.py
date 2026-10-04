from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UNIFIED = ROOT / "docs" / "02-research" / "unified-offensive-control-comparison-2026-10-04.md"
ADDENDUM = ROOT / "docs" / "02-research" / "etf031-path-survivability-addendum-2026-10-04.md"


def test_authoritative_offensive_comparison_uses_current_period():
    source = UNIFIED.read_text()
    assert "2010-03-11 → 2026-10-02" in source
    assert "2026-09-25" not in source
    assert "TQQQ 200-DMA/next-open" in source
    assert "| 162 |" in source
    assert "| 164 |" not in source


def test_etf031_survivability_addendum_is_common_period_consistent():
    source = ADDENDUM.read_text()
    assert "2010-03-11 → 2026-10-02" in source
    assert "4,167 daily observations" in source
    assert "37169061754" in source
    assert "2026-09-25" not in source
