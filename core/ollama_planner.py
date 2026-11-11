import json, os, urllib.request

def ollama_planner(state, model=None, base_url=None, timeout=120):
    model=model or os.getenv('OLLAMA_MODEL','qwen2.5:3b'); base_url=base_url or os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434')
    prompt=('Return JSON only with exactly one action among ask_user, search_knowledge, calculate_budget, finish_report and a params object. '
            'Do not explain. Public state: '+json.dumps(state,ensure_ascii=False))
    body=json.dumps({'model':model,'stream':False,'format':'json','messages':[{'role':'user','content':prompt}]}).encode()
    req=urllib.request.Request(base_url.rstrip('/')+'/api/chat',body,{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        data=json.loads(resp.read().decode()); return data['message']['content']
