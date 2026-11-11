"""Standalone escaped report renderer with controlled business-plan layout."""
from datetime import date
from html import escape
import json
from pathlib import Path
from typing import Any, Iterable
from .business_plan import BusinessPlan

_LABELS={'idea':'创业想法','price':'售价','units':'销量','variable_cost':'单位变动成本','fixed_cost':'固定成本','currency':'货币','period':'周期','revenue':'收入','variable_cost_total':'变动成本','total_cost':'总成本','profit':'利润','break_even_units':'盈亏平衡销量','break_even_revenue':'盈亏平衡收入'}

def _text(value:Any)->str:return escape(str(value),quote=True)
def _label(key:Any)->str:return _LABELS.get(str(key),str(key))
def _items(items:Iterable[Any],empty='暂无内容')->str:
    out=[]
    for item in items or []:
        if isinstance(item,dict):
            text=item.get('text',item.get('content',''))
            ids=item.get('supporting_evidence',[]) or []
            tags=''.join(f"<span class='tag'>{_text(x)}</span>" for x in ids)
            out.append(f"<li>{_text(text)} {tags}</li>")
        else: out.append(f"<li>{_text(item)}</li>")
    return ''.join(out) or f"<li class='muted'>{_text(empty)}</li>"

def _page(value:Any)->str:
    try:
        n=int(value); return f'PDF 第{n+1}页（索引{n}）'
    except (TypeError,ValueError): return f'PDF 第{_text(value)}页'

def _value(value:Any)->str:
    if isinstance(value,(int,float)) and not isinstance(value,bool): return f'{value:,.2f}'
    return str(value)

def render_business_plan(plan:BusinessPlan)->str:
    plan.validate()
    inputs=json.dumps(plan.user_inputs,ensure_ascii=False,indent=2,default=str)
    input_html=''.join(f"<div class='input-row'><span>{_text(_label(k))}：</span><strong>{_text(v)}</strong></div>" for k,v in plan.user_inputs.items()) or "<div class='muted'>未提供额外输入</div>"
    calc=''.join(f"<tr><th>{_text(_label(k))}</th><td>{_text(_value(v))}"+(f" { _text(plan.calculations.get('currency',''))}/{_text(plan.calculations.get('period',''))}" if k in {'revenue','variable_cost_total','fixed_cost','profit','break_even_revenue'} and plan.calculations.get('currency') else '')+"</td></tr>" for k,v in plan.calculations.items()) or "<tr><td colspan='2' class='muted'>暂无预算计算</td></tr>"
    kpi=''.join(f"<div class='kpi'><span>{label}</span><strong>{_text(_value(plan.calculations[key]))}{(' '+_text(plan.calculations.get('currency',''))+'/'+_text(plan.calculations.get('period',''))) if key!='break_even_units' and plan.calculations.get('currency') else ''}</strong></div>" for label,key in [('收入','revenue'),('总成本','total_cost'),('利润','profit'),('盈亏平衡销量（单位）','break_even_units')] if key in plan.calculations) or "<div class='muted'>暂无 KPI 数据</div>"
    evidence=''.join(f"<article class='evidence-card'><div><strong>{_text(Path(str(x.get('source',''))).name)}</strong><span class='tag'>{_page(x.get('page','?'))}</span></div><details><summary>展开原文</summary><p>{_text(x.get('text',''))}</p></details></article>" for x in plan.evidence) or "<p class='muted'>暂无相关证据；结论需要进一步验证。</p>"
    title=_text(plan.title)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
:root{{--ink:#172033;--muted:#667085;--line:#e5e7eb;--brand:#2457d6;--soft:#f4f7fc;--good:#087f5b}}*{{box-sizing:border-box}}body{{margin:0;background:#eef2f7;color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}.executive-summary{{background-color:#e3f2fd;border-left:5px solid #2196f3;padding:25px}}.strategic-plan{{background-color:#f3e5f5;border-left:5px solid #9c27b0}}.financial-plan{{background-color:#e8f5e9;border-left:5px solid #4caf50}}.operational-plan{{background-color:#fff3e0;border-left:5px solid #ff9800}}.risk-analysis{{background-color:#ffebee;border-left:5px solid #e53935}}.highlight{{background-color:#fff9c4;border-left:4px solid #fbc02d;padding:15px}}.metadata{{color:#666;border-top:2px solid #ddd;padding-top:20px}}.report{{max-width:1050px;margin:24px auto;background:#fff;box-shadow:0 16px 50px #17203318}}.cover{{padding:48px 60px;color:#fff;background:linear-gradient(135deg,#172b55,#2f67d9)}}.eyebrow{{letter-spacing:.12em;text-transform:uppercase;opacity:.78;font-size:12px}}h1{{font-size:38px;line-height:1.2;margin:12px 0 18px}}.meta{{display:flex;gap:24px;flex-wrap:wrap;opacity:.9}}.content{{padding:34px 60px}}section{{margin:0 0 28px;break-inside:avoid}}h2{{font-size:22px;margin:0 0 12px;border-bottom:2px solid var(--line);padding-bottom:8px}}.intro{{color:var(--muted)}}.input-grid{{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:14px}}.input-row{{display:flex;justify-content:space-between;gap:24px;padding:6px 0;border-bottom:1px solid var(--line)}}.input-row:last-child{{border-bottom:0}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}}.kpi{{padding:15px;border:1px solid var(--line);border-radius:12px}}.kpi span{{display:block;color:var(--muted);font-size:13px}}.kpi strong{{display:block;font-size:22px;margin-top:4px;color:var(--good)}}table{{border-collapse:collapse;width:100%}}th,td{{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left}}th{{width:42%;color:var(--muted);font-weight:500}}.evidence-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.evidence-card{{border:1px solid var(--line);border-radius:12px;padding:13px;overflow-wrap:anywhere}}.tag{{float:right;color:var(--brand);font-size:12px;background:#edf3ff;padding:2px 8px;border-radius:999px;margin-left:5px}}details{{margin-top:8px;color:var(--muted)}}summary{{cursor:pointer;color:var(--brand)}}ul,ol{{padding-left:22px}}li{{margin:6px 0}}.muted{{color:var(--muted)}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}footer{{padding:18px 60px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}@media(max-width:760px){{.cover,.content,footer{{padding:28px 20px}}h1{{font-size:30px}}.kpis,.evidence-grid{{grid-template-columns:1fr 1fr}}.input-row{{display:block}}}}@media print{{body{{background:#fff}}.report{{margin:0;box-shadow:none}}.cover{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}}}
</style></head><body><main class="container report"><header class="cover"><div class="eyebrow">Business Plan · Local AI</div><h1>{title}</h1><div class="meta"><span>生成日期：{date.today().isoformat()}</span><span>结构化商业计划报告</span></div></header><div class="content"><section class="section executive-summary"><h2>执行摘要</h2><p class="intro">预算结果由用户提供的价格、销量、成本等假设计算得出；请核实固定成本和实际经营周期，不应仅凭当前利润判断可行性。</p></section><section class="section"><h2>输入与约束</h2><div class="input-grid">{input_html}</div><details><summary>查看原始输入 JSON</summary><pre>{_text(inputs)}</pre></details></section><section class="section financial-plan"><h2>预算概览</h2><div class="kpis">{kpi}</div><table><tbody>{calc}</tbody></table></section><section class="section strategic-plan"><h2>战略与市场验证</h2><div class="evidence-grid">{evidence}</div></section><section class="section"><h2>假设</h2><ul>{_items(plan.assumptions)}</ul></section><section class="section"><h2>建议</h2><ul>{_items(plan.recommendations)}</ul></section><section class="section risk-analysis"><h2>风险与缺口</h2><ul>{_items(plan.gaps,'暂无；仍需核实')}</ul></section><section class="section operational-plan"><h2>运营与行动计划</h2><ol><li>核对预算参数与现金流周期。</li><li>验证最关键的客户和市场假设。</li><li>记录验证结果并更新下一版报告。</li></ol></section></div><footer>本报告由本地 AI 生成；模型输出以结构化数据呈现，未执行任何模型提供的 HTML 或脚本。</footer></main></body></html>'''















