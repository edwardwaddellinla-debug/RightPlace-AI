import pathlib, re, unittest
ROOT=pathlib.Path(__file__).resolve().parent
class DeploymentPackageTests(unittest.TestCase):
    def test_dockerfile_copies_all_local_imports(self):
        server=(ROOT/'server.py').read_text()
        docker=(ROOT/'Dockerfile').read_text()
        for module in re.findall(r'^from ([a-z_]+) import ',server,re.M):
            if (ROOT/(module+'.py')).exists():
                self.assertIn(module+'.py',docker)
    def test_free_preview_has_no_paid_keys_or_unsafe_override(self):
        manifest=(ROOT/'render.yaml').read_text()
        self.assertIn('plan: free',manifest)
        self.assertIn('runtime: docker',manifest)
        self.assertNotIn('RIGHTPLACE_ALLOW_PUBLIC_PAID',manifest)
        for key in ('OPENAI_API_KEY','GEMINI_API_KEY','ANTHROPIC_API_KEY'):
            self.assertNotIn(key,manifest)
    def test_docker_has_no_false_persistent_volume_claim(self):
        docker=(ROOT/'Dockerfile').read_text()
        self.assertNotIn('RIGHTPLACE_DB=/data/',docker)
if __name__=='__main__': unittest.main()
