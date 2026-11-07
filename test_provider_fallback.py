import unittest
from unittest.mock import patch
import server

class ProviderFallbackTests(unittest.TestCase):
    def test_failed_primary_uses_backup(self):
        def fake(name, prompt, timeout=35):
            return {'provider':name,'available':True,'error':'timeout'} if name=='OpenAI' else {'provider':name,'available':True,'answer':'Backup answer','seconds':0.2}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'x','ANTHROPIC_API_KEY':'y'},clear=True), patch.object(server,'ask_model',side_effect=fake) as call:
            result=server.model_batch('test')
        self.assertEqual(result['mode'],'live')
        self.assertEqual(result['answer'],'Backup answer')
        self.assertEqual(call.call_count,2)
        self.assertTrue(all(x.kwargs['timeout']==12 for x in call.call_args_list))

    def test_success_does_not_call_backup(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'x','ANTHROPIC_API_KEY':'y'},clear=True), patch.object(server,'ask_model',return_value={'provider':'OpenAI','available':True,'answer':'ok','seconds':0.1}) as call:
            result=server.model_batch('test')
        self.assertEqual(result['mode'],'live')
        self.assertEqual(call.call_count,1)

    def test_third_provider_after_two_failures(self):
        def fake(name, prompt, timeout=35):
            if name == 'Gemini':
                return {'provider':name,'available':True,'answer':'Third provider works','seconds':0.1}
            return {'provider':name,'available':True,'error':'failed'}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'x','ANTHROPIC_API_KEY':'y','GEMINI_API_KEY':'z'},clear=True), patch.object(server,'ask_model',side_effect=fake) as call:
            result=server.model_batch('test')
        self.assertEqual(result['mode'],'live')
        self.assertEqual(result['answer'],'Third provider works')
        self.assertEqual(call.call_count,3)
        self.assertTrue(all(x.kwargs['timeout']==12 for x in call.call_args_list))

    def test_both_fail_reports_unavailable(self):
        with patch.dict(server.os.environ, {'OPENAI_API_KEY':'x','ANTHROPIC_API_KEY':'y'},clear=True), patch.object(server,'ask_model',return_value={'available':True,'error':'failed'}) as call:
            result=server.model_batch('test')
        self.assertEqual(result['mode'],'unavailable')
        self.assertEqual(call.call_count,2)

if __name__=='__main__':unittest.main()
