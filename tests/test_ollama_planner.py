import json, unittest
from unittest.mock import patch
from core.ollama_planner import ollama_planner

class OllamaPlannerTests(unittest.TestCase):
    def test_mock_http_json_adapter(self):
        class R:
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self): return json.dumps({'message':{'content':'{"action":"ask_user","params":{}}'}}).encode()
        with patch('core.ollama_planner.urllib.request.urlopen',return_value=R()):
            self.assertEqual(json.loads(ollama_planner({'step':0}))['action'],'ask_user')

if __name__=='__main__': unittest.main()
