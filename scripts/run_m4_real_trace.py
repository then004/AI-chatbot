import json, os, sys, time
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.agent import run_agent
from core.ollama_planner import ollama_planner

run_id='m4-real-'+uuid4().hex[:12]; model=os.getenv('OLLAMA_MODEL','qwen2.5:3b'); started=time.time(); trace_path=Path(__file__).resolve().parents[1]/'docs/reports/artifacts'/run_id; trace_path.mkdir(parents=True,exist_ok=False)
retriever=type('R',(),{'search':lambda s,q:[{'evidence_id':'ev-real-demo','source':'demo.pdf','page':1,'text':'redacted','retrieval_mode':'sqlite_fts_fallback'}]})()
try:
    result=run_agent(lambda state: ollama_planner(state,model=model), 'AI legal consultation platform', retriever, max_steps=8)
    payload={'run_id':run_id,'model':model,'timeout_seconds':120,'status':result.status,'fallback':result.fallback,'stop_reason':result.stop_reason,'trace':result.trace,'elapsed_ms':(time.time()-started)*1000,'real_ollama':True}
except Exception as exc:
    payload={'run_id':run_id,'model':model,'timeout_seconds':120,'status':'blocked','fallback':False,'stop_reason':type(exc).__name__,'error':str(exc),'trace':[],'elapsed_ms':(time.time()-started)*1000,'real_ollama':True}
(trace_path/'trace.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(payload,ensure_ascii=False))
