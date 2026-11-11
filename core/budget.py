"""Deterministic budget calculations; all values use one currency and period."""
from typing import Any, Dict


def calculate_budget(*, price: float, units: float, variable_cost: float,
                     fixed_cost: float, currency: str = "USD", period: str = "month") -> Dict[str, Any]:
    values = {"price": price, "units": units, "variable_cost": variable_cost, "fixed_cost": fixed_cost}
    for name, value in values.items():
        if value is None or value != value:
            raise ValueError(f"{name} is required")
        if value < 0:
            raise ValueError(f"{name} cannot be negative")
    if not currency.strip() or not period.strip():
        raise ValueError("currency and period are required")
    if price <= variable_cost:
        raise ValueError("price must be greater than unit variable cost")
    revenue = price * units
    total_variable_cost = variable_cost * units
    profit = revenue - total_variable_cost - fixed_cost
    contribution_margin = price - variable_cost
    return {"currency": currency, "period": period, "revenue": revenue,
            "variable_cost_total": total_variable_cost, "fixed_cost": fixed_cost,
            "total_cost": total_variable_cost + fixed_cost,
            "profit": profit, "break_even_units": fixed_cost / contribution_margin,
            "break_even_revenue": fixed_cost * price / contribution_margin}

