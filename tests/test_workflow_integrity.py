from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dynamic_etf_workflow_uses_supported_parallel_shell_step():
    workflow = (ROOT / ".github" / "workflows" / "dynamic-etf-research.yml").read_text()
    assert "      - parallel:" not in workflow
    assert "      - name: Run parallel research analyses" in workflow
    assert "pids+=($!)" in workflow
    assert 'for pid in "${pids[@]}"; do' in workflow


def test_dynamic_etf_workflow_keeps_common_benchmark_artifacts():
    workflow = (ROOT / ".github" / "workflows" / "dynamic-etf-research.yml").read_text()
    assert "data/research/leverage_strategy_comparison.csv" in workflow
    assert "data/research/leverage_strategy_comparison_2018_2025.csv" in workflow
