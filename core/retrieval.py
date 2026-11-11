"""Read-only Chroma SQLite FTS retrieval with stable evidence identifiers."""
import hashlib
import sqlite3
from pathlib import Path


class RetrievalService:
    def __init__(self, db_path, top_k=5, version="chroma-local-v1"):
        self.db_path = Path(db_path)
        self.top_k = top_k
        self.version = version

    def search(self, query):
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if not self.db_path.exists():
            raise FileNotFoundError(f"retrieval database not found: {self.db_path}")
        uri = "file:" + str(self.db_path).replace("\\", "/") + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as con:
            rows = con.execute("SELECT string_value, rowid FROM embedding_fulltext_search WHERE embedding_fulltext_search MATCH ? LIMIT ?", (query, self.top_k)).fetchall()
            result = []
            for text, row_id in rows:
                meta = con.execute("SELECT COALESCE(string_value, int_value, float_value) FROM embedding_metadata WHERE id=? AND key='source'", (row_id,)).fetchone()
                page = con.execute("SELECT COALESCE(string_value, int_value, float_value) FROM embedding_metadata WHERE id=? AND key='page'", (row_id,)).fetchone()
                source = meta[0] if meta else "unknown"
                page_value = page[0] if page else "unknown"
                evidence_id = "ev-" + hashlib.sha1(f"{source}|{page_value}|{text}".encode()).hexdigest()[:12]
                result.append({"evidence_id": evidence_id, "source": source, "page": page_value, "text": text, "score": None, "retrieval_mode": "sqlite_fts_fallback", "document_version": self.version})
            return result
