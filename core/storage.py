"""Minimal parameterized SQLite persistence and single-worker task state machine."""
import sqlite3, time
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS projects (project_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, name TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS input_snapshots (snapshot_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, payload_json TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, snapshot_id TEXT, run_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, timeout_seconds REAL, retry_count INTEGER NOT NULL DEFAULT 0, max_concurrency INTEGER NOT NULL DEFAULT 1, heartbeat_at REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS task_steps (step_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL, detail TEXT, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS evidence_records (evidence_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, source TEXT NOT NULL, page TEXT, text TEXT NOT NULL, retrieval_mode TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS report_versions (report_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, task_id TEXT NOT NULL, run_id TEXT NOT NULL UNIQUE, version_no INTEGER NOT NULL, json_path TEXT NOT NULL, html_path TEXT NOT NULL, created_at REAL NOT NULL, UNIQUE(project_id, version_no));
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status); CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
'''
VALID = {'queued','running','waiting_input','succeeded','failed','cancelled','interrupted'}

class Storage:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, isolation_level=None, timeout=10)
        self.db.execute('PRAGMA journal_mode=WAL'); self.db.executescript(SCHEMA)
    def close(self): self.db.close()
    def create_project(self, project_id, session_id, name):
        self.db.execute('INSERT INTO projects VALUES (?,?,?,?)',(project_id,session_id,name,time.time()))
    def create_task(self, task_id, project_id, snapshot_id, run_id, timeout=900, retry=0, max_concurrency=1):
        now=time.time(); self.db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?)',(task_id,project_id,snapshot_id,run_id,'queued',timeout,retry,max_concurrency,None,now,now))
    def claim_one(self):
        try:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute("SELECT task_id FROM tasks WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
            if not row: self.db.execute('COMMIT'); return None
            now=time.time(); self.db.execute("UPDATE tasks SET status='running',heartbeat_at=?,updated_at=? WHERE task_id=? AND status='queued'",(now,now,row[0])); self.db.execute('COMMIT'); return row[0]
        except Exception:
            if self.db.in_transaction: self.db.execute('ROLLBACK')
            raise
    def heartbeat(self, task_id): self.db.execute("UPDATE tasks SET heartbeat_at=?,updated_at=? WHERE task_id=? AND status='running'",(time.time(),time.time(),task_id))
    def finish(self, task_id, status, detail=None):
        if status not in VALID or status in {'queued','running'}: raise ValueError('invalid terminal status')
        self.db.execute('UPDATE tasks SET status=?,updated_at=? WHERE task_id=?',(status,time.time(),task_id))
        if detail: self.db.execute('INSERT INTO task_steps VALUES (?,?,?,?,?)',(task_id+'-finish',task_id,'finish',status+': '+detail,time.time()))
    def cancel(self, task_id): self.db.execute("UPDATE tasks SET status='cancelled',updated_at=? WHERE task_id=? AND status IN ('queued','running','waiting_input')",(time.time(),task_id))
    def task_status(self, task_id):
        row=self.db.execute('SELECT status FROM tasks WHERE task_id=?',(task_id,)).fetchone(); return row[0] if row else None
    def is_cancel_requested(self, task_id): return self.task_status(task_id) == 'cancelled'
    def step_if_active(self, task_id, step_name):
        if self.is_cancel_requested(task_id): return False
        self.db.execute('INSERT INTO task_steps VALUES (?,?,?,?,?,?)',(task_id+'-'+step_name,task_id,step_name,'completed',None,time.time()))
        return not self.is_cancel_requested(task_id)
    def recover_stale(self, age=900):
        cutoff=time.time()-age; cur=self.db.execute("UPDATE tasks SET status='interrupted',updated_at=? WHERE status='running' AND COALESCE(heartbeat_at,updated_at)<?",(time.time(),cutoff)); return cur.rowcount
    def add_report(self, project_id, task_id, run_id, json_path, html_path):
        try:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT COALESCE(MAX(version_no),0)+1 FROM report_versions WHERE project_id=?',(project_id,)).fetchone(); version=row[0]
            self.db.execute('INSERT INTO report_versions VALUES (?,?,?,?,?,?,?,?)',(f'{run_id}-report',project_id,task_id,run_id,version,json_path,html_path,time.time()))
            self.db.execute('COMMIT'); return version
        except Exception:
            if self.db.in_transaction: self.db.execute('ROLLBACK')
            raise
