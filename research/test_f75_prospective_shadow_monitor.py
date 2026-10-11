import unittest
import hashlib
import numpy as np
import pandas as pd
from f75_prospective_shadow_monitor import (
    reconcile_canonical_signal, compose_f75_signal, validate_existing_ledger, only_unrecorded_sessions, EXPECTED_HASH,
)

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

    def _valid_ledger_fixture(self):
        ledger_bytes = b"synthetic-ledger-bytes"
        prior = pd.DataFrame({
            "date": ["2026-10-08", "2026-10-09"],
            "source_canonical_sha256": [EXPECTED_HASH, EXPECTED_HASH],
            "initialization_session": [True, False],
            "b0_exposure": [0.0, 1.0],
            "f75_exposure": [0.0, 1.0],
            "b0_equity_0bps": [5000.0, 4973.0],
            "b0_equity_25bps": [5000.0, 4960.5],
            "b0_equity_50bps": [5000.0, 4948.0],
            "f75_equity_0bps": [5000.0, 4973.0],
            "f75_equity_25bps": [5000.0, 4960.5],
            "f75_equity_50bps": [5000.0, 4948.0],
        })
        state = {
            "canonical_input_sha256": EXPECTED_HASH,
            "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "last_observation": "2026-10-09",
            "mode": "SHADOW_ONLY_NO_ORDERS",
        }
        return prior, state, ledger_bytes

    def test_ledger_tail_filter_makes_rerun_idempotent(self):
        prior = pd.DataFrame({"date": ["2026-10-08", "2026-10-09"]})
        fresh = pd.DataFrame(
            {"price": [1, 2]},
            index=pd.to_datetime(["2026-10-08", "2026-10-09"]),
        )
        result = only_unrecorded_sessions(fresh, prior)
        self.assertTrue(result.empty)

    def test_ledger_tail_filter_keeps_only_new_sessions(self):
        prior = pd.DataFrame({"date": ["2026-10-08", "2026-10-09"]})
        fresh = pd.DataFrame(
            {"price": [1, 2, 3]},
            index=pd.to_datetime(["2026-10-09", "2026-10-12", "2026-10-13"]),
        )
        result = only_unrecorded_sessions(fresh, prior)
        self.assertEqual(list(result.index), list(pd.to_datetime(["2026-10-12", "2026-10-13"])))

    def test_existing_ledger_and_state_manifest_validate(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        self.assertTrue(validate_existing_ledger(prior, state, ledger_bytes))

    def test_existing_ledger_hash_mismatch_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["ledger_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "ledger SHA-256 mismatch"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_tail_mismatch_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["last_observation"] = "2026-10-08"
        with self.assertRaisesRegex(RuntimeError, "tail date"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_duplicate_dates_fail_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "date"] = "2026-10-08"
        with self.assertRaisesRegex(RuntimeError, "dates invalid"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_source_hash_mismatch_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[0, "source_canonical_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "canonical source hash mismatch"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_nonfinite_equity_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "b0_equity_25bps"] = np.nan
        with self.assertRaisesRegex(RuntimeError, "non-finite"):
            validate_existing_ledger(prior, state, ledger_bytes)

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
