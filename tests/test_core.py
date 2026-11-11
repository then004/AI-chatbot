import unittest
from core.business_plan import BusinessPlan
from core.budget import calculate_budget
from core.html_renderer import render_business_plan


class CoreTests(unittest.TestCase):
    def test_budget(self):
        result = calculate_budget(price=10, units=100, variable_cost=4, fixed_cost=300)
        self.assertEqual(result["revenue"], 1000)
        self.assertEqual(result["profit"], 300)
        self.assertEqual(result["break_even_units"], 50)

    def test_budget_boundaries(self):
        for kwargs in ({"price": 4, "units": 1, "variable_cost": 4, "fixed_cost": 1},
                       {"price": 10, "units": -1, "variable_cost": 4, "fixed_cost": 1}):
            with self.assertRaises(ValueError): calculate_budget(**kwargs)

    def test_renderer_escapes(self):
        plan = BusinessPlan("<unsafe>", evidence=[{"source": "s", "text": "<script>alert(1)</script>"}])
        output = render_business_plan(plan)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

    def test_renderer_business_dicts_and_page_labels(self):
        plan = BusinessPlan('创立咖啡店', user_inputs={'idea':'创立咖啡店'}, evidence=[{'source':'C:\\docs\\menu.pdf','page':0,'text':'coffee'}], assumptions=[{'id':'a1','text':'租金稳定','supporting_evidence':['ev-1']}], calculations={'revenue':1000.0,'profit':300.0,'currency':'CNY','period':'month'})
        output=render_business_plan(plan)
        self.assertIn('租金稳定', output); self.assertIn('ev-1', output); self.assertNotIn("{'id':", output); self.assertIn('PDF 第1页（索引0）', output); self.assertIn('menu.pdf', output); self.assertIn('创业想法', output); self.assertIn('1,000.0', output)

    def test_renderer_has_report_sections_and_safe_template(self):
        plan = BusinessPlan(
            "AI <script>idea</script>",
            user_inputs={"idea": "<img src=x onerror=alert(1)>"},
            evidence=[{"source": "source.pdf", "page": 4, "text": "<script>bad()</script>"}],
            calculations={"revenue": 1000, "total_cost": 700, "profit": 300, "break_even_units": 50},
            assumptions=["<b>assumption</b>"], recommendations=["Validate pricing"], gaps=["Need more evidence"],
        )
        output = render_business_plan(plan)
        for marker in ("class=\"container report\"", "class=\"section executive-summary\"", "class=\"section strategic-plan\"", "class=\"section financial-plan\"", "class=\"section operational-plan\"", "class=\"section risk-analysis\"", "#e3f2fd", "#f3e5f5", "#e8f5e9", "class=\"cover\"", "执行摘要", "预算概览", "战略与市场验证", "风险与缺口", "运营与行动计划", "@media print", "<details>"):
            self.assertIn(marker, output)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", output)

    def test_plan_validation_boundaries(self):
        with self.assertRaises(ValueError): BusinessPlan("").validate()
        with self.assertRaises(ValueError): BusinessPlan("x", evidence=[{"text": "missing source"}]).validate()
        for kwargs in ({"price": 10, "units": 1, "variable_cost": 4, "fixed_cost": 1, "currency": "", "period": "month"}, {"price": 10, "units": 1, "variable_cost": 4, "fixed_cost": 1, "currency": "USD", "period": ""}, {"price": 3, "units": 1, "variable_cost": 4, "fixed_cost": 1}, {"price": 10, "units": 1, "variable_cost": -1, "fixed_cost": 1}):
            with self.assertRaises(ValueError): calculate_budget(**kwargs)


if __name__ == "__main__": unittest.main()
