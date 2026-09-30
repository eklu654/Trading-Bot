import pandas as pd

from research.analyze_options002_capital_ladder import PATTERN


def test_capital_ladder_pattern_accepts_wider_strategy_labels():
    name = "options002_delta20_w10_broad_sideways_mid_account_5000_risk_0.05_summary.csv"
    m = PATTERN.fullmatch(name)
    assert m is not None
    assert m.group("label") == "delta20_w10"
    assert m.group("candidate") == "broad_sideways"
    assert m.group("fill") == "mid"
    assert m.group("nlv") == "5000"
    assert m.group("risk") == "0.05"


def test_capital_ladder_pattern_keeps_legacy_label():
    name = "options002_delta16_w2_all_days_conservative_account_2000_risk_0.03_summary.csv"
    m = PATTERN.fullmatch(name)
    assert m is not None
    assert m.group("label") == "delta16_w2"
