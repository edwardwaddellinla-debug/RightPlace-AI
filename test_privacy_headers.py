"""Check privacy and framing protections on both HTML and JSON responses."""
import threading, unittest, urllib.request
from http.server import ThreadingHTTPServer
from server import Handler

class PrivacyHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.worker.join(timeout=2)
    def test_headers_on_html_and_json(self):
        for path in ('/', '/api/health'):
            with self.subTest(path=path):
                with urllib.request.urlopen(f'http://127.0.0.1:{self.server.server_port}{path}', timeout=3) as r:
                    self.assertEqual(r.headers['Cache-Control'], 'no-store')
                    self.assertEqual(r.headers['X-Frame-Options'], 'DENY')
                    self.assertEqual(r.headers['X-Content-Type-Options'], 'nosniff')
                    self.assertEqual(r.headers['Referrer-Policy'], 'no-referrer')
if __name__ == '__main__': unittest.main()
