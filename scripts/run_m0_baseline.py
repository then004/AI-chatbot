"""M0 fallback RAG probe; retrieval_mode=sqlite_fts_fallback.

Reads the existing Chroma SQLite FTS index read-only, then sends retrieved
chunks to the local Ollama API. It does not modify the vector database.
"""
import argparse, datetime as dt, json, re, sqlite3, time, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "RAG_bot" / "law_db" / "chroma.sqlite3"
OUT = ROOT / "docs" / "reports" / "artifacts"

def retrieve(query, top_k):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = con.execute("""
          SELECT f.rowid, bm25(embedding_fulltext_search), f.string_value,
                 source.string_value, page.int_value
          FROM embedding_fulltext_search f
          LEFT JOIN embedding_metadata source ON source.id=f.rowid AND source.key='source'
          LEFT JOIN embedding_metadata page ON page.id=f.rowid AND page.key='page'
          WHERE embedding_fulltext_search MATCH ? ORDER BY bm25(embedding_fulltext_search) LIMIT ?
        """, (query, top_k)).fetchall()
    finally:
        con.close()
    return [{"evidence_id": f"m0-fts-{r[0]}", "chunk_id": r[0], "score": r[1],
             "text": r[2], "source": r[3], "page": r[4]} for r in rows]

def ollama(question, evidence, model, url):
    context = "\n\n".join(f"[{x['evidence_id']}] {x['source']} page {x['page']}\n{x['text']}" for x in evidence)
    prompt = ("Answer only from the retrieved context. If insufficient, say so. Cite evidence IDs.\n\n"
              f"Question: {question}\n\nContext:\n{context}")
    body = json.dumps({"model": model, "stream": False, "options": {"temperature": 0},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(url.rstrip('/') + '/api/chat', body,
                                 {"Content-Type": "application/json"})
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as response:
        data = json.loads(response.read().decode())
    return data, round((time.perf_counter() - started) * 1000, 2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--question', required=True)
    ap.add_argument('--fts-query', required=True)
    ap.add_argument('--top-k', type=int, default=3)
    ap.add_argument('--model', default='qwen2.5:3b')
    ap.add_argument('--ollama-url', default='http://127.0.0.1:11434')
    args = ap.parse_args()
    run_id = f"m0-fts-{dt.datetime.now():%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"
    run_dir = OUT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    result = {"run_id": run_id, "retrieval_mode": "sqlite_fts_fallback",
              "question": args.question, "fts_query": args.fts_query,
              "model": args.model, "status": "failed"}
    started = time.perf_counter()
    try:
        evidence = retrieve(args.fts_query, args.top_k)
        result["evidence"] = evidence
        if not evidence:
            result["error"] = "No FTS matches"; code = 2
        else:
            answer, model_ms = ollama(args.question, evidence, args.model, args.ollama_url)
            result["answer"] = answer.get("message", {}).get("content", "")
            result["model_elapsed_ms"] = model_ms
            result["status"] = "succeeded"; code = 0
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"; code = 1
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    result["exit_code"] = code
    output = run_dir / "result.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(output)
    return code

if __name__ == '__main__':
    raise SystemExit(main())
