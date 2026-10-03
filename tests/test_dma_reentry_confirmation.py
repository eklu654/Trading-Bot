from pathlib import Path

SCRIPT = Path("research/test_dma_reentry_confirmation.py").read_text()

def test_confirmation_rule_is_fixed_to_one_trading_week():
    assert "CONFIRM_SESSIONS = 5" in SCRIPT
    assert "immediate" in SCRIPT
    assert "five_session_confirmation" in SCRIPT
