import tempfile,unittest
from pathlib import Path
from deployment_preflight import inspect_deployment

class DeploymentPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in ('server.py','index.html','Dockerfile','render.yaml'):(self.root/name).write_text('ok')
    def test_preview_not_ready(self):
        report=inspect_deployment({'HOST':'0.0.0.0'},self.root)
        self.assertFalse(report['ready_for_real_ai']);self.assertIn('preview',str(report['findings']))
    def test_local_ai_ready(self):
        report=inspect_deployment({'HOST':'127.0.0.1','OPENAI_API_KEY':'TOP_SECRET'},self.root)
        self.assertTrue(report['ready_for_real_ai']);self.assertNotIn('TOP_SECRET',str(report))
    def test_public_paid_requires_protection(self):
        report=inspect_deployment({'HOST':'0.0.0.0','OPENAI_API_KEY':'TOP_SECRET'},self.root)
        self.assertFalse(report['ready_for_real_ai']);self.assertNotIn('TOP_SECRET',str(report))
    def test_missing_files(self):
        (self.root/'index.html').unlink()
        self.assertIn('Missing required file: index.html',inspect_deployment({},self.root)['findings'])
    def test_override_warns(self):
        report=inspect_deployment({'HOST':'0.0.0.0','OPENAI_API_KEY':'secret','RIGHTPLACE_ALLOW_PUBLIC_PAID':'yes'},self.root)
        self.assertFalse(report['ready_for_real_ai'])
        self.assertIn('distributed abuse',str(report['findings']))
if __name__=='__main__':unittest.main()
