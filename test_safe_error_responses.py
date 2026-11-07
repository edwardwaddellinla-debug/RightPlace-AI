"""Regression tests: unexpected exceptions never disclose internal details."""
import json, threading, unittest, urllib.error, urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import server

class SafeErrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.httpd.server_port}/api/ask'
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(timeout=2)
    def request(self,body):
        req=urllib.request.Request(self.url,data=body,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=3) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_internal_exception_redacted(self):
        with patch.object(server,'model_batch',side_effect=RuntimeError('SECRET_KEY=/private/path')):
            status,body=self.request(b'{"question":"hello"}')
        self.assertEqual(status,500)
        self.assertNotIn('SECRET_KEY',json.dumps(body))
        self.assertNotIn('/private/path',json.dumps(body))
    def test_malformed_json_is_client_error(self):
        status,body=self.request(b'{not json')
        self.assertEqual(status,400)
        self.assertNotIn('Traceback',json.dumps(body))
if __name__=='__main__':unittest.main()
