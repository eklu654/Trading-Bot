"""Reconcile the hand-maintained FED_EVENTS table against FRED daily target-rate history.

This is a data-source/timing audit, not a strategy backtest. It does not alter
FED_EVENTS or select policy dates; it reports rate mismatches and the nearest
observed transition dates for manual review.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "tqqq_three_layer_event_attribution.py"
OUT = ROOT / "data" / "research"
SERIES = ("DFEDTAR", "DFEDTARL", "DFEDTARU")
MAX_SEARCH_DAYS = 7


def read_event_table(path: Path = SOURCE) -> list[tuple[str, float, float]]:
    """Read FED_EVENTS as a literal without importing the research module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "FED_EVENTS"
            for target in node.targets
        ):
            raw = ast.literal_eval(node.value)
            return [(str(d), float(change), float(target)) for d, change, target in raw]
    raise ValueError(f"FED_EVENTS assignment not found in {path}")


def download_series(series_id: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = Request(url, headers={"User-Agent": "Trading-Bot-Fed-Audit/1.0"})
    with urlopen(req, timeout=30) as response:
        frame = pd.read_csv(response)
    date_col = "observation_date" if "observation_date" in frame.columns else frame.columns[0]
    value_col = series_id if series_id in frame.columns else frame.columns[-1]
    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    series = frame.dropna(subset=[date_col]).set_index(date_col)[value_col].dropna().sort_index()
    series.index = pd.DatetimeIndex(series.index).tz_localize(None)
    return series[~series.index.duplicated(keep="last")]


def download_target() -> pd.Series:
    parts = {sid: download_series(sid) for sid in SERIES}
    index = parts["DFEDTAR"].index.union(parts["DFEDTARL"].index).union(parts["DFEDTARU"].index)
    frame = pd.DataFrame({k: v.reindex(index) for k, v in parts.items()}).sort_index()
    target = frame["DFEDTAR"].copy()
    midpoint_ok = frame["DFEDTARL"].notna() & frame["DFEDTARU"].notna()
    target.loc[midpoint_ok] = (
        frame.loc[midpoint_ok, "DFEDTARL"] + frame.loc[midpoint_ok, "DFEDTARU"]
    ) / 2.0
    return target.dropna()


def reconcile(events: list[tuple[str, float, float]], target: pd.Series) -> pd.DataFrame:
    rows = []
    for i, (date_text, change, new_rate) in enumerate(events):
        date = pd.Timestamp(date_text)
        prior_rate = float(events[i - 1][2]) if i else float("nan")
        prior_rows = target.loc[target.index < date]
        on_or_after = target.loc[target.index >= date]
        before = float(prior_rows.iloc[-1]) if len(prior_rows) else float("nan")
        after = float(on_or_after.iloc[0]) if len(on_or_after) else float("nan")
        after_date = on_or_after.index[0] if len(on_or_after) else pd.NaT
        expected_before = prior_rate
        expected_after = new_rate
        observed_delta = after - before if pd.notna(after) and pd.notna(before) else float("nan")
        nearest = target.loc[
            (target.index >= date - pd.Timedelta(days=MAX_SEARCH_DAYS))
            & (target.index <= date + pd.Timedelta(days=MAX_SEARCH_DAYS))
        ]
        match_dates = nearest.index[(nearest - new_rate).abs() < 0.001]
        rows.append({
            "event_date": date.date().isoformat(),
            "listed_change": change,
            "listed_prior_rate": expected_before,
            "listed_new_rate": expected_after,
            "fred_last_rate_before_event_date": before,
            "fred_first_rate_on_or_after_event_date": after,
            "fred_first_on_or_after_date": after_date.date().isoformat() if pd.notna(after_date) else "",
            "observed_delta_across_event_date": observed_delta,
            "new_rate_seen_within_7d": bool(len(match_dates)),
            "first_matching_new_rate_date_within_7d": match_dates[0].date().isoformat() if len(match_dates) else "",
            "prior_rate_matches": bool(pd.notna(before) and abs(before - expected_before) < 0.001),
            "new_rate_matches": bool(pd.notna(after) and abs(after - expected_after) < 0.001),
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    events = read_event_table()
    target = download_target()
    ledger = reconcile(events, target)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    fred_hash = hashlib.sha256(target.to_csv(float_format="%.8f").encode()).hexdigest()
    ledger.to_csv(OUT / "fed_event_table_fred_reconciliation.csv", index=False)
    manifest = {
        "source_file": str(SOURCE.relative_to(ROOT)),
        "source_sha256": source_hash,
        "fred_target_series_sha256": fred_hash,
        "event_count": len(events),
        "fred_rows": len(target),
        "fred_first_date": target.index.min().date().isoformat(),
        "fred_last_date": target.index.max().date().isoformat(),
        "prior_rate_mismatches": int((~ledger["prior_rate_matches"]).sum()),
        "new_rate_mismatches_on_or_after_event_date": int((~ledger["new_rate_matches"]).sum()),
        "events_without_new_rate_seen_within_7d": int((~ledger["new_rate_seen_within_7d"]).sum()),
        "note": "Mismatch flags are diagnostics. Announcement/effective-date semantics require manual review; no event dates are automatically shifted.",
    }
    (OUT / "fed_event_table_fred_reconciliation_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    print("\nEvents with a rate/date discrepancy (first 40):")
    flagged = ledger.loc[
        ~ledger["prior_rate_matches"] | ~ledger["new_rate_matches"]
        | ~ledger["new_rate_seen_within_7d"]
    ]
    print(flagged.head(40).to_string(index=False) if len(flagged) else "None")


if __name__ == "__main__":
    main()
