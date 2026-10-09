import numpy as np
import pytest

from research.b0_250dma_hybrid_validation import hybrid_target_exposure


def test_hybrid_never_overrides_b0_cash_exit_and_caps_only_below_dma():
    b0 = [1.0, 0.0, 1.0, 1.0, 0.0]
    close = [90.0, 80.0, 110.0, 90.0, 110.0]
    dma = [100.0] * len(b0)
    got = hybrid_target_exposure(b0, close, dma, 0.25)
    assert np.array_equal(got, [0.25, 0.0, 1.0, 0.25, 0.0])


def test_hybrid_rejects_invalid_exposure_and_misaligned_inputs():
    with pytest.raises(ValueError):
        hybrid_target_exposure([1.0], [100.0], [100.0], 1.25)
    with pytest.raises(ValueError):
        hybrid_target_exposure([1.0, 0.0], [100.0], [100.0], 0.5)
