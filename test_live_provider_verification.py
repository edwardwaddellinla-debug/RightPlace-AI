import json, os, tempfile, unittest
from unittest.mock import patch
import server

class ProviderVerificationTests(unittest.TestCase):
    def setUp(self):
        server.VERIFIED_PROVIDERS.clear()
        self.tmp=tempfile.TemporaryDirectory()
        self.old_db=server.DB
        server.DB=__import__('pathlib').Path(self.tmp.name)/'db.sqlite'
        server.setup()
    def tearDown(self):
        server.DB=self.old_db
        server.VERIFIED_PROVIDERS.clear()
        self.tmp.cleanup()
    def test_success_marks_only_actual_provider(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake'}),patch.object(server,'post_json',return_value={'output':[{'content':[{'type':'output_text','text':'Hello'}]}]}):
            result=server.ask_model('OpenAI','hello')
        self.assertEqual(result['answer'],'Hello')
        self.assertEqual(server.VERIFIED_PROVIDERS,{'OpenAI'})
    def test_empty_reply_not_verified(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake'}),patch.object(server,'post_json',return_value={'output':[]}):
            result=server.ask_model('OpenAI','hello')
        self.assertIn('error',result)
        self.assertFalse(server.VERIFIED_PROVIDERS)
    def test_exception_not_verified(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake'}),patch.object(server,'post_json',side_effect=TimeoutError('secret')):
            result=server.ask_model('OpenAI','hello')
        self.assertIn('error',result)
        self.assertNotIn('secret',result['error'])
        self.assertFalse(server.VERIFIED_PROVIDERS)
if __name__=='__main__':unittest.main()
