import base64
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import server


class PrivatePilotHTTPTests(unittest.TestCase):
    def test_paid_routes_require_owner_and_preview_liveness_is_public(self):
        password='owner-test-password-for-unit-tests'
        auth='Basic '+base64.b64encode(('owner:'+password).encode()).decode()
        with patch.dict(server.os.environ,{'HOST':'0.0.0.0','OPENAI_API_KEY':'dummy','RIGHTPLACE_PRIVATE_PASSWORD':password},clear=False), patch.object(server,'model_batch',return_value={'mode':'live','answer':'test answer'}) as model, patch.object(server,'permit_request',return_value=True):
            with ThreadingHTTPServer(('127.0.0.1',0),server.Handler) as http:
                t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
                base=f'http://127.0.0.1:{http.server_port}'
                def request(path,auth_value=None,post=False,site=None):
                    headers={'Content-Type':'application/json'}
                    if auth_value: headers['Authorization']=auth_value
                    if site: headers['Sec-Fetch-Site']=site
                    req=urllib.request.Request(base+path,data=b'{"question":"Hello"}' if post else None,headers=headers)
                    try: response=urllib.request.urlopen(req,timeout=2)
                    except urllib.error.HTTPError as e: response=e
                    with response: return response.status,response.headers,response.read()
                try:
                    self.assertEqual(json.loads(request('/api/health')[2]),{'ok':True})
                    for path in ('/','/api/readiness','/api/parts','/api/jobs/example'):
                        status,headers,_=request(path)
                        self.assertEqual(status,401)
                        self.assertTrue(headers['WWW-Authenticate'].startswith('Basic '))
                    for path in ('/api/ask','/api/benchmark','/api/jobs','/api/jobs/example/resume'):
                        self.assertEqual(request(path,post=True)[0],401)
                    self.assertEqual(request('/api/ask','Basic invalid',True)[0],401)
                    self.assertEqual(request('/api/ask',auth,True,'same-site')[0],403)
                    self.assertEqual(request('/api/jobs',auth,True)[0],409)
                    model.assert_not_called()
                    self.assertEqual(request('/',auth)[0],200)
                    self.assertEqual(json.loads(request('/api/health',auth)[2])['ai_providers'],['OpenAI'])
                    self.assertEqual(json.loads(request('/api/ask',auth,True)[2])['mode'],'live')
                    model.assert_called_once()
                finally:
                    http.shutdown();t.join(timeout=2)
