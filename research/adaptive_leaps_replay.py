"""Chronological, quote-side LEAPS long-call replay engine.

Decisions use a completed observation-date chain and can execute only on the
next available observation date. This module is a mechanics baseline, not a
claim of executable fills or investment performance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
from typing import Iterable

from research.adaptive_leaps_lifecycle import (
    OptionQuote,
    can_execute_next_observation,
    conservative_buy_cost,
    conservative_sell_proceeds,
    select_long_call,
    should_exit_long_call,
)


@dataclass(frozen=True)
class LedgerRow:
    date: date
    event: str
    symbol: str
    cash: float
    contract_id: str | None
    dte: int | None
    bid_mark: float | None
    market_value: float | None
    equity: float | None
    realized_pnl: float
    detail: str


@dataclass(frozen=True)
class ReplayResult:
    ledger: tuple[LedgerRow, ...]
    transactions: tuple[dict, ...]
    final_cash: float
    final_equity: float | None
    final_mark_available: bool
    rejected_orders: int


def _valid_buy(q: OptionQuote | None) -> bool:
    return q is not None and q.bid > 0 and q.ask >= q.bid and q.ask > 0


def _valid_sell(q: OptionQuote | None) -> bool:
    return q is not None and q.bid > 0 and q.ask >= q.bid


def replay_long_call(
    quotes: Iterable[OptionQuote],
    *,
    symbol: str,
    starting_cash: float = 5000.0,
    target_dte: int = 270,
    target_abs_delta: float = 0.80,
    exit_dte: int = 30,
    multiplier: int = 100,
    enforce_account_cash: bool = False,
) -> ReplayResult:
    """Replay one long call, next-observation execution, ask-in/bid-out.

    If an exit quote is absent/invalid, the position remains open and the exit
    is retried. Invalid entry quotes are logged and the engine stays flat.
    Missing daily bid marks are never silently valued at zero: equity is null
    for that row and final equity is unavailable if the terminal position
    cannot be marked.
    """
    if starting_cash < 0 or multiplier <= 0:
        raise ValueError("starting_cash must be nonnegative and multiplier positive")
    source = [q for q in quotes if q.symbol.upper() == symbol.upper()]
    by_date: dict[date, list[OptionQuote]] = {}
    by_key: dict[tuple[date, str], OptionQuote] = {}
    for q in source:
        by_date.setdefault(q.observation_date, []).append(q)
        if q.contract_id:
            key = (q.observation_date, q.contract_id)
            if key in by_key:
                raise ValueError(f"duplicate quote key for {q.observation_date} / {q.contract_id}")
            by_key[key] = q
    dates = sorted(by_date)
    if not dates:
        return ReplayResult((), (), starting_cash, starting_cash, True, 0)

    cash = float(starting_cash)
    held: OptionQuote | None = None
    entry_cost: float | None = None
    pending: tuple[str, str, date] | None = None
    ledger: list[LedgerRow] = []
    transactions: list[dict] = []
    rejected = 0
    realized = 0.0

    for idx, day in enumerate(dates):
        day_quotes = by_date[day]
        event = "HOLD" if held else "FLAT"
        detail = ""
        if pending is not None:
            action, cid, signal_day = pending
            if not can_execute_next_observation(signal_day, day):
                raise AssertionError("non-causal execution attempted")
            execution_quote = by_key.get((day, cid))
            if action == "BUY":
                if not _valid_buy(execution_quote):
                    rejected += 1
                    event, detail = "ENTRY_REJECTED", "selected contract missing or invalid at next observation; no fill"
                else:
                    cost = conservative_buy_cost(execution_quote, multiplier)
                    if enforce_account_cash and cost > cash:
                        rejected += 1
                        event, detail = "ENTRY_REJECTED", f"ask cost {cost:.2f} exceeds available cash {cash:.2f}"
                    else:
                        cash -= cost
                        held, entry_cost = execution_quote, cost
                        event, detail = "BUY", "filled at next-observation ask"
                        transactions.append({
                            "date": day.isoformat(), "action": "BUY", "signal_date": signal_day.isoformat(),
                            "contract_id": cid, "price": execution_quote.ask, "multiplier": multiplier,
                            "cash_flow": -cost, "reason": "scheduled_entry",
                        })
            elif action == "SELL":
                if held is not None and held.contract_id == cid and _valid_sell(execution_quote):
                    proceeds = conservative_sell_proceeds(execution_quote, multiplier)
                    cash += proceeds
                    trade_pnl = proceeds - (entry_cost or 0.0)
                    realized += trade_pnl
                    event, detail = "SELL", "scheduled exit filled at next-observation bid"
                    transactions.append({
                        "date": day.isoformat(), "action": "SELL", "signal_date": signal_day.isoformat(),
                        "contract_id": cid, "price": execution_quote.bid, "multiplier": multiplier,
                        "cash_flow": proceeds, "trade_realized_pnl": trade_pnl, "reason": "expiry_buffer",
                    })
                    held, entry_cost = None, None
                else:
                    rejected += 1
                    event, detail = "EXIT_REJECTED", "exit quote missing/invalid; position retained and exit retried"
            pending = None

        # Refresh contract state from today's row, even when its quote is invalid.
        # Expiry/DTE are contract metadata; a bad bid must not freeze DTE at yesterday.
        if held is not None and held.contract_id:
            current_contract = by_key.get((day, held.contract_id))
            if current_contract is not None:
                held = current_contract
            else:
                # Expiry advances with calendar time even when today's chain omits the contract.
                held = replace(held, observation_date=day)
        mark_quote = by_key.get((day, held.contract_id)) if held and held.contract_id else None
        bid_mark = mark_quote.bid if _valid_sell(mark_quote) else None
        market_value = bid_mark * multiplier if bid_mark is not None else None
        equity = cash + market_value if market_value is not None else (cash if held is None else None)
        ledger.append(LedgerRow(
            date=day, event=event, symbol=symbol.upper(), cash=round(cash, 4),
            contract_id=held.contract_id if held else None,
            dte=held.dte if held else None, bid_mark=bid_mark,
            market_value=market_value, equity=round(equity, 4) if equity is not None else None,
            realized_pnl=round(realized, 4), detail=detail,
        ))

        if idx + 1 < len(dates):
            if held is not None and should_exit_long_call(held, exit_dte):
                pending = ("SELL", held.contract_id, day)
            elif held is None:
                candidate = select_long_call(day_quotes, target_dte=target_dte, target_abs_delta=target_abs_delta)
                if candidate is not None:
                    pending = ("BUY", candidate.contract_id, day)
                elif not detail:
                    ledger[-1] = LedgerRow(**{
                        **asdict(ledger[-1]), "detail": "no eligible candidate on this snapshot"
                    })

    terminal = ledger[-1] if ledger else None
    final_mark_available = terminal is not None and terminal.equity is not None
    return ReplayResult(
        tuple(ledger), tuple(transactions), cash,
        terminal.equity if final_mark_available else None,
        bool(final_mark_available), rejected,
    )
