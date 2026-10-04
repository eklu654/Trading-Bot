from pathlib import Path

from research.test_dma_family_rotation import END as ROTATION_END

ROOT = Path(__file__).resolve().parents[1]


def test_family_rotation_matrix_uses_current_endpoint():
    source = (ROOT / "research" / "test_dma_family_rotation.py").read_text()
    assert ROTATION_END.strftime("%Y-%m-%d") == "2026-10-02"
    assert "2026-09-25" not in source


def test_family_rotation_risk_reports_use_current_endpoint():
    for relative in (
        "research/test_dma_family_rotation_risk_overlay.py",
        "research/test_dma_family_rotation_risk_overlay_robustness.py",
    ):
        source = (ROOT / relative).read_text()
        assert "2026-09-25" not in source


def test_account_replay_and_docs_use_same_terminal_date():
    replay = (ROOT / "research" / "replay_family_rotation_account.py").read_text()
    doc = (ROOT / "docs" / "02-research" / "dma-family-rotation-5000-account-replay.md").read_text()
    assert "2026-10-02" in replay
    assert "2026-10-02" in doc
    assert "On the final session, it marks the newly executed position at that day's adjusted close" in doc
