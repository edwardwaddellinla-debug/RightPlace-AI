import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
import server

class DeleteResearchTests(unittest.TestCase):
    def test_owned_job_deleted_and_wrong_token_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server,'DB',Path(tmp)/'test.db'):
            server.setup()
            jid='deletion-test'; token='secret-test-token'
            with server.connect() as c:
                c.execute('INSERT INTO jobs(id,question,status,created_at,updated_at,next_run) VALUES(?,?,?,?,?,?)',(jid,'test','queued',server.now(),server.now(),0))
                c.execute('INSERT INTO job_tokens VALUES(?,?)',(jid,server.token_hash(token)))
                c.execute('INSERT INTO findings(job_id,created_at,query,source_url,title,snippet) VALUES(?,?,?,?,?,?)',(jid,server.now(),'q','https://example.com','title','snippet'))
                c.execute('INSERT INTO runs(job_id,round,created_at,notes,urls_checked) VALUES(?,?,?,?,?)',(jid,1,server.now(),'note',1))
                c.execute('INSERT INTO tried_steps(job_id,created_at,step) VALUES(?,?,?)',(jid,server.now(),'attempt'))
            self.assertFalse(server.delete_research_job(jid,'wrong'))
            self.assertIsNotNone(server.get_job(jid))
            self.assertTrue(server.delete_research_job(jid,token))
            self.assertFalse(server.check_token(jid,token))
            with server.connect() as c:
                for table in ('jobs','job_tokens','findings','runs','tried_steps'):
                    self.assertEqual(c.execute(f'SELECT count(*) FROM {table}').fetchone()[0],0,table)
            self.assertFalse(server.delete_research_job(jid,token))
if __name__=='__main__':unittest.main()
