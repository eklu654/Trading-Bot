import unittest
import numpy as np
from f75_prospective_shadow_monitor import reconcile_canonical_signal, compose_f75_signal

class ShadowMonitorGuardrails(unittest.TestCase):
    def test_f75_uses_partial_exposure_when_overlay_active(self):
        candidate = compose_f75_signal([1, 1, 0, 1], [1, 0, 0, 1])
        np.testing.assert_allclose(candidate, [1, 0.75, 0, 1])

    def test_f75_partial_exposure_is_capped_by_b0(self):
        candidate = compose_f75_signal([1, 0, 1, 1], [0, 0, 1, 1])
        np.testing.assert_allclose(candidate, [0.75, 0, 1, 1])

    def test_f75_rejects_shape_mismatch(self):
        with self.assertRaisesRegex(ValueError, "equal shapes"):
            compose_f75_signal([1, 0], [1])

    def test_exact_canonical_signal_passes(self):
        self.assertTrue(reconcile_canonical_signal([1, 0, 0, 1], [1, 0, 0, 1]))

    def test_signal_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            reconcile_canonical_signal([1, 0, 1], [1, 0, 0])

    def test_length_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "length"):
            reconcile_canonical_signal([1, 0], [1])

if __name__ == "__main__":
    unittest.main()
