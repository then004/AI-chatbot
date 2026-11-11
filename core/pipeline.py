"""Structured local planning pipeline."""
import json, os, urllib.request
from pathlib import Path
from uuid import uuid4
from .retrieval import RetrievalService
from .orchestrator import compose_plan
from .html_renderer import render_business_plan

class PipelineError(RuntimeError): pass

def _ollama_json(prompt, model, url):
    body = json.dumps({'model': model, 'stream': False, 'format': 'json', 'messages': [{'role': 'user', 'content': prompt}]}).encode()
    req = urllib.request.Request(url.rstrip('/') + '/api/chat', body, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(json.loads(response.read().decode())['message']['content'])

def run_pipeline(idea, budget_inputs=None, db_path=None, output_root=None, model=None, ollama_url=None):
    if not idea or not idea.strip(): raise PipelineError('business idea is required')
    db = db_path or Path(__file__).resolve().parents[1] / 'RAG_bot' / 'law_db' / 'chroma.sqlite3'
    query = f"{idea.strip()} startup business market customers costs"
    evidence = RetrievalService(db, top_k=3).search(query)
    model = model or os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')
    url = ollama_url or os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    language = 'Chinese' if any('\u4e00' <= ch <= '\u9fff' for ch in idea) else 'the same language as the idea'
    evidence_note = json.dumps(evidence, ensure_ascii=False) if evidence else '[] (No relevant evidence found; state this clearly in gaps and do not make evidence-backed claims.)'
    prompt = (f'Return JSON only with keys assumptions, recommendations, gaps. Write in {language}. Do not include HTML, calculations, sources, or invented citations. '
              'If evidence is empty, put a clear evidence gap in gaps. Idea: ' + idea + '\nEvidence: ' + evidence_note)
    try: generated = _ollama_json(prompt, model, url)
    except Exception as first:
        try: generated = _ollama_json(prompt + '\nReturn a minimal valid JSON object now.', model, url)
        except Exception as second: raise PipelineError(f'Ollama JSON failed after one repair attempt: {second}') from first
    if not isinstance(generated, dict): raise PipelineError('Ollama JSON must be an object')
    budget = {}
    if budget_inputs:
        from .budget import calculate_budget
        budget = calculate_budget(**budget_inputs)
        if budget_inputs.get('fixed_cost', 0) <= 0 or budget_inputs.get('units', 0) <= 0:
            budget['budget_status'] = '待核实：固定成本或销量未充分提供'
    elif not evidence:
        generated.setdefault('gaps', []).append('No relevant evidence was found for this idea; conclusions are preliminary assumptions and require validation. 未找到与该创业想法直接相关的证据。')
    plan = compose_plan(idea, {'idea': idea}, evidence, generated.get('assumptions', []), budget, generated.get('recommendations', []), generated.get('gaps', []))
    run_id = 'm3-' + uuid4().hex[:12]
    out = Path(output_root or Path(__file__).resolve().parents[1] / 'docs' / 'reports' / 'artifacts') / run_id
    out.mkdir(parents=True, exist_ok=False)
    data = dict(plan.__dict__, retrieval_mode=(evidence[0].get('retrieval_mode') if evidence else 'no_relevant_evidence'), model=model)
    (out / 'Business_Plan.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'Business_Plan.html').write_text(render_business_plan(plan), encoding='utf-8')
    return {'run_id': run_id, 'output_dir': str(out), 'data': data}
