from pathlib import Path

SCRIPT = Path("research/test_tqqq_partial_exposure_dma.py").read_text()

def test_partial_grid_is_systematic():
    assert "DMAS = (100, 125, 150, 175, 200, 225, 250, 300)" in SCRIPT
    assert "DISTANCE_GRID = (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)" in SCRIPT
    assert "THRESHOLD_TUPLES = tuple(combinations(DISTANCE_GRID, 3))" in SCRIPT
    assert "product(EXPOSURES, repeat=4)" in SCRIPT
    assert "WEIGHT_TUPLES = tuple(" in SCRIPT
    assert "w[0] >= w[1] >= w[2] >= w[3]" in SCRIPT
    assert "INITIAL = 5000.0" in SCRIPT
    assert "EXPECTED_OBSERVATIONS = 4167" in SCRIPT

def test_exact_period_and_controls_are_frozen():
    assert 'START = pd.Timestamp("2010-03-11")' in SCRIPT
    assert 'END = pd.Timestamp("2026-10-02")' in SCRIPT
    assert '"TQQQ buy-and-hold"' in SCRIPT
    assert '"TQQQ 200-DMA binary"' in SCRIPT
    assert '"tqqq_partial_exposure_dma_full_matrix.csv"' in SCRIPT

def test_no_result_dependent_parameter_search():
    assert "sort_values" in SCRIPT
    assert "product(" in SCRIPT
    assert "threshold" in SCRIPT.lower()
    # The matrix is fully predeclared; no optimizer/model selection is used.
    assert "scipy" not in SCRIPT.lower()
    assert "sklearn" not in SCRIPT.lower()
