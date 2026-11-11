"""Idempotently copy and keyword-index the legacy public PDF knowledge base."""
import argparse, hashlib, json, shutil, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'RAG_bot'/'law'; DEST=ROOT/'web'/'public_knowledge'; DB=ROOT/'web'/'workspace.sqlite3'

def extract(pdf):
    from pypdf import PdfReader
    return [(i+1,i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(str(pdf)).pages)]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',default=str(SOURCE)); ap.add_argument('--dest',default=str(DEST)); ap.add_argument('--db',default=str(DB)); args=ap.parse_args()
    source=Path(args.source); dest=Path(args.dest); dest.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(args.db); c.executescript('CREATE TABLE IF NOT EXISTS public_documents(id TEXT PRIMARY KEY,filename TEXT NOT NULL,stored_path TEXT NOT NULL,sha256 TEXT UNIQUE,status TEXT,error TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS public_segments(id INTEGER PRIMARY KEY AUTOINCREMENT,document_id TEXT,segment INTEGER,page INTEGER,text TEXT);')
    result={'source':str(source),'destination':str(dest),'success':0,'skipped':0,'failed':0,'files':[]}
    for pdf in sorted(source.glob('*.pdf')):
        digest=hashlib.sha256(pdf.read_bytes()).hexdigest(); old=c.execute('select id,status from public_documents where sha256=?',(digest,)).fetchone()
        target=dest/pdf.name
        if old and old[1]=='indexed':
            if not target.exists(): shutil.copy2(pdf,target)
            result['skipped']+=1; result['files'].append({'file':pdf.name,'status':'skipped'}); continue
        docid=old[0] if old else digest[:32]
        try:
            if not target.exists(): shutil.copy2(pdf,target)
            rows=extract(target); c.execute('insert or replace into public_documents(id,filename,stored_path,sha256,status,error) values(?,?,?,?,?,NULL)',(docid,pdf.name,str(target),digest,'indexing')); c.execute('delete from public_segments where document_id=?',(docid,)); c.executemany('insert into public_segments(document_id,segment,page,text) values(?,?,?,?)',[(docid,i,p,t) for p,i,t in rows if t.strip()]); c.execute('update public_documents set status="indexed" where id=?',(docid,)); c.commit(); result['success']+=1; result['files'].append({'file':pdf.name,'status':'indexed','pages':len(rows)})
        except Exception as exc:
            c.execute('insert or replace into public_documents(id,filename,stored_path,sha256,status,error) values(?,?,?,?,?,?)',(docid,pdf.name,str(target),digest,'failed',str(exc))); c.commit(); result['failed']+=1; result['files'].append({'file':pdf.name,'status':'failed','error':str(exc)})
    c.close(); print(json.dumps(result,ensure_ascii=False,indent=2)); return 1 if result['failed'] else 0
if __name__=='__main__': raise SystemExit(main())
