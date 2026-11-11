import argparse, json, tempfile, sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.budget import calculate_budget
from core.business_plan import BusinessPlan
from core.html_renderer import render_business_plan
from core.retrieval import RetrievalService
from core.agent import run_agent
from core.storage import Storage

parser=argparse.ArgumentParser(); parser.add_argument('--output-dir'); args=parser.parse_args()
base=Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix='final-smoke-'))
base.mkdir(parents=True, exist_ok=True); out=base/('smoke-'+uuid4().hex[:10]); out.mkdir()
html=render_business_plan(BusinessPlan('<smoke>',evidence=[{'source':'s','text':'<script>'}]))
Storage(out/'state.sqlite3').close()
seq=iter([{'action':'search_knowledge','params':{'query':'x'}},{'action':'calculate_budget','params':{'price':10,'units':2,'variable_cost':2,'fixed_cost':1}},{'action':'finish_report','params':{}}])
agent=run_agent(lambda c:next(seq),'x',type('R',(),{'search':lambda s,q:[{'evidence_id':'e','source':'s','page':1}]})())
result={'run_id':'smoke-'+uuid4().hex[:10],'checks':{'budget':calculate_budget(price=10,units=2,variable_cost=2,fixed_cost=1)['profit']==15,'html_escaped':'<script>' not in html,'agent_mock_success':agent.status=='succeeded','storage_db':(out/'state.sqlite3').exists()},'cannot_verify':['production vector RAG in copied .venv','browser acceptance','real async worker']}
artifact=out/'smoke.json'; artifact.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps({'artifact':str(artifact),**result}))
