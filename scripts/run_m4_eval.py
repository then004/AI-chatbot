import argparse, json, sys, time
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.agent import run_agent

class R:
    def search(self, q): return [{'evidence_id':'ev-demo','source':'demo.pdf','page':1,'text':'redacted'}] if q else []
parser=argparse.ArgumentParser(); parser.add_argument('--output-dir'); args=parser.parse_args()
scenarios=[]
plans=[lambda c:{'action':'ask_user','params':{}}, lambda c:{'action':'search_knowledge','params':{'query':'none'}}, lambda c:{'action':'calculate_budget','params':{'price':1,'units':1,'variable_cost':2,'fixed_cost':1}}, lambda c:{'action':'bad'}, lambda c:{'action':'finish_report','params':{}}, None]
seq=iter([{'action':'search_knowledge','params':{'query':'x'}},{'action':'calculate_budget','params':{'price':10,'units':2,'variable_cost':2,'fixed_cost':1}},{'action':'finish_report','params':{}}]); plans[5]=lambda c:next(seq)
for i,p in enumerate(plans,1):
    t=time.perf_counter(); r=run_agent(p,'demo idea',R()); scenarios.append({'scenario':i,'mode':'mock_agent','status':r.status,'fallback':r.fallback,'steps':len(r.trace),'elapsed_ms':(time.perf_counter()-t)*1000,'stop_reason':r.stop_reason})
fixed=[{'status':'waiting_input','steps':1},{'status':'failed','steps':1},{'status':'failed','steps':1},{'status':'failed','steps':1},{'status':'failed','steps':1},{'status':'succeeded','steps':3}]
for item, base in zip(scenarios,fixed): item['fixed_baseline']={'status':base['status'],'steps':base['steps'],'mode':'deterministic_mock'}; item['agent_vs_fixed']='functional comparison only'
assert len(scenarios)==6 and scenarios[5]['status']=='succeeded' and scenarios[5]['steps']==3
out=Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parents[1]/'docs/reports/artifacts'/('m4-'+uuid4().hex[:12]); out.mkdir(parents=True,exist_ok=True); (out/'evaluation.json').write_text(json.dumps({'mode':'mock_agent_vs_fixed_baseline','scenarios':scenarios,'limitations':'No quality or improvement claim; fixed baseline is deterministic and not a model benchmark.'},indent=2),encoding='utf-8'); print(out)
