import numpy as np
import pytest

from research.tqqq_partial_dma_matrix import combine_b0_and_dma


def test_b0_defensive_signal_takes_precedence_over_dma_exposure():
    b0 = np.array([1.0, 0.0, 0.0, 1.0, 1.0])
    dma = np.array([0.25, 1.0, 0.5, 0.75, 1.0])
    combined = combine_b0_and_dma(b0, dma)
    np.testing.assert_array_equal(combined, [0.25, 0.0, 0.0, 0.75, 1.0])


def test_b0_plus_dma_equals_b0_when_dma_exposure_is_full():
    b0 = np.array([1.0, 0.0, 1.0, 0.0])
    np.testing.assert_array_equal(combine_b0_and_dma(b0, np.ones(4)), b0)


def test_combined_signals_must_have_matching_shapes():
    with pytest.raises(ValueError, match="identical shapes"):
        combine_b0_and_dma(np.ones(3), np.ones(2))


def test_combined_signals_reject_exposure_outside_zero_to_one():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        combine_b0_and_dma(np.array([1.0]), np.array([1.25]))


def test_partial_dma_matrix_marks_standalone_variants_as_diagnostic_only():
    from pathlib import Path

    source = Path("research/tqqq_partial_dma_matrix.py").read_text()
    assert '"B0_PLUS_DMA_PARTIAL_EXPOSURE"' in source
    assert '"DMA_ONLY_DIAGNOSTIC"' in source
    assert "combine_b0_and_dma(b0, dma_signal)" in source

def test_actual_tqqq_matrix_also_tests_b0_combinations():
    from pathlib import Path

    source = Path("research/tqqq_actual_partial_dma_matrix.py").read_text()
    assert '"B0_PLUS_DMA_PARTIAL"' in source
    assert '"DMA_ONLY_DIAGNOSTIC"' in source
    assert "np.minimum(x.b0_signal.to_numpy(dtype=float),sig)" in source
