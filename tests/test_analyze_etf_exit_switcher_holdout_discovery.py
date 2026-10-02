from pathlib import Path

from research.analyze_etf_exit_switcher_holdout import discover_paths


def test_discover_paths_excludes_summary_files(tmp_path, monkeypatch):
    root = tmp_path / "data" / "research"
    root.mkdir(parents=True)
    (root / "etf_exit_switcher_a.csv").write_text("x\n1\n")
    (root / "etf_exit_switcher_a_summary.csv").write_text("x\n1\n")

    import research.analyze_etf_exit_switcher_holdout as module
    monkeypatch.setattr(module, "ROOT", tmp_path)

    assert discover_paths("etf_exit_switcher_*.csv") == [root / "etf_exit_switcher_a.csv"]
