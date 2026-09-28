"""Account-level feasibility replay for OPTIONS-001.

This module wraps the existing trade-economics replay with a deterministic
account ledger. It deliberately treats buying-power and undefined-risk
requirements as modeled estimates, not broker-observed values.

Input is a complete candidate ledger plus independently reconstructed
candidate lifecycles. This separation is important: the account engine must
not inherit the baseline strategy's one-position sequencing or silently lose
opportunities that were rejected only because another candidate was open.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "data" / "research"


@dataclass(frozen=True)
class FeasibilityConfig:
    starting_nlv: float = 2000.0
    contract_multiplier: int = 100
    max_bpr_pct_nlv: float = 0.50
    fee_per_contract: float = 0.65
    slippage_credit: float = 0.0
    stress_multiplier: float = 1.00
    fill_model: str = "conservative"
    max_concurrent_positions: int = 1
    pnl_reconciliation_tolerance: float = 0.01
    pnl_reconciliation_tolerance: float = 0.01

    @property
    def max_bpr_dollars(self) -> float:
        return self.starting_nlv * self.max_bpr_pct_nlv


def _finite(value: object) -> bool:
    return pd.notna(value) and float(value) == float(value)


def estimate_short_strangle_bpr(
    underlying: float,
    put_strike: float,
    call_strike: float,
    credit: float,
    multiplier: int = 100,
    stress_multiplier: float = 1.0,
) -> float:
    """Conservative modeled BPR estimate for one naked short strangle.

    This is deliberately an estimate rather than a broker preview. For each
    short leg we use the common 20%-of-underlying-minus-OTM amount framework,
    floored at 10% of underlying, plus the received credit. The larger leg
    requirement is used for the strangle and then multiplied by the configured
    stress factor.

    The formula is a research assumption and must not be interpreted as an
    Alpaca/OCC buying-power quotation.
    """
    if underlying <= 0 or credit < 0:
        raise ValueError("underlying must be positive and credit nonnegative")
    call_otm = max(call_strike - underlying, 0.0)
    put_otm = max(underlying - put_strike, 0.0)

    call_req = max(
        0.20 * underlying - call_otm,
        0.10 * underlying,
    )
    put_req = max(
        0.20 * underlying - put_otm,
        0.10 * underlying,
    )
    # Add the premium received to the larger naked-leg requirement.
    return max(call_req, put_req) * multiplier + credit * multiplier * stress_multiplier


def max_stress_loss(
    underlying: float,
    put_strike: float,
    call_strike: float,
    credit: float,
    multiplier: int = 100,
    stress_multiplier: float = 1.0,
) -> float:
    """Finite stress loss for a naked strangle using a 20% underlying move."""
    if underlying <= 0:
        raise ValueError("underlying must be positive")
    lower = underlying * (1.0 - 0.20 * stress_multiplier)
    upper = underlying * (1.0 + 0.20 * stress_multiplier)
    put_loss = max(put_strike - lower, 0.0)
    call_loss = max(upper - call_strike, 0.0)
    return max(put_loss, call_loss) * multiplier - credit * multiplier


def replay(
    candidates: pd.DataFrame,
    config: FeasibilityConfig,
    outcomes: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    required = {"entry_date", "entry_credit", "call_strike", "put_strike"}
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(f"candidate input missing required columns: {sorted(missing)}")

    frame = candidates.copy()
    frame["entry_date"] = pd.to_datetime(frame["entry_date"])
    if "candidate_id" not in frame.columns:
        frame["candidate_id"] = (
            frame["entry_date"].dt.strftime("%Y-%m-%d") + ":" + frame.index.astype(str)
        )

    if outcomes is not None:
        outcome_required = {"candidate_id", "exit_date", "pnl"}
        missing_outcomes = outcome_required - set(outcomes.columns)
        if missing_outcomes:
            raise ValueError(f"outcome input missing required columns: {sorted(missing_outcomes)}")
        outcome_columns = list(outcome_required)
        if "exit_debit" in outcomes.columns:
            outcome_columns.append("exit_debit")
        outcome_frame = outcomes[outcome_columns].copy()
        outcome_frame["exit_date"] = pd.to_datetime(outcome_frame["exit_date"])
        if outcome_frame["candidate_id"].duplicated().any():
            raise ValueError("outcome input contains duplicate candidate_id values")
        frame = frame.merge(outcome_frame, on="candidate_id", how="left", validate="one_to_one")
    elif not {"exit_date", "pnl"}.issubset(frame.columns):
        raise ValueError("outcomes are required unless candidates contain exit_date and pnl")

    frame["exit_date"] = pd.to_datetime(frame.get("exit_date"), errors="coerce")
    frame = frame.sort_values(["entry_date", "candidate_id"]).reset_index(drop=True)

    cash = float(config.starting_nlv)
    active: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    def open_value() -> float:
        return float(sum(float(p["position_value"]) for p in active))

    def active_bpr() -> float:
        return float(sum(float(p["bpr"]) for p in active))

    def active_stress_loss() -> float:
        return float(sum(float(p["stress_loss"]) for p in active))

    def settle_positions_through(timestamp: pd.Timestamp) -> None:
        nonlocal cash, active
        settling = [p for p in active if pd.Timestamp(p["exit_date"]) <= timestamp]
        if not settling:
            return
        for position in sorted(settling, key=lambda p: (pd.Timestamp(p["exit_date"]), str(p["candidate_id"]))):
            cash += float(position["exit_cash_flow"])
            row = rows[int(position["row_index"])]
            remaining_value = open_value() - float(position["position_value"])
            row["cash_after_exit"] = cash
            row["open_position_value_after_exit"] = remaining_value
            row["post_exit_nlv"] = cash + remaining_value
            row["post_trade_nlv"] = row["post_exit_nlv"]
            active.remove(position)

    for i, row in frame.iterrows():
        entry = pd.Timestamp(row["entry_date"])
        settle_positions_through(entry)
        nlv_before = cash + open_value()
        exit_date = row["exit_date"]
        credit = float(row["entry_credit"])

        if _finite(row.get("exit_debit")):
            exit_debit = float(row["exit_debit"])
        elif _finite(row.get("pnl")):
            exit_debit = credit - float(row["pnl"]) / config.contract_multiplier
        else:
            exit_debit = float("nan")

        rejection: list[str] = []
        pnl_reconciliation_residual = float("nan")

        if credit <= 0:
            rejection.append("NONPOSITIVE_CREDIT")
        if not _finite(row.get("call_strike")) or not _finite(row.get("put_strike")):
            rejection.append("MISSING_STRIKES")
        if pd.isna(exit_date) or not _finite(row.get("pnl")) or not _finite(exit_debit):
            rejection.append("UNRESOLVED_LIFECYCLE_DATA")
        elif exit_date <= entry:
            rejection.append("INVALID_LIFECYCLE_DATES")
        else:
            pnl_from_quotes = (credit - exit_debit) * config.contract_multiplier
            pnl_reconciliation_residual = float(row["pnl"]) - pnl_from_quotes
            if abs(pnl_reconciliation_residual) > config.pnl_reconciliation_tolerance:
                rejection.append("PNL_RECONCILIATION_MISMATCH")

        underlying = row.get("underlying_close", float("nan"))
        if active and len(active) + 1 > config.max_concurrent_positions:
            rejection.append("POSITION_ALREADY_OPEN" if config.max_concurrent_positions == 1 else "MAX_CONCURRENT_POSITIONS")

        if not _finite(underlying):
            rejection.append("MISSING_UNDERLYING_PRICE")
            bpr = float("nan")
            stress_loss = float("nan")
        else:
            bpr = estimate_short_strangle_bpr(
                float(underlying), float(row["put_strike"]), float(row["call_strike"]),
                credit, config.contract_multiplier, config.stress_multiplier,
            )
            stress_loss = max_stress_loss(
                float(underlying), float(row["put_strike"]), float(row["call_strike"]),
                credit, config.contract_multiplier, config.stress_multiplier,
            )
            bp_limit = min(config.max_bpr_dollars, nlv_before * config.max_bpr_pct_nlv)
            if active_bpr() + bpr > bp_limit:
                rejection.append("AGGREGATE_BUYING_POWER_LIMIT" if active else "BUYING_POWER_LIMIT")
            if active_stress_loss() + stress_loss >= nlv_before:
                rejection.append("AGGREGATE_STRESS_LOSS_EXCEEDS_NLV" if active else "STRESS_LOSS_EXCEEDS_NLV")

        accepted = not rejection
        entry_fee = 2.0 * config.fee_per_contract if accepted else 0.0
        exit_fee = 2.0 * config.fee_per_contract if accepted else 0.0
        fees = entry_fee + exit_fee
        pnl = float(row["pnl"]) if accepted and _finite(row.get("pnl")) else 0.0
        entry_cash_flow = credit * config.contract_multiplier - entry_fee if accepted else 0.0
        entry_position_value = -credit * config.contract_multiplier if accepted else 0.0
        exit_cash_flow = -(exit_debit * config.contract_multiplier) - exit_fee if accepted else 0.0

        row_index = len(rows)
        if accepted:
            cash += entry_cash_flow
            active.append({
                "candidate_id": row["candidate_id"],
                "exit_date": pd.Timestamp(exit_date),
                "position_value": entry_position_value,
                "bpr": bpr,
                "stress_loss": stress_loss,
                "exit_cash_flow": exit_cash_flow,
                "row_index": row_index,
            })

        nlv_after_entry = cash + open_value()
        rows.append({
            "candidate_index": i,
            "candidate_id": row["candidate_id"],
            "account_id": f"NLV_{config.starting_nlv:g}",
            "mode": "account_feasibility_estimate",
            "entry_date": entry,
            "exit_date": exit_date,
            "pre_trade_nlv": nlv_before,
            "entry_cash_flow": entry_cash_flow,
            "entry_position_value": entry_position_value,
            "nlv_after_entry": nlv_after_entry,
            "exit_cash_flow": exit_cash_flow,
            "exit_debit": exit_debit,
            "cash_after_exit": float("nan"),
            "open_position_value_after_exit": float("nan"),
            "post_exit_nlv": float("nan"),
            "bpr_estimate": bpr,
            "aggregate_bpr_pre_trade": active_bpr(),
            "aggregate_stress_loss_pre_trade": active_stress_loss(),
            "bpr_pct_pre_trade_nlv": bpr / nlv_before if _finite(bpr) and nlv_before else float("nan"),
            "stress_loss": stress_loss,
            "fees": fees,
            "gross_pnl": pnl,
            "net_pnl": pnl - fees,
            "pnl_reconciliation_residual": pnl_reconciliation_residual,
            "accepted": accepted,
            "rejection_codes": "|".join(rejection),
            "post_trade_nlv": nlv_after_entry,
        })

    if active:
        settle_positions_through(pd.to_datetime(frame["exit_date"].dropna().max()))
    ending_nlv = cash
    ledger = pd.DataFrame(rows)
    summary = {
        "starting_nlv": config.starting_nlv,
        "ending_nlv": ending_nlv,
        "candidate_count": float(len(ledger)),
        "accepted_count": float(ledger["accepted"].sum()) if len(ledger) else 0.0,
        "rejected_count": float((~ledger["accepted"]).sum()) if len(ledger) else 0.0,
        "fees": float(ledger["fees"].sum()) if len(ledger) else 0.0,
        "net_pnl": ending_nlv - config.starting_nlv,
    }
    return ledger, summary

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OPTIONS-001 $2,000 account feasibility replay")
    p.add_argument("--input", required=True, help="Complete OPTIONS-001 candidate ledger CSV")
    p.add_argument("--outcomes", default=None, help="Independent candidate lifecycle CSV")
    p.add_argument("--output", default=None, help="Ledger CSV path")
    p.add_argument("--starting-nlv", type=float, default=2000.0)
    p.add_argument("--max-bpr-pct", type=float, default=0.50)
    p.add_argument("--fee-per-contract", type=float, default=0.65)
    p.add_argument("--max-concurrent-positions", type=int, default=1)
    p.add_argument("--stress-multiplier", type=float, default=1.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.input)
    candidates = pd.read_csv(source)
    outcomes = pd.read_csv(Path(args.outcomes)) if args.outcomes else None

    # Candidate replay persists the underlying close; reconstruct it only for
    # older candidate files that do not contain it.
    # from the authoritative historical regime dataset before feasibility testing.
    regime = pd.read_csv(
        RESEARCH_DIR / "historical_regime_dataset.csv",
        parse_dates=["Date"],
    )
    regime = regime.set_index("Date").sort_index()
    candidates["entry_date"] = pd.to_datetime(candidates["entry_date"])
    if "underlying_close" not in candidates.columns:
        candidates["underlying_close"] = candidates["entry_date"].map(regime["spy_close"])

    config = FeasibilityConfig(
        starting_nlv=args.starting_nlv,
        max_bpr_pct_nlv=args.max_bpr_pct,
        fee_per_contract=args.fee_per_contract,
        max_concurrent_positions=args.max_concurrent_positions,
        stress_multiplier=args.stress_multiplier,
    )
    ledger, summary = replay(candidates, config, outcomes)

    output = Path(args.output) if args.output else source.with_name(
        source.stem + f"_account_{int(args.starting_nlv)}.csv"
    )
    ledger.to_csv(output, index=False)

    print("OPTIONS-001 account feasibility replay")
    for key, value in summary.items():
        print(f"{key}={value}")
    print("rejections:")
    rejected = ledger.loc[~ledger["accepted"], "rejection_codes"]
    if rejected.empty:
        print("none")
    else:
        print(rejected.to_string(index=False))


if __name__ == "__main__":
    main()
