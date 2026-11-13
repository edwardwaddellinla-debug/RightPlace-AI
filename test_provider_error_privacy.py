import unittest
import urllib.error
from unittest.mock import patch
import server

class ProviderErrorPrivacyTests(unittest.TestCase):
    def test_http_error_never_leaks_secret_or_url(self):
        error=urllib.error.HTTPError('https://api.example/?key=SECRET123',401,'SECRET123',None,None)
        msg=server.safe_provider_error(error)
        self.assertNotIn('SECRET123',msg)
        self.assertNotIn('https:',msg)
        self.assertIn('authentication',msg)
    def test_network_failure_never_leaks_secret(self):
        msg=server.safe_provider_error(urllib.error.URLError('token=SECRET123'))
        self.assertNotIn('SECRET123',msg)
    def test_unknown_failure_never_leaks_secret(self):
        msg=server.safe_provider_error(ValueError('SECRET123'))
        self.assertNotIn('SECRET123',msg)
    def test_actual_provider_path_redacts_secret(self):
        with patch.dict(server.os.environ,{'OPENAI_API_KEY':'SECRET123'}),patch.object(server,'claim_ai_budget',return_value=True),patch.object(server,'post_json',side_effect=ValueError('SECRET123')):
            response=server.ask_model('OpenAI','test')
        self.assertNotIn('SECRET123',str(response))
        self.assertIn('error',response)

if __name__=='__main__':unittest.main()
