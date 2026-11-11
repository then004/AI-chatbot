import os, tempfile, unittest
from fastapi.testclient import TestClient
from main import app
import main
from unittest.mock import patch
class ApiTests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.NamedTemporaryFile(suffix='.sqlite3',delete=False); self.tmp.close(); self.old=main.DB; main.DB=self.tmp.name; self.c=TestClient(app)
 def tearDown(self): main.DB=self.old; os.unlink(self.tmp.name)
 def test_project_memory_reports_isolation(self):
  self.assertEqual(self.c.get('/api/projects/nope/memory').status_code,404); p=self.c.post('/api/projects',json={'name':'P'}).json(); pid=p['project_id']; m=self.c.post(f'/api/projects/{pid}/memory',json={'content':'idea'}).json(); self.assertEqual(self.c.post(f'/api/projects/{pid}/memory/{m["id"]}/confirmed').json()['status'],'confirmed'); self.c.post(f'/api/projects/{pid}/memory/{m["id"]}/ignored'); self.assertEqual(len(self.c.get(f'/api/projects/{pid}/memory').json()),1); r1=self.c.post(f'/api/projects/{pid}/reports',json={'content_json':{'v':1},'html':'<h1>1</h1>'}).json(); r2=self.c.post(f'/api/projects/{pid}/reports',json={'content_json':{'v':2},'html':'<h1>2</h1>'}).json(); self.assertEqual(len(self.c.get(f'/api/projects/{pid}/reports').json()),2); self.assertEqual(self.c.get(f'/api/projects/{pid}/reports/{r1["id"]}').json()['content_json']['v'],1); self.assertEqual(self.c.get(f'/api/projects/{pid}/reports/{r2["id"]}').status_code,200)
 def test_txt_upload_search_and_bad_format(self):
  pid=self.c.post('/api/projects',json={'name':'Docs'}).json()['project_id']; self.assertEqual(self.c.post('/api/projects/bad/uploads',files={'file':('x.txt',b'x','text/plain')}).status_code,404); response=self.c.post(f'/api/projects/{pid}/uploads',files={'file':('notes.txt',b'Hong Kong company registration\nmarket research','text/plain')}); self.assertEqual(response.status_code,200); self.assertEqual(self.c.get(f'/api/projects/{pid}/search',params={'q':'Hong Kong'}).json()[0]['scope'],'project'); self.assertTrue(self.c.get(f'/api/projects/{pid}/tasks').json()); self.assertEqual(self.c.post(f'/api/projects/{pid}/uploads',files={'file':('x.exe',b'x','application/octet-stream')}).status_code,400)
 def test_chat_persists_and_failure_is_explicit(self):
  pid=self.c.post('/api/projects',json={'name':'Chat'}).json()['project_id']; self.c.post(f'/api/projects/{pid}/memory',json={'content':'candidate'}); c=main.db(); c.execute("update memory_candidates set status='confirmed'"); c.commit(); c.close()
  with patch('main.ollama_chat',return_value='local answer'):
   r=self.c.post(f'/api/projects/{pid}/messages',json={'content':'hello'}); self.assertEqual(r.status_code,200); self.assertEqual(len(self.c.get(f'/api/projects/{pid}/messages').json()),2)
  with patch('main.ollama_chat',side_effect=RuntimeError('offline')):
   self.assertEqual(self.c.post(f'/api/projects/{pid}/messages',json={'content':'again'}).status_code,503)
 def test_plan_rejects_short_idea(self):
  pid=self.c.post('/api/projects',json={'name':'Plan'}).json()['project_id']; self.assertEqual(self.c.post(f'/api/projects/{pid}/plans',json={'idea':'1'}).status_code,422)
 def test_public_knowledge_is_read_only_and_available_to_all_projects(self):
  p1=self.c.post('/api/projects',json={'name':'One'}).json()['project_id']; p2=self.c.post('/api/projects',json={'name':'Two'}).json()['project_id']; c=main.db(); c.execute("insert into public_documents values(?,?,?,?,?,NULL,CURRENT_TIMESTAMP)",('pub-1','guide.pdf','readonly','hash-1','indexed')); c.execute("insert into public_segments(document_id,segment,page,text) values(?,?,?,?)",('pub-1',1,1,'coffee shop market')); c.commit(); c.close()
  for pid in (p1,p2): self.assertEqual(self.c.get(f'/api/projects/{pid}/search',params={'q':'coffee'}).json()[0]['scope'],'public')
  info=self.c.get('/api/knowledge/public').json(); self.assertEqual(info['document_count'],1); self.assertTrue(info['read_only']); self.assertEqual(self.c.delete('/api/knowledge/public').status_code,405)
if __name__=='__main__': unittest.main()
