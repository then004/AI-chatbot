import json, sqlite3, uuid, re, os, urllib.request
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
try: from .reddit_service import reddit_configured, praw_adapter, run_research, collect_posts, analyze_local
except ImportError: from reddit_service import reddit_configured, praw_adapter, run_research, collect_posts, analyze_local

ROOT=Path(__file__).resolve().parents[2]; DB=ROOT/'web'/'workspace.sqlite3'
app=FastAPI(title='AI Chatbot Workspace')
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.executescript('CREATE TABLE IF NOT EXISTS projects(project_id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS memory_candidates(id TEXT PRIMARY KEY,project_id TEXT,content TEXT,status TEXT DEFAULT "candidate",source_message_id TEXT); CREATE TABLE IF NOT EXISTS project_messages(id TEXT PRIMARY KEY,project_id TEXT,role TEXT,content TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS report_versions(id TEXT PRIMARY KEY,project_id TEXT,content_json TEXT,html TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY,project_id TEXT,filename TEXT,stored_path TEXT,status TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS upload_segments(id INTEGER PRIMARY KEY AUTOINCREMENT,upload_id TEXT,project_id TEXT,segment INTEGER,page INTEGER,text TEXT); CREATE TABLE IF NOT EXISTS public_documents(id TEXT PRIMARY KEY,filename TEXT NOT NULL,stored_path TEXT NOT NULL,sha256 TEXT UNIQUE,status TEXT,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS public_segments(id INTEGER PRIMARY KEY AUTOINCREMENT,document_id TEXT,segment INTEGER,page INTEGER,text TEXT); CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,project_id TEXT,type TEXT,status TEXT,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);')
    return c
def require_project(c, pid):
    if c.execute('select 1 from projects where project_id=?',(pid,)).fetchone() is None:
        c.close(); raise HTTPException(404, 'project not found')
def run_reddit_task(pid,tid,runid,proposal):
    c=db(); c.execute("update tasks set status='running',updated_at=CURRENT_TIMESTAMP where id=?",(tid,)); c.execute("update research_runs set status='running' where id=?",(runid,)); c.commit()
    try:
        posts=collect_posts(proposal['query'],json.loads(proposal['subreddits']),proposal['limit_n'],adapter=None)
        def ollama(prompt):
            body=json.dumps({'model':os.getenv('OLLAMA_MODEL','qwen2.5:3b'),'stream':False,'format':'json','messages':[{'role':'user','content':prompt}]}).encode(); req=urllib.request.Request(os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434')+'/api/chat',body,{'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=180) as r: return json.loads(json.loads(r.read().decode())['message']['content'])
        result=analyze_local(posts,ollama)
        for p in posts: c.execute('insert into research_sources values(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),pid,runid,p['title'],p['subreddit'],p['permalink'],p['created'],p['text']))
        c.execute('update research_runs set status="succeeded",report_json=? where id=?',(json.dumps(result),runid)); c.execute("update tasks set status='succeeded',updated_at=CURRENT_TIMESTAMP where id=?",(tid,)); c.commit()
    except Exception as exc:
        c.execute('update research_runs set status="failed",error=? where id=?',(str(exc),runid)); c.execute('update tasks set status="failed",error=?,updated_at=CURRENT_TIMESTAMP where id=?',(str(exc),tid)); c.commit()
    finally: c.close()
class ProjectIn(BaseModel): name:str
class MemoryIn(BaseModel): content:str
class ReportIn(BaseModel): content_json:dict; html:str
class ProposalIn(BaseModel): idea:str; query:str; subreddits:list[str]=[]; mode:str='fast'; limit:int=10
class ChatIn(BaseModel): content:str
class PlanIn(BaseModel): idea:str; price:float|None=None; units:float|None=None; variable_cost:float|None=None; fixed_cost:float|None=None
UPLOAD_ROOT=ROOT/'web'/'uploads'; MAX_UPLOAD=10*1024*1024
def extract_file(path,suffix):
    if suffix=='.txt': return [(None,i+1,x) for i,x in enumerate(path.read_text(encoding='utf-8',errors='replace').splitlines()) if x.strip()]
    if suffix=='.pdf':
        from pypdf import PdfReader
        return [(i+1,i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(str(path)).pages)]
    if suffix=='.docx':
        from docx import Document
        return [(None,i+1,p.text) for i,p in enumerate(Document(str(path)).paragraphs) if p.text.strip()]
    raise ValueError('only .pdf, .docx and .txt are supported')
def run_index(task_id,upload_id,pid,path):
    c=db(); c.execute("update tasks set status='running',updated_at=CURRENT_TIMESTAMP where id=? and status='queued'",(task_id,)); c.commit()
    try:
        rows=extract_file(Path(path),Path(path).suffix.lower()); c.executemany('insert into upload_segments(upload_id,project_id,segment,page,text) values(?,?,?,?,?)',[(upload_id,pid,i,p,t) for p,i,t in rows]); c.execute("update uploads set status='indexed' where id=?",(upload_id,)); c.execute("update tasks set status='succeeded',updated_at=CURRENT_TIMESTAMP where id=?",(task_id,)); c.commit()
    except Exception as exc:
        c.execute("update uploads set status='failed',error=? where id=?",(str(exc),upload_id)); c.execute("update tasks set status='failed',error=?,updated_at=CURRENT_TIMESTAMP where id=?",(str(exc),task_id)); c.commit()
    finally: c.close()
@app.get('/api/projects')
def projects():
    c=db(); rows=[dict(x) for x in c.execute('select * from projects order by created_at desc')]; c.close(); return rows
@app.post('/api/projects')
def create_project(body:ProjectIn):
    pid=str(uuid.uuid4()); c=db(); c.execute('insert into projects(project_id,name) values(?,?)',(pid,body.name)); c.commit(); c.close(); return {'project_id':pid,'name':body.name}
@app.get('/api/projects/{pid}/memory')
def memories(pid):
    c=db(); require_project(c,pid); rows=[dict(x) for x in c.execute('select * from memory_candidates where project_id=? order by rowid desc',(pid,))]; c.close(); return rows
@app.post('/api/projects/{pid}/memory')
def add_memory(pid,body:MemoryIn):
    mid=str(uuid.uuid4()); c=db(); require_project(c,pid); c.execute('insert into memory_candidates(id,project_id,content) values(?,?,?)',(mid,pid,body.content)); c.commit(); c.close(); return {'id':mid,'status':'candidate','content':body.content}
@app.post('/api/projects/{pid}/memory/{mid}/{status}')
def update_memory(pid,mid,status):
    if status not in ('confirmed','ignored'): raise HTTPException(400,'status must be confirmed or ignored')
    c=db(); require_project(c,pid); cur=c.execute('update memory_candidates set status=? where id=? and project_id=?',(status,mid,pid)); c.commit(); c.close()
    if cur.rowcount==0: raise HTTPException(404,'memory not found')
    return {'id':mid,'status':status}
@app.get('/api/projects/{pid}/reports')
def reports(pid):
    c=db(); require_project(c,pid); rows=[dict(x) for x in c.execute('select id,project_id,created_at from report_versions where project_id=? order by created_at desc',(pid,))]; c.close(); return rows
@app.get('/api/projects/{pid}/reports/{rid}')
def report(pid,rid):
    c=db(); require_project(c,pid); row=c.execute('select * from report_versions where id=? and project_id=?',(rid,pid)).fetchone(); c.close()
    if row is None: raise HTTPException(404,'report not found')
    data=dict(row); data['content_json']=json.loads(data['content_json']); return data
@app.post('/api/projects/{pid}/reports')
def save_report(pid,body:ReportIn):
    rid=str(uuid.uuid4()); c=db(); require_project(c,pid); c.execute('insert into report_versions(id,project_id,content_json,html) values(?,?,?,?)',(rid,pid,json.dumps(body.content_json),body.html)); c.commit(); c.close(); return {'id':rid}
@app.get('/api/health')
def health(): return {'ok':True,'mode':'local'}
@app.get('/api/knowledge/public')
def public_knowledge():
    c=db(); rows=[dict(x) for x in c.execute('select id,filename,status,error from public_documents order by filename')]; count=c.execute('select count(*) from public_segments').fetchone()[0]; c.close(); return {'documents':rows,'document_count':len(rows),'segment_count':count,'scope':'public','read_only':True}
def run_plan_task(pid,tid,runid,body):
    c=db(); c.execute("update tasks set status='running',updated_at=CURRENT_TIMESTAMP where id=?",(tid,)); c.commit()
    try:
        from core.pipeline import run_pipeline
        b=None
        if all(x is not None for x in (body['price'],body['units'],body['variable_cost'],body['fixed_cost'])): b={'price':body['price'],'units':body['units'],'variable_cost':body['variable_cost'],'fixed_cost':body['fixed_cost']}
        result=run_pipeline(body['idea'],b); out=Path(result['output_dir']); html=(out/'Business_Plan.html').read_text(encoding='utf-8'); data=result['data']; c.execute('insert into report_versions(id,project_id,content_json,html) values(?,?,?,?)',(runid,pid,json.dumps(data),html)); c.execute("update tasks set status='succeeded',updated_at=CURRENT_TIMESTAMP where id=?",(tid,)); c.commit()
    except Exception as exc: c.execute("update tasks set status='failed',error=?,updated_at=CURRENT_TIMESTAMP where id=?",(str(exc),tid)); c.commit()
    finally: c.close()
@app.post('/api/projects/{pid}/plans')
def create_plan(pid,body:PlanIn,background_tasks:BackgroundTasks):
    if len(body.idea.strip())<5: raise HTTPException(422,'idea must be at least 5 characters and include the business idea or target user')
    c=db(); require_project(c,pid); tid=str(uuid.uuid4()); c.execute('insert into tasks(id,project_id,type,status) values(?,?,?,?)',(tid,pid,'business_plan','queued')); c.commit(); c.close(); background_tasks.add_task(run_plan_task,pid,tid,str(uuid.uuid4()),body.model_dump()); return {'task_id':tid,'status':'queued'}
def ollama_chat(messages):
    body=json.dumps({'model':os.getenv('OLLAMA_MODEL','qwen2.5:3b'),'stream':False,'messages':messages}).encode(); req=urllib.request.Request(os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434')+'/api/chat',body,{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r: return json.loads(r.read().decode())['message']['content']
@app.get('/api/projects/{pid}/messages')
def messages(pid):
    c=db(); require_project(c,pid); rows=[dict(x) for x in c.execute('select * from project_messages where project_id=? order by created_at',(pid,))]; c.close(); return rows
@app.post('/api/projects/{pid}/messages')
def chat(pid,body:ChatIn):
    c=db(); require_project(c,pid); mid=str(uuid.uuid4()); c.execute('insert into project_messages(id,project_id,role,content) values(?,?,?,?)',(mid,pid,'user',body.content)); memories=[x[0] for x in c.execute("select content from memory_candidates where project_id=? and status='confirmed' limit 20",(pid,))]; history=[{'role':x['role'],'content':x['content']} for x in c.execute('select role,content from project_messages where project_id=? order by created_at desc limit 12',(pid,))][::-1]; c.commit(); c.close(); prompt={'role':'system','content':'You are a local startup research assistant. Confirmed project memories may be used as context; candidate or ignored memories are not facts. Confirmed memories: '+json.dumps(memories,ensure_ascii=False)}
    try: answer=ollama_chat([prompt]+history)
    except Exception as exc: raise HTTPException(503,f'Local Ollama unavailable: {exc}')
    c=db(); aid=str(uuid.uuid4()); c.execute('insert into project_messages(id,project_id,role,content) values(?,?,?,?)',(aid,pid,'assistant',answer)); c.commit(); c.close(); return {'message_id':aid,'role':'assistant','content':answer,'candidate_memories':[]}
@app.post('/api/projects/{pid}/research/proposals')
def create_proposal(pid,body:ProposalIn):
    c=db(); require_project(c,pid); rid=str(uuid.uuid4()); c.execute('create table if not exists research_proposals(id text primary key,project_id text,idea text,query text,subreddits text,mode text,limit_n integer,status text)'); c.execute('insert into research_proposals values(?,?,?,?,?,?,?,?)',(rid,pid,body.idea,body.query,json.dumps(body.subreddits),body.mode,body.limit,'draft')); c.commit(); c.close(); return {'id':rid,'status':'draft','reddit_configured':reddit_configured()}
@app.post('/api/projects/{pid}/research/proposals/{rid}/confirm')
def confirm_proposal(pid,rid,background_tasks:BackgroundTasks):
    c=db(); require_project(c,pid); row=c.execute('select 1 from research_proposals where id=? and project_id=?',(rid,pid)).fetchone()
    if row is None: c.close(); raise HTTPException(404,'proposal not found')
    if not reddit_configured(): c.execute("update research_proposals set status='blocked' where id=?",(rid,)); c.commit(); c.close(); return {'id':rid,'status':'blocked','reason':'Reddit credentials are not configured; no request was sent.'}
    tid=str(uuid.uuid4()); c.execute('create table if not exists research_runs(id text primary key,proposal_id text,project_id text,task_id text,status text,error text,report_json text)'); c.execute('create table if not exists research_sources(id text primary key,project_id text,run_id text,title text,subreddit text,permalink text,created real,text text)'); c.execute('insert into tasks(id,project_id,type,status) values(?,?,?,?)',(tid,pid,'reddit_research','queued')); runid=str(uuid.uuid4()); c.execute('insert into research_runs(id,proposal_id,project_id,task_id,status) values(?,?,?,?,?)',(runid,rid,pid,tid,'queued')); c.execute("update research_proposals set status='confirmed' where id=?",(rid,)); proposal_row=dict(c.execute('select * from research_proposals where id=?',(rid,)).fetchone()); c.commit(); c.close(); background_tasks.add_task(run_reddit_task,pid,tid,runid,proposal_row); return {'id':rid,'task_id':tid,'run_id':runid,'status':'queued'}
@app.get('/api/projects/{pid}/research')
def research(pid):
    c=db(); require_project(c,pid); c.execute('create table if not exists research_proposals(id text primary key,project_id text,idea text,query text,subreddits text,mode text,limit_n integer,status text)'); rows=[dict(x) for x in c.execute('select * from research_proposals where project_id=?',(pid,))]; c.close(); return rows
@app.get('/api/projects/{pid}/research/runs/{runid}')
def research_run(pid,runid):
    c=db(); require_project(c,pid); c.execute('create table if not exists research_runs(id text primary key,proposal_id text,project_id text,task_id text,status text,error text,report_json text)'); c.execute('create table if not exists research_sources(id text primary key,project_id text,run_id text,title text,subreddit text,permalink text,created real,text text)'); row=c.execute('select * from research_runs where id=? and project_id=?',(runid,pid)).fetchone(); sources=[dict(x) for x in c.execute('select title,subreddit,permalink,created,text from research_sources where run_id=?',(runid,))]; c.close()
    if row is None: raise HTTPException(404,'run not found')
    d=dict(row); d['report_json']=json.loads(d['report_json']) if d['report_json'] else None; d['sources']=sources; return d
@app.post('/api/projects/{pid}/uploads')
async def upload(pid, background_tasks:BackgroundTasks, file:UploadFile=File(...)):
    c=db(); require_project(c,pid); suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.docx','.txt'): c.close(); raise HTTPException(400,'only PDF, DOCX and TXT are supported')
    data=await file.read()
    if len(data)>MAX_UPLOAD: c.close(); raise HTTPException(413,'file exceeds 10 MB limit')
    uid=str(uuid.uuid4()); folder=UPLOAD_ROOT/pid; folder.mkdir(parents=True,exist_ok=True); safe=re.sub(r'[^A-Za-z0-9_.-]','_',Path(file.filename).name); path=folder/(uid+'_'+safe); path.write_bytes(data)
    tid=str(uuid.uuid4()); c.execute('insert into uploads(id,project_id,filename,stored_path,status) values(?,?,?,?,?)',(uid,pid,file.filename,str(path),'queued')); c.execute('insert into tasks(id,project_id,type,status) values(?,?,?,?)',(tid,pid,'index_upload','queued')); c.commit(); c.close(); background_tasks.add_task(run_index,tid,uid,pid,path); return {'upload_id':uid,'task_id':tid,'status':'queued'}
@app.get('/api/projects/{pid}/uploads')
def uploads(pid):
    c=db(); require_project(c,pid); rows=[dict(x) for x in c.execute('select id,filename,status,error,created_at from uploads where project_id=? order by created_at desc',(pid,))]; c.close(); return rows
@app.get('/api/projects/{pid}/search')
def search(pid,q:str):
    c=db(); require_project(c,pid); like='%'+q+'%'; rows=[{'source':x['filename'],'page':x['page'],'segment':x['segment'],'excerpt':x['text'],'scope':'project'} for x in c.execute('select u.filename,s.page,s.segment,s.text from upload_segments s join uploads u on u.id=s.upload_id where s.project_id=? and lower(s.text) like lower(?) limit 20',(pid,like))]; rows += [{'source':x['filename'],'page':x['page'],'segment':x['segment'],'excerpt':x['text'],'scope':'public'} for x in c.execute('select d.filename,s.page,s.segment,s.text from public_segments s join public_documents d on d.id=s.document_id where d.status="indexed" and lower(s.text) like lower(?) limit 20',(like,))]; c.close(); return rows[:40]
@app.get('/api/projects/{pid}/tasks')
def tasks(pid):
    c=db(); require_project(c,pid); rows=[dict(x) for x in c.execute('select * from tasks where project_id=? order by created_at desc',(pid,))]; c.close(); return rows
@app.post('/api/projects/{pid}/tasks/{tid}/cancel')
def cancel_task(pid,tid):
    c=db(); require_project(c,pid); cur=c.execute("update tasks set status='cancelled',updated_at=CURRENT_TIMESTAMP where id=? and project_id=? and status='queued'",(tid,pid)); c.commit(); c.close()
    if not cur.rowcount: raise HTTPException(409,'task already started or not found')
    return {'id':tid,'status':'cancelled'}
