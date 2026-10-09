import numpy as np
import pytest

from research.b0_vix30_hybrid_validation import vix_hybrid_target_exposure


def test_vix_hybrid_only_reduces_invested_b0_when_vix_close_is_at_least_30():
    got = vix_hybrid_target_exposure(
        b0=[1.0, 0.0, 1.0, 1.0, 1.0],
        vix_close=[30.0, 45.0, 29.9, 35.0, 20.0],
        below=0.75,
    )
    assert np.array_equal(got, [0.75, 0.0, 1.0, 0.75, 1.0])


def test_vix_hybrid_rejects_invalid_exposure_and_misaligned_inputs():
    with pytest.raises(ValueError):
        vix_hybrid_target_exposure([1.0], [30.0], 1.25)
    with pytest.raises(ValueError):
        vix_hybrid_target_exposure([1.0, 0.0], [30.0], 0.5)
