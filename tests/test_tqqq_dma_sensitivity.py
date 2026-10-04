from pathlib import Path

SCRIPT = Path("research/test_tqqq_dma_sensitivity.py").read_text()


def test_dma_matrix_is_predeclared():
    assert "DMA_WINDOWS = (100, 125, 150, 175, 200, 225, 250, 300)" in SCRIPT
    assert "CONFIRM_SESSIONS = 5" in SCRIPT
    assert "START_CAPITAL = 5000.0" in SCRIPT
    assert "TQQQ buy-and-hold" in SCRIPT
    assert "immediate re-entry" in SCRIPT


def test_primary_matrix_does_not_optimize_on_results():
    assert "rank(" in SCRIPT
    assert "DMA_WINDOWS" in SCRIPT
    assert "product(" not in SCRIPT.lower()
    assert "itertools" not in SCRIPT.lower()
