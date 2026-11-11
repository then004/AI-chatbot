# Windows local startup

Prerequisites: Ollama installed and `qwen2.5:3b` available. No API key is required.

```powershell
cd 'E:\year4\AI chatbot'
ollama list
ollama pull qwen2.5:3b   # only if missing
& '.\.venv\Scripts\python.exe' -m chainlit run '.\RAG_bot\chainlit_app.py' --host 127.0.0.1 --port 8000
& '.\.venv\Scripts\python.exe' -m chainlit run '.\StartUp_Advisor\startup_web.py' --host 127.0.0.1 --port 8001
```

Optional structured path: set `$env:STARTUP_STRUCTURED_PIPELINE='1'` before starting port 8001. Agent and evaluation entry points are standalone scripts under `scripts/` and do not change the default UI.

Check Ollama with `Invoke-WebRequest http://127.0.0.1:11434/api/tags`. To stop only a process you started, inspect `Get-NetTCPConnection -LocalPort 8000,8001` and use `Stop-Process -Id <PID>` after verifying the PID. Do not kill unrelated processes. Tests use `$env:AI_CHATBOT_TEST_TMPDIR` when the system temp directory is restricted.

Full tests: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=E:\year4\AI chatbot`, then `C:\Python314\python.exe -m unittest discover -s E:\year4\AI chatbot\tests -v`.
