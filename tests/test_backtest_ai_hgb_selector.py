"""Unit tests for the E4b histogram-gradient-boosting selector."""

from research.backtest_ai_hgb_selector import MODEL_PARAMS, make_model


def test_hgb_parameters_are_fixed():
    model = make_model()
    for name, value in MODEL_PARAMS.items():
        assert getattr(model, name) == value
