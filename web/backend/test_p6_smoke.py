import os,tempfile,unittest,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from unittest.mock import patch
from fastapi.testclient import TestClient
import main
class P6Smoke(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.NamedTemporaryFile(suffix='.sqlite3',delete=False);self.tmp.close();self.old=main.DB;main.DB=self.tmp.name;self.c=TestClient(main.app)
 def tearDown(self):main.DB=self.old;os.unlink(self.tmp.name)
 def test_project_chat_upload_plan_reddit_blocked(self):
  pid=self.c.post('/api/projects',json={'name':'P6'}).json()['project_id']
  with patch('main.ollama_chat',return_value='answer'): self.assertEqual(self.c.post(f'/api/projects/{pid}/messages',json={'content':'idea'}).status_code,200)
  mid=self.c.post(f'/api/projects/{pid}/memory',json={'content':'candidate'}).json()['id'];self.assertEqual(self.c.post(f'/api/projects/{pid}/memory/{mid}/confirmed').status_code,200)
  self.assertEqual(self.c.post(f'/api/projects/{pid}/uploads',files={'file':('x.txt',b'keyword text','text/plain')}).status_code,200);self.assertTrue(self.c.get(f'/api/projects/{pid}/search?q=keyword').json())
  with patch('core.pipeline.run_pipeline',return_value={'output_dir':tempfile.gettempdir(),'data':{'title':'mock'}}): self.assertEqual(self.c.post(f'/api/projects/{pid}/plans',json={'idea':'valid idea'}).status_code,200)
  prop=self.c.post(f'/api/projects/{pid}/research/proposals',json={'idea':'x','query':'x'}).json();self.assertEqual(self.c.post(f'/api/projects/{pid}/research/proposals/{prop["id"]}/confirm').json()['status'],'blocked')
if __name__=='__main__':unittest.main()
