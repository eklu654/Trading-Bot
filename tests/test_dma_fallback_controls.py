from pathlib import Path

SCRIPT = Path("research/test_dma_fallback_controls.py").read_text()

def test_fallback_controls_are_fixed_and_predeclared():
    assert "CONTROL_PAIRS" in SCRIPT
    assert "soxl_to_tqqq" in SCRIPT
    assert "soxl_to_spxl" in SCRIPT
    assert "rolling" in SCRIPT
    assert "optimiz" not in SCRIPT.lower()
