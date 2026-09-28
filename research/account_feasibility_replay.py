"""Account-level feasibility replay for OPTIONS-001.

This module wraps the existing trade-economics replay with a deterministic
account ledger. It deliberately treats buying-power and undefined-risk
requirements as modeled estimates, not broker-observed values.

Input CSV is the first-pass OPTIONS-001 trade-economics output. Each row is
treated as a candidate opportunity. This is intentionally a separate layer:
trade economics remain unchanged while account feasibility decides whether the
candidate could have been carried by the configured account.

The next iteration can consume a richer candidate ledger without changing the
account engine.
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
) -> tuple[pd.DataFrame, dict[str, float]]:
    required = {
        "entry_date", "exit_date", "entry_credit", "pnl",
        "call_strike", "put_strike",
    }
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(f"candidate input missing required columns: {sorted(missing)}")

    frame = candidates.copy()
    frame["entry_date"] = pd.to_datetime(frame["entry_date"])
    frame["exit_date"] = pd.to_datetime(frame["exit_date"])
    frame = frame.sort_values(["entry_date", "exit_date"]).reset_index(drop=True)

    nlv = float(config.starting_nlv)
    open_until = pd.Timestamp.min
    rows: list[dict[str, object]] = []

    for i, row in frame.iterrows():
        entry = pd.Timestamp(row["entry_date"])
        exit_date = pd.Timestamp(row["exit_date"])
        credit = float(row["entry_credit"])
        pnl = float(row["pnl"])

        rejection: list[str] = []
        if entry <= open_until:
            rejection.append("POSITION_ALREADY_OPEN")
        if credit <= 0:
            rejection.append("NONPOSITIVE_CREDIT")
        if not _finite(row.get("call_strike")) or not _finite(row.get("put_strike")):
            rejection.append("MISSING_STRIKES")

        underlying = row.get("underlying_close", float("nan"))
        if not _finite(underlying):
            rejection.append("MISSING_UNDERLYING_PRICE")
            bpr = float("nan")
            stress_loss = float("nan")
        else:
            bpr = estimate_short_strangle_bpr(
                float(underlying),
                float(row["put_strike"]),
                float(row["call_strike"]),
                credit,
                config.contract_multiplier,
                config.stress_multiplier,
            )
            stress_loss = max_stress_loss(
                float(underlying),
                float(row["put_strike"]),
                float(row["call_strike"]),
                credit,
                config.contract_multiplier,
                config.stress_multiplier,
            )
            if bpr > min(config.max_bpr_dollars, nlv * config.max_bpr_pct_nlv):
                rejection.append("BUYING_POWER_LIMIT")
            if stress_loss >= nlv:
                rejection.append("STRESS_LOSS_EXCEEDS_NLV")

        accepted = not rejection
        fees = 2.0 * config.fee_per_contract if accepted else 0.0
        net_pnl = pnl - fees if accepted else 0.0
        nlv_before = nlv

        if accepted:
            nlv += net_pnl
            open_until = exit_date

        rows.append({
            "candidate_index": i,
            "account_id": f"NLV_{config.starting_nlv:g}",
            "mode": "account_feasibility_estimate",
            "entry_date": entry,
            "exit_date": exit_date,
            "pre_trade_nlv": nlv_before,
            "bpr_estimate": bpr,
            "bpr_pct_pre_trade_nlv": bpr / nlv_before if _finite(bpr) and nlv_before else float("nan"),
            "stress_loss": stress_loss,
            "fees": fees,
            "gross_pnl": pnl if accepted else 0.0,
            "net_pnl": net_pnl,
            "accepted": accepted,
            "rejection_codes": "|".join(rejection),
            "post_trade_nlv": nlv,
        })

    ledger = pd.DataFrame(rows)
    summary = {
        "starting_nlv": config.starting_nlv,
        "ending_nlv": nlv,
        "candidate_count": float(len(ledger)),
        "accepted_count": float(ledger["accepted"].sum()) if len(ledger) else 0.0,
        "rejected_count": float((~ledger["accepted"]).sum()) if len(ledger) else 0.0,
        "fees": float(ledger["fees"].sum()) if len(ledger) else 0.0,
        "net_pnl": nlv - config.starting_nlv,
    }
    return ledger, summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OPTIONS-001 $2,000 account feasibility replay")
    p.add_argument("--input", required=True, help="OPTIONS-001 trade-economics CSV")
    p.add_argument("--output", default=None, help="Ledger CSV path")
    p.add_argument("--starting-nlv", type=float, default=2000.0)
    p.add_argument("--max-bpr-pct", type=float, default=0.50)
    p.add_argument("--fee-per-contract", type=float, default=0.65)
    p.add_argument("--stress-multiplier", type=float, default=1.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.input)
    candidates = pd.read_csv(source)

    # First-pass replay does not persist the underlying close, so reconstruct it
    # from the authoritative historical regime dataset before feasibility testing.
    regime = pd.read_csv(
        RESEARCH_DIR / "historical_regime_dataset.csv",
        parse_dates=["Date"],
    )
    regime = regime.set_index("Date").sort_index()
    candidates["entry_date"] = pd.to_datetime(candidates["entry_date"])
    candidates["underlying_close"] = candidates["entry_date"].map(regime["spy_close"])

    config = FeasibilityConfig(
        starting_nlv=args.starting_nlv,
        max_bpr_pct_nlv=args.max_bpr_pct,
        fee_per_contract=args.fee_per_contract,
        stress_multiplier=args.stress_multiplier,
    )
    ledger, summary = replay(candidates, config)

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
