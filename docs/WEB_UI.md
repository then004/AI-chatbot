# P1 Web workspace

Install/run locally:

```powershell
cd 'E:\year4\AI chatbot\web\frontend'; npm install; npm run build; npm run dev
cd 'E:\year4\AI chatbot'; C:\Python314\python.exe -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8100
```

The React/Vite frontend is `http://127.0.0.1:5173`; FastAPI is `http://127.0.0.1:8100`. Current API: `GET/POST /api/projects`, `GET/POST /api/projects/{id}/memory`, `POST /api/projects/{id}/memory/{memory_id}/confirmed|ignored`, `GET/POST /api/projects/{id}/reports`, `GET /api/projects/{id}/reports/{report_id}`, and `GET /api/health`. The UI now creates mock memory candidates from the conversation tab, supports confirm/ignore, edits JSON plan content, saves new report versions and shows history links. Reddit, uploads and real background execution are intentionally deferred. Existing Chainlit ports 8000/8001 remain available separately.
P2 adds `POST/GET /api/projects/{id}/uploads`, `GET /api/projects/{id}/search?q=...`, `GET /api/projects/{id}/tasks` and queued-task cancellation. Uploads accept PDF/DOCX/TXT up to 10 MB and use a single-process index task.
P3 adds proposal endpoints `POST /api/projects/{id}/research/proposals` and `/proposals/{proposal_id}/confirm`; without Reddit environment variables the confirmation is safely blocked and does not make a request. See [REDDIT_SETUP.md](REDDIT_SETUP.md).
P4 adds `GET/POST /api/projects/{id}/messages`. It uses local Ollama only; unavailable Ollama returns an explicit error. Confirmed memory is context, while candidate memory is not treated as fact.
P5 adds `POST /api/projects/{id}/plans` with idea and optional budget fields. It creates a project task and stores a report version only after the existing structured pipeline succeeds; failures are retained on the task.
P7 changes the presentation to conversation-first: use the mode chips above the composer, send questions in the message stream, and open right-side context drawers for memory, files and tasks. Business-plan and Reddit actions appear as in-chat cards rather than mandatory forms. The new visual layout needs manual browser verification.

## From-zero browser check

Run `scripts\run_web_local.ps1` for the one-command local start. It checks ports first, never kills an existing listener, starts FastAPI/Vite only when ports are free, writes PIDs/logs under `web\.runtime`, and probes both URLs. Use `-DryRun` to print commands only. Stop only matching PIDs with `scripts\stop_web_local.ps1`; it does not scan or kill unrelated Python/node processes. Open `http://127.0.0.1:5173`. Create a project, use Conversation to call local Ollama, upload/search a TXT in Knowledge, create a Plan and inspect its task/report/downloads, and open Market Validation to create a proposal. Without Reddit variables it must show blocked. Optional `.env` values are `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT`; never commit secrets.
