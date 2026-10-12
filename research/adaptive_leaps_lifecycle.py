"""Deterministic, causal LEAPS lifecycle primitives.

No backtest P/L is produced here. Signals observed at close t are acted on at
the next available option-chain observation date, never on the same snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    observation_date: date
    expiration: date
    strike: float
    option_type: str
    delta: float
    bid: float
    ask: float
    mark: float
    volume: float | None
    open_interest: float | None
    contract_id: str = ""

    @property
    def dte(self) -> int:
        return (self.expiration - self.observation_date).days

    @property
    def relative_spread(self) -> float:
        mid = (self.bid + self.ask) / 2
        return (self.ask - self.bid) / mid if mid > 0 else float("inf")


def quote_is_eligible(q: OptionQuote, min_dte: int = 225, max_dte: int = 315) -> bool:
    """Conservative 270-DTE call eligibility; requires valid quote and activity."""
    return (
        q.option_type.lower() == "call"
        and min_dte <= q.dte <= max_dte
        and 0.60 <= abs(q.delta) <= 0.95
        and q.bid > 0
        and q.ask >= q.bid
        and q.mark > 0
        and ((q.volume or 0) > 0 or (q.open_interest or 0) > 0)
    )


def select_long_call(
    quotes: list[OptionQuote],
    target_dte: int = 270,
    target_abs_delta: float = 0.80,
) -> OptionQuote | None:
    """Choose one call by frozen lexicographic rank; no optimization."""
    min_dte, max_dte = target_dte - 45, target_dte + 45
    eligible = [q for q in quotes if quote_is_eligible(q, min_dte, max_dte)]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda q: (
            abs(q.dte - target_dte),
            abs(abs(q.delta) - target_abs_delta),
            q.relative_spread,
            -(q.open_interest or 0),
            -(q.volume or 0),
            q.expiration,
            q.strike,
            q.contract_id,
        ),
    )


def conservative_buy_cost(q: OptionQuote, multiplier: int = 100) -> float:
    if q.ask <= 0 or q.ask < q.bid:
        raise ValueError("Cannot buy using an invalid or crossed quote")
    return q.ask * multiplier


def conservative_sell_proceeds(q: OptionQuote, multiplier: int = 100) -> float:
    if q.bid <= 0 or q.ask < q.bid:
        raise ValueError("Cannot sell using an invalid or crossed quote")
    return q.bid * multiplier


def should_exit_long_call(q: OptionQuote, exit_dte: int = 30) -> bool:
    """Exit when the observed contract reaches the frozen expiry buffer."""
    return q.dte <= exit_dte


def can_execute_next_observation(signal_date: date, execution_date: date) -> bool:
    """Prevent same-snapshot fills and look-ahead execution."""
    return execution_date > signal_date
