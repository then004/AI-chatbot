from .business_plan import BusinessPlan
from .budget import calculate_budget


def compose_plan(title, user_inputs, evidence, assumptions=None, budget=None, recommendations=None, gaps=None):
    plan = BusinessPlan(title, user_inputs=user_inputs, evidence=list(evidence), assumptions=assumptions or [], calculations=budget or {}, recommendations=recommendations or [], gaps=gaps or [])
    plan.validate()
    return plan


def compose_budgeted_plan(title, user_inputs, evidence, assumptions, budget_inputs, recommendations=None, gaps=None):
    budget = calculate_budget(**budget_inputs)
    return compose_plan(title, user_inputs, evidence, assumptions, budget, recommendations, gaps)
