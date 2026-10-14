from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowTriggerScopeTests(unittest.TestCase):
    def test_tqqq_partial_matrices_only_watch_their_inputs(self) -> None:
        cases = {
            "tqqq-partial-dma-matrix.yml": "research/tqqq_partial_dma_matrix.py",
            "tqqq-actual-partial-dma-matrix.yml": "research/tqqq_actual_partial_dma_matrix.py",
        }
        for filename, entrypoint in cases.items():
            with self.subTest(workflow=filename):
                text = (WORKFLOWS / filename).read_text(encoding="utf-8")
                self.assertNotIn('"research/*.py"', text)
                self.assertNotIn('"research/**/*.py"', text)
                self.assertIn(f'"{entrypoint}"', text)
                self.assertIn('"research/causal_execution.py"', text)
                self.assertIn('"research/reentry_isolation.py"', text)
                self.assertIn("workflow_dispatch:", text)
                self.assertNotIn(f'".github/workflows/{filename}"', text)

    def test_full_research_suite_skips_docs_only_changes(self) -> None:
        text = (WORKFLOWS / "research-tests.yml").read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("    paths:"), 2)
        self.assertIn('"research/**/*.py"', text)
        self.assertIn('"tests/**"', text)
        self.assertIn('"data/**"', text)
        self.assertNotIn('"docs/**"', text)

    def test_replay_receipt_is_not_a_replay_trigger(self) -> None:
        text = (WORKFLOWS / "adaptive-leaps-replay.yml").read_text(encoding="utf-8")
        trigger = text.split("permissions:", maxsplit=1)[0]
        self.assertIn('"research/adaptive_leaps_replay.py"', trigger)
        self.assertNotIn("docs/LEAPS_REPLAY_LATEST_RUN.md", trigger)


if __name__ == "__main__":
    unittest.main()
