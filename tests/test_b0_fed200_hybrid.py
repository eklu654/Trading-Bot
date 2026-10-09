import numpy as np
import pytest

from research.b0_fed200_hybrid_validation import fed_hike_hybrid_target_exposure


def test_fed_hybrid_only_reduces_invested_b0_below_dma_during_net_hike_state():
    got = fed_hike_hybrid_target_exposure(
        b0=[1.0, 0.0, 1.0, 1.0, 1.0],
        qqq_close=[90.0, 90.0, 90.0, 110.0, 90.0],
        dma_close=[100.0] * 5,
        fed_change=[0.25, 0.50, 0.50, 0.50, 0.24],
        below=0.50,
    )
    assert np.array_equal(got, [0.50, 0.0, 0.50, 1.0, 1.0])


def test_fed_hybrid_rejects_invalid_exposure_and_misaligned_inputs():
    with pytest.raises(ValueError):
        fed_hike_hybrid_target_exposure([1.0], [100.0], [100.0], [0.5], 1.1)
    with pytest.raises(ValueError):
        fed_hike_hybrid_target_exposure([1.0, 0.0], [100.0], [100.0], [0.5], 0.5)
