# Implementation status

- **Stage:** M5 final acceptance
- **Task ID:** M5-FINAL-ACCEPTANCE-001
- **Status:** ready_for_review
- **Updated:** 2026-10-28T10:30:00+08:00

## Scope

Only local RAG information retrieval and local business-plan generation are in scope. Sentiment, crawling, travel and supply-chain modules are explicitly out of scope for this milestone.

## Baseline summary

- Ollama is reachable at `http://127.0.0.1:11434`; installed model: `qwen2.5:3b` (3.1B, Q4_K_M).
- A real `/api/chat` request returned `LOCAL_MODEL_OK` in 4,595 ms.
- Existing Chainlit HTTP endpoints returned 200: RAG `http://127.0.0.1:8000`, business planner `http://127.0.0.1:8001`.
- RAG corpus contains 22 PDF files in `RAG_bot/law/`; persisted Chroma data exists in `RAG_bot/law_db/`.
- Existing localised business-plan path was preserved: `StartUp_Advisor/conversation.py` calls `ChatOllama`; `startup_web.py` retains per-session locking and HTML/JSON attachments.
- The current vector RAG path was not independently executable in this sandbox: `.venv\Scripts\python.exe` fails before Python starts because its Store-Python base executable is unavailable, and the protected Store installation refused direct execution even with normal escalation.
- A separately labelled `sqlite_fts_fallback` baseline was executed against the existing Chroma SQLite database in read-only mode. It retrieved actual chunks with source/page metadata and completed three local-Ollama answers.

## Important limits

- The copied `.venv` cannot be invoked by this execution sandbox because its `pyvenv.cfg` points at a Microsoft Store Python path unavailable to the sandbox. The user has successfully run the app in their own terminal; that is recorded as manual/browser evidence, not a sandbox reproduction.
- Browser automation could not be independently reproduced because the available UI automation kernel reported a missing kernel-assets path; the user has manually confirmed successful browser execution. This does not claim performance, concurrency or production acceptance.
- Dependency-light retrieval, structured-plan, evidence-ID and SQLite-storage foundations now exist under `core/`; the production Chainlit RAG remains embedded in `RAG_bot/chainlit_app.py` and has not been migrated to those services. A 30-question semantic-vector benchmark has not been performed.

## Regression entrypoints

```powershell
# RAG (existing endpoint)
& ".\.venv\Scripts\python.exe" -m chainlit run ".\RAG_bot\chainlit_app.py" --host 127.0.0.1 --port 8000

# local business-plan assistant (existing endpoint)
& ".\.venv\Scripts\python.exe" -m chainlit run ".\StartUp_Advisor\startup_web.py" --host 127.0.0.1 --port 8001
```

Detailed evidence is in [reports/M0.md](reports/M0.md). Seed questions are in [eval/seed_questions.json](eval/seed_questions.json).

The reproducible fallback runner is [scripts/run_m0_baseline.py](../scripts/run_m0_baseline.py). It must not be interpreted as proof that the production semantic vector path passed.

## M5 final acceptance

20/20 tests pass and final smoke passes when given a writable `--output-dir`. M2 is lexical `sqlite_fts_fallback` with 12 samples, not 30-question semantic vector acceptance. The production vector path is blocked by the copied `.venv` Store-Python runtime. The user manually confirmed successful browser execution, but automation did not independently reproduce it; this is not a performance, concurrency or production acceptance claim. The real Ollama Agent trace with `qwen2.5:3b` stopped on repeated action and is marked failed/fallback. SQLite persistence is not connected to UI or a real async Worker.

## New manual evidence

The user successfully imported `chromadb` and `langchain_ollama` inside `.venv`, confirming the production vector dependencies load in the user's runtime. The user also ran the current RAG chain in a browser with “How to register a company in Hong Kong?” and received a cautious insufficient-information answer citing Entrepreneurs Guide PDF pages 34, 53, 66, 92 and 95. This is current-chain evidence only, not a 30-question vector benchmark or ranking-metric result. The user manually confirmed the real asynchronous Worker succeeded; automated reproduction remains unavailable.

See [STARTUP.md](STARTUP.md), [ARCHITECTURE.md](ARCHITECTURE.md), [M5.md](reports/M5.md), and [run_final_smoke.py](../scripts/run_final_smoke.py).

## P1 Web Foundation

Added `web/frontend` React/Vite and `web/backend/main.py` FastAPI/SQLite workspace. `npm run build` passes and the FastAPI temporary-DB API test passes. The UI now supports project list/create, mock memory candidate confirm/ignore, light JSON plan editing, report version history and a three-column workspace shell. Task status remains simulated and browser acceptance was not independently run. Start instructions are in [WEB_UI.md](WEB_UI.md).

## P2 Knowledge and tasks

Project-scoped PDF/DOCX/TXT upload, extraction, keyword search, file status and single-process queued index tasks are implemented. FastAPI API tests pass 2/2 and frontend build passes. This is not semantic vector retrieval or a durable cross-restart Worker; PDF/DOCX fixture extraction and browser acceptance remain unverified.
