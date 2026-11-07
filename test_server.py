import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

# One isolated database for the entire test module. Unittest runs test classes
# alphabetically, so class-scoped setup previously left earlier classes without tables.
_TEST_DIR = None

def setUpModule():
    global _TEST_DIR
    _TEST_DIR = tempfile.TemporaryDirectory()
    os.environ['RIGHTPLACE_DB'] = str(Path(_TEST_DIR.name) / 'test.db')
    import server
    server.DB = Path(os.environ['RIGHTPLACE_DB'])
    server.setup()

def tearDownModule():
    global _TEST_DIR
    if _TEST_DIR is not None:
        _TEST_DIR.cleanup()
        _TEST_DIR = None

class RightPlaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server
        cls.s = server

    def test_scores(self):
        self.assertTrue(self.s.score_known_answer('Advil contains ibuprofen.','ibuprofen'))
        self.assertFalse(self.s.score_known_answer('Acetaminophen','ibuprofen'))
        self.assertFalse(self.s.score_known_answer('notibuprofen','ibuprofen'))
        self.assertIsNone(self.s.score_known_answer('Anything',''))

    def test_secrets(self):
        import secrets
        token=secrets.token_urlsafe(24)
        with self.s.connect() as c:
            c.execute('INSERT INTO job_tokens VALUES (?,?)',('testjob',self.s.token_hash(token)))
        self.assertTrue(self.s.check_token('testjob',token))
        self.assertFalse(self.s.check_token('testjob','wrong'))
        self.assertFalse(self.s.check_token('testjob',''))
        self.assertFalse(self.s.check_token('missing',token))

    def test_demo_no_keys(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'','ANTHROPIC_API_KEY':'','GEMINI_API_KEY':''}):
            answer=self.s.model_batch('What is this?',compare=True)
            self.assertEqual(answer['mode'],'demo')
            self.assertEqual(answer['results'],[])



# Additional tests run under the same suite using a separate class.
class JobWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server
        cls.s=server
        cls.s.setup()

    def test_request_rate_limit(self):
        addr='test-'+__import__('uuid').uuid4().hex
        for i in range(4):self.assertTrue(self.s.permit_request('/api/benchmark',addr))
        self.assertFalse(self.s.permit_request('/api/benchmark',addr))

    def test_budget_counter(self):
        s=self.s
        with patch.object(s,'MAX_DAILY_AI_CALLS',2):
            with s.connect() as c:c.execute('DELETE FROM ai_budget')
            self.assertTrue(s.claim_ai_budget())
            self.assertTrue(s.claim_ai_budget())
            self.assertFalse(s.claim_ai_budget())

    def test_tried_steps_database(self):
        s=self.s
        jid='workflow-'+__import__('uuid').uuid4().hex
        with s.connect() as c:
            c.execute('INSERT INTO jobs(id,question,status,created_at,updated_at,next_run) VALUES(?,?,?,?,?,?)',(jid,'Help with a pump','queued',s.now(),s.now(),0))
            c.execute('INSERT INTO tried_steps(job_id,created_at,step) VALUES(?,?,?)',(jid,s.now(),'Checked hydraulic fluid'))
        self.assertEqual(s.get_job(jid)['tried_steps'][0]['step'],'Checked hydraulic fluid')

class EvidenceQualityTests(unittest.TestCase):
    def test_schema_is_ready_before_any_test_class(self):
        import server as s
        with s.connect() as c:
            names={row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({'jobs','findings','job_tokens','tried_steps','ai_budget'}.issubset(names))

    def test_labels_are_not_truth_claims(self):
        import server as s
        self.assertEqual(s.source_category('https://www.ontario.ca/page/example'),'government')
        self.assertEqual(s.source_category('https://www.canada.ca/en/example'),'government')
        self.assertEqual(s.source_category('https://www.reddit.com/r/MechanicAdvice/'),'community discussion')
        self.assertEqual(s.source_category('https://www.cdc.gov/health'),'government')
        self.assertEqual(s.source_category('https://youtube.com/watch?v=abc'),'video')
    def test_normalizes_tracking_only(self):
        import server as s
        self.assertEqual(s.normalized_source_url('https://example.com/part/?utm_source=google&id=32#reviews'),'https://example.com/part?id=32')
        self.assertEqual(s.normalized_source_url('file:///etc/passwd'),'')
    def test_repetition_detector(self):
        import server as s
        prior='Check the hydraulic fluid level, inspect the line, locate the identification plate, and confirm whether the pump motor responds when the controls engage, recording the resulting pressure and temperature readings.'
        self.assertTrue(s.substantial_repeat(prior, [prior]))
        self.assertFalse(s.substantial_repeat('An entirely new research avenue involves a warranty recall bulletin and manufacturer specification changes.',[prior]))
    def test_job_only_contains_unverified_leads(self):
        import server as s,uuid
        jid='evidence-'+uuid.uuid4().hex
        with s.connect() as c:
            c.execute('INSERT INTO jobs(id,question,status,created_at,updated_at,next_run) VALUES(?,?,?,?,?,?)',(jid,'Question','waiting',s.now(),s.now(),0))
            c.execute('INSERT INTO findings(job_id,created_at,query,source_url,title,snippet) VALUES(?,?,?,?,?,?)',(jid,s.now(),'query','https://reddit.com/r/test','Topic','Community suggestion'))
        j=s.get_job(jid)
        self.assertEqual(j['findings'][0]['evidence_status'],'unverified search lead')
        self.assertEqual(j['source_types']['community discussion'],1)

if __name__=='__main__':unittest.main()


class RequestParsingTests(unittest.TestCase):
    def test_rejects_negative_or_missing_content_length(self):
        import server, io
        for headers in ({'Content-Length':'-1','Content-Type':'application/json'},
                        {'Content-Type':'application/json'},
                        {'Content-Length':'bad','Content-Type':'application/json'}):
            fake=type('Fake',(),{'headers':headers,'rfile':io.BytesIO(b'{}')})()
            with self.assertRaises(ValueError):server.Handler.read_body(fake)

    def test_rejects_arrays_and_oversize_bodies(self):
        import server, io
        for data in (b'[]',b'null',b'42'):
            fake=type('Fake',(),{'headers':{'Content-Length':str(len(data)),'Content-Type':'application/json'},'rfile':io.BytesIO(data)})()
            with self.assertRaises(ValueError):server.Handler.read_body(fake)
        fake=type('Fake',(),{'headers':{'Content-Length':'30001','Content-Type':'application/json'},'rfile':io.BytesIO(b'')})()
        with self.assertRaises(ValueError):server.Handler.read_body(fake)

    def test_accepts_json_object_with_charset(self):
        import server, io
        data=b'{"question":"hello"}'
        fake=type('Fake',(),{'headers':{'Content-Length':str(len(data)),'Content-Type':'application/json; charset=utf-8'},'rfile':io.BytesIO(data)})()
        self.assertEqual(server.Handler.read_body(fake),{'question':'hello'})
