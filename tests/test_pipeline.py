import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from core.pipeline import run_pipeline, PipelineError

EVIDENCE = [{'evidence_id': 'ev-1', 'source': 'x.pdf', 'page': 1, 'text': 'business plan', 'retrieval_mode': 'sqlite_fts_fallback'}]
def temp_dir(): return tempfile.TemporaryDirectory(dir=os.getenv('AI_CHATBOT_TEST_TMPDIR') or None)

class PipelineTests(unittest.TestCase):
    def test_invalid_json_repairs_once_and_leaves_no_report(self):
        calls = []
        def fake(*a, **k): calls.append(1); raise ValueError('bad json')
        d = temp_dir()
        with patch('core.pipeline.RetrievalService.search', return_value=EVIDENCE), patch('core.pipeline._ollama_json', side_effect=fake):
            with self.assertRaises(PipelineError): run_pipeline('idea', output_root=d.name)
            self.assertEqual(len(calls), 2); self.assertEqual(list(Path(d.name).iterdir()), [])
        d.cleanup()

    def test_non_object_and_no_evidence(self):
        d = temp_dir()
        with patch('core.pipeline.RetrievalService.search', return_value=EVIDENCE), patch('core.pipeline._ollama_json', return_value=['wrong']):
            with self.assertRaises(PipelineError): run_pipeline('idea', output_root=d.name)
            self.assertEqual(list(Path(d.name).iterdir()), [])
        d.cleanup()
        d = temp_dir()
        with patch('core.pipeline.RetrievalService.search', return_value=[]), patch('core.pipeline._ollama_json', return_value={'assumptions': [], 'recommendations': [], 'gaps': []}):
            result = run_pipeline('idea', output_root=d.name)
            self.assertTrue(any('No relevant evidence was found' in gap for gap in result['data']['gaps']))
        d.cleanup()

    def test_query_and_language_follow_idea(self):
        d = temp_dir(); calls=[]
        def model(prompt,*args,**kwargs): calls.append(prompt); return {'assumptions': [], 'recommendations': [], 'gaps': []}
        with patch('core.pipeline.RetrievalService.search', return_value=EVIDENCE) as search, patch('core.pipeline._ollama_json', side_effect=model):
            run_pipeline('创立咖啡店', output_root=d.name)
        self.assertIn('创立咖啡店', search.call_args.args[0]); self.assertIn('Chinese', calls[0]); d.cleanup()

    def test_isolation_and_budget_not_model(self):
        d = temp_dir()
        with patch('core.pipeline.RetrievalService.search', return_value=EVIDENCE), patch('core.pipeline._ollama_json', return_value={'assumptions': [], 'recommendations': [], 'gaps': [], 'calculations': {'profit': 999999}}):
            a = run_pipeline('idea', {'price': 10, 'units': 10, 'variable_cost': 2, 'fixed_cost': 20}, output_root=d.name)
            b = run_pipeline('idea', {'price': 10, 'units': 10, 'variable_cost': 2, 'fixed_cost': 20}, output_root=d.name)
            self.assertNotEqual(a['run_id'], b['run_id']); self.assertEqual(a['data']['calculations']['profit'], 60)
        d.cleanup()

if __name__ == '__main__': unittest.main()
