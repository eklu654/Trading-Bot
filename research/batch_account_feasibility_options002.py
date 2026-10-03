"""Batch OPTIONS-002 account-feasibility replays for one regime/fill.

Loads the candidate/outcome/mark CSVs once and reuses the same in-memory
inputs across the 27 NLV/risk configurations. The underlying replay function
and all calculation semantics remain unchanged; this only removes repeated
CSV parsing and process startup overhead.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from account_feasibility_options002 import replay


NLVS = (2000, 3000, 5000, 7500, 10000, 15000, 25000, 50000, 100000)
RISKS = (0.03, 0.05, 0.07)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--regime", choices=("all_days", "broad_sideways", "turbulent_only"), required=True)
    p.add_argument("--fill-model", choices=("conservative", "mid"), required=True)
    p.add_argument("--data-dir", default="data/research")
    args = p.parse_args()

    base = Path(args.data_dir)
    stem = f"options002_delta16_w2_{args.regime}_{args.fill_model}"

    candidates = pd.read_csv(base / f"{stem}_candidates.csv")
    outcomes = pd.read_csv(base / f"{stem}_candidate_outcomes.csv")
    marks = pd.read_csv(base / f"{stem}_candidate_marks.csv")

    print(
        f"OPTIONS-002 batch {stem}: "
        f"candidates={len(candidates)} outcomes={len(outcomes)} marks={len(marks)}",
        flush=True,
    )

    for starting_nlv in NLVS:
        for max_risk_pct in RISKS:
            output = base / f"{stem}_account_{starting_nlv}_risk_{max_risk_pct}.csv"
            replay_args = argparse.Namespace(
                starting_nlv=starting_nlv,
                max_bpr_pct=0.50,
                max_risk_pct=max_risk_pct,
                fee_per_contract=0.65,
                output=str(output),
            )
            replay(candidates, outcomes, marks, replay_args)
            print(
                f"completed {stem} nlv={starting_nlv} risk={max_risk_pct}",
                flush=True,
            )


if __name__ == "__main__":
    main()
