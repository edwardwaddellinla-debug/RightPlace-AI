"""Readiness must never mistake a configured API key for a verified answer."""
import json, os, threading, unittest, urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import server

class ReadinessTests(unittest.TestCase):
    def test_preview_readiness(self):
        with patch.dict(os.environ, {k:'' for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY')}):
            httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
            thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{httpd.server_port}/api/readiness',timeout=3) as response:
                    data=json.load(response)
                self.assertTrue(data['server_running'])
                self.assertEqual(data['mode'],'preview_only')
                self.assertFalse(data['real_ai_configured'])
                self.assertFalse(data['real_ai_verified'])
                self.assertFalse(data['voice_device_verified'])
            finally:
                httpd.shutdown();httpd.server_close();thread.join(timeout=3)
    def test_key_does_not_mean_verified(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'fake-test-key'}):
            httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
            thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{httpd.server_port}/api/readiness',timeout=3) as response:
                    data=json.load(response)
                self.assertTrue(data['real_ai_configured'])
                self.assertFalse(data['real_ai_verified'])
                self.assertEqual(data['mode'],'configured_unverified')
            finally:
                httpd.shutdown();httpd.server_close();thread.join(timeout=3)

if __name__=='__main__':unittest.main()
