import unittest
import hashlib
import numpy as np
import pandas as pd
from f75_prospective_shadow_monitor import (
    reconcile_canonical_signal, compose_f75_signal, validate_existing_ledger, only_unrecorded_sessions, exclude_current_session, EXPECTED_HASH,
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

    def test_f75_rejects_nonbinary_baseline(self):
        with self.assertRaisesRegex(ValueError, "binary"):
            compose_f75_signal([1, 0.5], [1, 1])

    def test_f75_rejects_nonbinary_overlay(self):
        with self.assertRaisesRegex(ValueError, "binary"):
            compose_f75_signal([1, 1], [1, 0.5])

    def test_f75_rejects_nonfinite_signal(self):
        with self.assertRaisesRegex(ValueError, "finite binary"):
            compose_f75_signal([1, np.nan], [1, 0])

    def test_f75_rejects_invalid_partial_exposure(self):
        with self.assertRaisesRegex(ValueError, "finite and between"):
            compose_f75_signal([1], [0], partial_exposure=float("nan"))

    def _valid_ledger_fixture(self):
        ledger_bytes = b"synthetic-ledger-bytes"
        prior = pd.DataFrame({
            "date": ["2026-10-08", "2026-10-09"],
            "source_canonical_sha256": [EXPECTED_HASH, EXPECTED_HASH],
            "initialization_session": [True, False],
            "b0_signal_close": [1.0, 1.0],
            "f75_overlay_signal_close": [1.0, 1.0],
            "f75_signal_close": [1.0, 1.0],
            "b0_exposure": [0.0, 1.0],
            "f75_exposure": [0.0, 1.0],
            "overnight_return": [0.0, 0.0185715792275],
            "intraday_return": [0.0, -0.00538426865925],
            "b0_equity_0bps": [5000.0, 4973.07865670375],
            "b0_equity_25bps": [5000.0, 4960.64596006199],
            "b0_equity_50bps": [5000.0, 4948.21326342023],
            "f75_equity_0bps": [5000.0, 4973.07865670375],
            "f75_equity_25bps": [5000.0, 4960.64596006199],
            "f75_equity_50bps": [5000.0, 4948.21326342023],
        })
        state = {
            "canonical_input_sha256": EXPECTED_HASH,
            "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "last_observation": "2026-10-09",
            "sessions_appended_this_run": 0,
            "ledger_rows_total": 2,
            "return_bearing_sessions_total": 1,
            "initialization_date": "2026-10-08",
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

    def test_current_session_bar_is_excluded(self):
        fresh = pd.DataFrame(
            {"price": [10, 11, 12]},
            index=pd.to_datetime(["2026-10-09", "2026-10-12", "2026-10-13"]),
        )
        result = exclude_current_session(fresh, today="2026-10-12")
        self.assertEqual(list(result.index), list(pd.to_datetime(["2026-10-09"])))

    def test_current_session_guard_handles_empty_input(self):
        fresh = pd.DataFrame(columns=["price"], index=pd.DatetimeIndex([]))
        result = exclude_current_session(fresh, today="2026-10-12")
        self.assertTrue(result.empty)

    def test_existing_ledger_and_state_manifest_validate(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        self.assertTrue(validate_existing_ledger(prior, state, ledger_bytes))

    def test_state_rejects_ledger_row_count_mismatch(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["ledger_rows_total"] = 3
        with self.assertRaisesRegex(RuntimeError, "total ledger row count"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_state_rejects_return_bearing_count_mismatch(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["return_bearing_sessions_total"] = 2
        with self.assertRaisesRegex(RuntimeError, "return-bearing session count"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_state_rejects_initialization_date_mismatch(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["initialization_date"] = "2026-10-09"
        with self.assertRaisesRegex(RuntimeError, "initialization date"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_state_rejects_invalid_per_run_append_counter(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        state["sessions_appended_this_run"] = -1
        with self.assertRaisesRegex(RuntimeError, "per-run append counter"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_rejects_full_exit_masquerading_as_f75(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "f75_overlay_signal_close"] = 0.0
        prior.loc[1, "f75_signal_close"] = 0.0
        with self.assertRaisesRegex(RuntimeError, "partial-exposure rule"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_requires_lagged_realized_exposure(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "f75_exposure"] = 0.75
        with self.assertRaisesRegex(RuntimeError, "not lagged"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_requires_initialization_marker_only_on_first_row(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[0, "initialization_session"] = False
        with self.assertRaisesRegex(RuntimeError, "initialization marker"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_daily_equity_reconciliation_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "f75_equity_25bps"] = 4800.0
        with self.assertRaisesRegex(RuntimeError, "equity accounting mismatch"):
            validate_existing_ledger(prior, state, ledger_bytes)

    def test_existing_ledger_nonpositive_equity_fails_closed(self):
        prior, state, ledger_bytes = self._valid_ledger_fixture()
        prior.loc[1, "b0_equity_50bps"] = 0.0
        with self.assertRaisesRegex(RuntimeError, "non-positive"):
            validate_existing_ledger(prior, state, ledger_bytes)

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
