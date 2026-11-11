# Architecture

The verified default path is fixed business-plan generation plus a separate RAG page. M3 adds an opt-in structured pipeline. M4 adds a constrained action loop with four actions; it is not claimed to be autonomous improvement over the fixed path.

Retrieval currently has a read-only `sqlite_fts_fallback` path. This is lexical fallback, not semantic vector-RAG acceptance. The existing vector path remains blocked in this execution environment by the copied Store-Python virtualenv.

SQLite storage provides a single-worker foundation, atomic claims, heartbeats, recovery and safe cancellation checkpoints. It is not connected to UI and is not a real asynchronous worker yet. The real Ollama trace selected a repeated search action and was correctly marked failed/fallback.
