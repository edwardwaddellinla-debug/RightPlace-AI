import unittest
from unittest.mock import patch
import server

class ProviderFailureTests(unittest.TestCase):
    def test_configured_but_failing_provider_is_not_live(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'test'}, clear=True), patch.object(server,'ask_model',return_value={'provider':'OpenAI','available':True,'error':'upstream error'}):
            result=server.model_batch('Hello')
        self.assertEqual(result['mode'],'unavailable')
        self.assertNotIn('No available model returned',result['answer'])
    def test_empty_provider_output_is_not_live(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'test'}, clear=True), patch.object(server,'claim_ai_budget',return_value=True), patch.object(server,'post_json',return_value={'output':[]}):
            provider=server.ask_model('OpenAI','Hello')
            result=server.model_batch('Hello')
        self.assertNotIn('answer',provider)
        self.assertEqual(result['mode'],'unavailable')

    def test_error_and_answer_together_is_not_live(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'test'}, clear=True), patch.object(server,'ask_model',return_value={'provider':'OpenAI','available':True,'answer':'Old cached answer','error':'provider failed','seconds':0.1}):
            result=server.model_batch('Hello')
        self.assertEqual(result['mode'],'unavailable')

    def test_successful_provider_is_live(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'test'}, clear=True), patch.object(server,'ask_model',return_value={'provider':'OpenAI','available':True,'answer':'Hello','seconds':0.2}):
            result=server.model_batch('Hello')
        self.assertEqual(result['mode'],'live')
        self.assertEqual(result['answer'],'Hello')

if __name__=='__main__':unittest.main()
