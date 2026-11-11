import argparse, json, sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.retrieval import RetrievalService

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir')
parser.add_argument('--update-fixtures', action='store_true')
args = parser.parse_args()
db = root / 'RAG_bot' / 'law_db' / 'chroma.sqlite3'
service = RetrievalService(db, top_k=2)
queries = [
 ('business plan', 'What does the corpus say about writing a business plan?', 'supported'),
 ('patent', 'What does the corpus say about patents?', 'supported'),
 ('trademark', 'What does the corpus say about trademarks?', 'supported'),
 ('copyright', 'What does the corpus say about copyright?', 'supported'),
 ('business plan', '中文：商业计划为什么重要？', 'supported'),
 ('nonexistentzz', 'What does the corpus say about quantum teleportation?', 'no_evidence'),
]
scenarios = []
for fts, question, status in queries:
    evidence = service.search(fts)
    scenarios.append({'question': question, 'fts_query': fts, 'ground_truth': status, 'retrieval_mode': 'sqlite_fts_fallback', 'evidence': evidence})
samples = []
for i, item in enumerate(scenarios[:5] + scenarios[:5] + scenarios[:2], 1):
    ev = item['evidence'][0] if item['evidence'] else {}
    samples.append({'sample_id': f'm2-{i:02d}', 'question': item['question'], 'ground_truth': item['ground_truth'], 'retrieval_mode': item['retrieval_mode'], 'source': ev.get('source'), 'page': ev.get('page'), 'text': ev.get('text')})
if args.update_fixtures:
    output = root / 'docs' / 'eval'
else:
    output = Path(args.output_dir) if args.output_dir else root / 'docs' / 'reports' / 'artifacts' / ('m2-' + uuid4().hex[:12])
output.mkdir(parents=True, exist_ok=False)
(output / 'm2_samples.json').write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding='utf-8')
(output / 'm2_scenarios.json').write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'scenario_count': len(scenarios), 'sample_count': len(samples), 'supported': sum(bool(x['evidence']) for x in scenarios), 'output_dir': str(output), 'fixtures_updated': args.update_fixtures}, ensure_ascii=False))
