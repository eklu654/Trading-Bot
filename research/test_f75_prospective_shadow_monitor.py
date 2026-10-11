import unittest
import numpy as np
from f75_prospective_shadow_monitor import reconcile_canonical_signal

class ShadowMonitorGuardrails(unittest.TestCase):
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
