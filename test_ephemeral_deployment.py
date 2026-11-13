import tempfile
import unittest
from pathlib import Path
from deployment_preflight import inspect_deployment

class StoragePreflightTests(unittest.TestCase):
    def test_free_render_warns_about_ephemeral_storage(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('server.py','index.html','Dockerfile'):
                (root/name).write_text('')
            (root/'render.yaml').write_text('services:\n  - type: web\n    plan: free\n')
            result=inspect_deployment({'HOST':'0.0.0.0','OPENAI_API_KEY':'example'},root)
            self.assertTrue(any('ephemeral SQLite' in x for x in result['findings']))
            self.assertFalse(result['ready_for_real_ai'])

if __name__=='__main__': unittest.main()
