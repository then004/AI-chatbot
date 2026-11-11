"""Auditable constrained action loop; planner output is data, not hidden reasoning."""
import json, time
from .retrieval import RetrievalService
from .budget import calculate_budget

ACTIONS={'ask_user','search_knowledge','calculate_budget','finish_report'}

class AgentResult:
    def __init__(self, status, trace, report=None, fallback=False, stop_reason=None): self.status=status; self.trace=trace; self.report=report; self.fallback=fallback; self.stop_reason=stop_reason

def run_agent(planner, idea, retriever=None, max_steps=8):
    trace=[]; seen=set(); evidence=[]; budget={}
    for step in range(max_steps):
        started=time.time()
        try: raw=planner({'idea':idea,'evidence':evidence,'budget':budget,'step':step})
        except Exception as exc: trace.append({'step':step,'action':'planner','result':str(exc),'elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='planner_error')
        if isinstance(raw,str):
            try: raw=json.loads(raw)
            except Exception:
                trace.append({'step':step,'action':'format_repair','result':'initial JSON invalid','elapsed_ms':(time.time()-started)*1000})
                try:
                    repaired=planner({'repair':True,'step':step})
                    raw=repaired if isinstance(repaired,dict) else json.loads(repaired)
                except Exception: trace.append({'step':step,'action':'format_repair','result':'repair failed','elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='format_repair_failed')
                trace.append({'step':step,'action':'format_repair','result':'repair succeeded','elapsed_ms':(time.time()-started)*1000})
        if not isinstance(raw,dict) or raw.get('action') not in ACTIONS:
            trace.append({'step':step,'action':str(raw.get('action') if isinstance(raw,dict) else raw),'result':'invalid action','elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='invalid_action')
        action=raw['action']; params=raw.get('params',{})
        allowed={'ask_user':set(), 'finish_report':set(), 'search_knowledge':{'query'}, 'calculate_budget':{'price','units','variable_cost','fixed_cost','currency','period'}}[action]
        if not isinstance(params,dict) or set(params)-allowed or (action=='search_knowledge' and not isinstance(params.get('query'),str)) or (action=='calculate_budget' and not all(isinstance(params.get(k),(int,float)) and not isinstance(params.get(k),bool) for k in ('price','units','variable_cost','fixed_cost'))):
            trace.append({'step':step,'action':action,'params':list(params) if isinstance(params,dict) else type(params).__name__,'result':'invalid_params','elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='invalid_params')
        if action in seen and action != 'finish_report': return AgentResult('failed',trace,fallback=True,stop_reason='repeated_action')
        seen.add(action); result=''
        if action=='ask_user': result='waiting_input'; trace.append({'step':step,'action':action,'params':list(params) if isinstance(params,dict) else [],'result':result,'elapsed_ms':(time.time()-started)*1000}); return AgentResult('waiting_input',trace,fallback=False,stop_reason='ask_user')
        if action=='search_knowledge':
            if retriever is None: result='no retriever'
            else: evidence=retriever.search(params.get('query','')); result={'count':len(evidence),'evidence':[{'evidence_id':x.get('evidence_id'),'source':x.get('source'),'page':x.get('page')} for x in evidence]}
            if not evidence: trace.append({'step':step,'action':action,'params':params,'result':result,'elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='no_evidence')
        if action=='calculate_budget':
            try: budget=calculate_budget(**params); result={'revenue':budget['revenue'],'profit':budget['profit'],'break_even_units':budget['break_even_units']}
            except Exception as exc: trace.append({'step':step,'action':action,'params':list(params),'result':str(exc),'elapsed_ms':(time.time()-started)*1000}); return AgentResult('failed',trace,fallback=True,stop_reason='invalid_budget')
        trace.append({'step':step,'action':action,'params':list(params) if isinstance(params,dict) else [],'result':result or 'report requested','elapsed_ms':(time.time()-started)*1000})
        if action=='finish_report':
            if not evidence or not budget: return AgentResult('failed',trace,fallback=True,stop_reason='missing_prerequisites')
            return AgentResult('succeeded',trace,report={'idea':idea,'evidence':evidence,'budget':budget},fallback=False)
    return AgentResult('failed',trace,fallback=True,stop_reason='step_limit')
