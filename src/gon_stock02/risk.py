from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR


@dataclass(frozen=True)
class EntryState:
    equity: str
    day_open_equity: str
    peak_equity: str
    cash: str
    gross_exposure: str
    symbol_exposure: str
    positions: int
    entries_today: int
    quote_age_seconds: float | None
    venue_verified: bool
    reserved_loss_krw: str


def assess_entry(policy, state, symbol, venue, entry, stop, cost_per_share):
    try:
        fields = [state.equity, state.day_open_equity, state.peak_equity, state.cash,
                  state.gross_exposure, state.symbol_exposure, entry, stop, cost_per_share, state.reserved_loss_krw]
        values = [Decimal(str(value)) for value in fields]
        if any(not value.is_finite() or value < 0 for value in values):
            return {"allowed": False, "reason": "invalid_numbers"}
        equity, day_open, peak, cash, gross, exposure, entry, stop, cost, reserved_loss = values
        if type(state.positions) is not int or type(state.entries_today) is not int:
            return {"allowed": False, "reason": "invalid_positions"}
        for key in ("max_positions", "max_entries_per_symbol_per_day", "max_quote_age_seconds"):
            if type(policy[key]) is not int or policy[key] <= 0:
                return {"allowed": False, "reason": "invalid_policy"}
        ratios = [Decimal(policy[key]) for key in ("risk_per_trade", "daily_loss_limit", "drawdown_limit", "max_symbol_allocation", "max_gross_allocation")]
        if any(not value.is_finite() or value <= 0 or value > 1 for value in ratios):
            return {"allowed": False, "reason": "invalid_policy"}
        trade_risk, daily, drawdown, symbol_cap, total_cap = ratios
        initial = Decimal(policy["initial_capital_krw"])
        if not initial.is_finite() or initial <= 0 or min(equity, day_open, peak, entry) <= 0 or stop >= entry or peak < equity:
            return {"allowed": False, "reason": "invalid_numbers"}
        if state.positions < 0 or state.entries_today < 0 or exposure > gross or (exposure > 0 and state.positions == 0):
            return {"allowed": False, "reason": "invalid_positions"}
        if policy["environment"] != "mock" or symbol not in policy["symbols"] or venue not in policy["paper_order_venues"]:
            return {"allowed": False, "reason": "instrument_or_environment_blocked"}
        age = state.quote_age_seconds
        if type(age) not in (int, float) or not Decimal(str(age)).is_finite() or age < 0 or age > policy["max_quote_age_seconds"] or state.venue_verified is not True:
            return {"allowed": False, "reason": "unverified_or_stale_quote"}
        if equity <= day_open * (1 - daily) or equity <= initial * (1 - drawdown) or equity <= peak * (1 - drawdown):
            return {"allowed": False, "reason": "loss_limit"}
        if state.entries_today >= policy["max_entries_per_symbol_per_day"]:
            return {"allowed": False, "reason": "entry_limit"}
        if exposure == 0 and state.positions >= policy["max_positions"]:
            return {"allowed": False, "reason": "position_limit"}
        capital = min(initial, day_open, equity)
        available = min(cash, capital * symbol_cap - exposure, capital * total_cap - gross)
        remaining_loss = min(equity - day_open * (1 - daily), equity - initial * (1 - drawdown),
                             equity - peak * (1 - drawdown)) - reserved_loss
        risk_budget = max(Decimal(0), min(capital * trade_risk, remaining_loss))
        quantity = min((risk_budget / (entry - stop + cost)).to_integral_value(rounding=ROUND_FLOOR),
                       (max(Decimal(0), available) / (entry + cost)).to_integral_value(rounding=ROUND_FLOOR))
        if quantity < 1:
            return {"allowed": False, "reason": "minimum_lot_exceeds_limit"}
        enabled = policy.get("order_submission_enabled") is True
        return {"allowed": enabled, "risk_passed": True, "reason": "risk_passed" if enabled else "execution_gate_closed",
                "quantity": int(quantity), "planned_loss_krw": str(quantity * (entry - stop + cost))}
    except (KeyError, TypeError, ValueError, InvalidOperation, ZeroDivisionError):
        return {"allowed": False, "reason": "invalid_input"}
