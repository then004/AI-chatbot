import os, sqlite3, tempfile, time, unittest
from core.storage import Storage

class StorageTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(dir=os.getenv('AI_CHATBOT_TEST_TMPDIR') or None); self.s=Storage(os.path.join(self.tmp.name,'state.sqlite3')); self.s.create_project('p','s','P')
    def tearDown(self): self.s.close(); self.tmp.cleanup()
    def task(self, n='1'): self.s.create_task('t'+n,'p',None,'r'+n)
    def test_migration_and_project_isolation(self):
        self.task(); self.s.create_project('p2','s2','P2'); self.s.create_task('t2','p2',None,'r2'); self.assertEqual(self.s.db.execute('select count(*) from tasks where project_id=?',('p',)).fetchone()[0],1)
    def test_atomic_claim_and_cancel(self):
        self.task(); self.assertEqual(self.s.claim_one(),'t1'); self.assertIsNone(self.s.claim_one()); self.s.cancel('t1'); self.assertEqual(self.s.db.execute('select status from tasks where task_id=?',('t1',)).fetchone()[0],'cancelled')
    def test_recovery_and_versions(self):
        self.task(); self.s.claim_one(); self.s.db.execute("update tasks set heartbeat_at=?",(time.time()-1000,)); self.assertEqual(self.s.recover_stale(900),1); self.assertEqual(self.s.db.execute('select status from tasks').fetchone()[0],'interrupted'); self.assertEqual(self.s.add_report('p','t1','r1','a','b'),1); self.assertEqual(self.s.add_report('p','t1','r2','c','d'),2)
    def test_two_connections_versions_and_safe_cancel_step(self):
        self.task(); self.s.finish('t1','succeeded'); other=Storage(self.s.path); self.assertEqual(self.s.add_report('p','t1','r1','a','b'),1); self.assertEqual(other.add_report('p','t1','r2','c','d'),2); other.close()
        self.task('3'); self.assertEqual(self.s.claim_one(),'t3'); self.s.cancel('t3'); self.assertTrue(self.s.is_cancel_requested('t3')); self.assertFalse(self.s.step_if_active('t3','ollama'))
        self.task('4'); self.assertEqual(self.s.claim_one(),'t4'); self.assertTrue(self.s.step_if_active('t4','retrieve')); row=self.s.db.execute("select status,detail,created_at from task_steps where task_id=?",('t4',)).fetchone(); self.assertEqual(row[0],'completed'); self.assertIsNone(row[1]); self.assertGreater(row[2],0); self.s.cancel('t4'); count=self.s.db.execute("select count(*) from task_steps where task_id=?",('t4',)).fetchone()[0]; self.assertFalse(self.s.step_if_active('t4','ollama')); self.assertEqual(self.s.db.execute("select count(*) from task_steps where task_id=?",('t4',)).fetchone()[0],count)
    def test_claim_rolls_back_after_transaction_error(self):
        self.task(); self.s.db.execute('BEGIN');
        with self.assertRaises(sqlite3.OperationalError): self.s.claim_one()
        self.assertEqual(self.s.db.execute('select status from tasks where task_id=?',('t1',)).fetchone()[0],'queued')
    def test_unique_ids(self):
        self.task()
        with self.assertRaises(sqlite3.IntegrityError): self.s.create_task('t2','p',None,'r1')

if __name__ == '__main__': unittest.main()
