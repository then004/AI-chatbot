import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.business_plan import BusinessPlan
from core.budget import calculate_budget
from core.html_renderer import render_business_plan

run_id = "m1-" + uuid4().hex[:12]
out = ROOT / "docs" / "reports" / "artifacts" / run_id
out.mkdir(parents=True, exist_ok=False)
budget = calculate_budget(price=25, units=120, variable_cost=9, fixed_cost=900, currency="GBP", period="month")
plan = BusinessPlan("Local Repair Booking Service", user_inputs={"price": 25, "units": 120, "currency": "GBP", "period": "month"}, evidence=[{"source": "sample-user-input", "page": "n/a", "text": "Customer interviews indicate demand."}], assumptions=["120 bookings per month"], calculations=budget, recommendations=["Validate demand with a small pilot"], gaps=["Competitor pricing not yet verified"])
plan.validate()
(out / "Business_Plan.json").write_text(json.dumps(plan.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
(out / "Business_Plan.html").write_text(render_business_plan(plan), encoding="utf-8")
print(json.dumps({"run_id": run_id, "directory": str(out), "json": str(out / "Business_Plan.json"), "html": str(out / "Business_Plan.html")}, ensure_ascii=False))
