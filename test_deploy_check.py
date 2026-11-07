import unittest
from deploy_check import audit
class DeploymentAuditTests(unittest.TestCase):
    def test_empty_config_warns(self):
        a=audit({})
        self.assertFalse(a['ready_for_public_paid_launch'])
        self.assertEqual(a['configured_providers'],[])
        self.assertGreaterEqual(len(a['warnings']),4)
    def test_configured_key_not_leaked(self):
        a=audit({'OPENAI_API_KEY':'secret-123','RIGHTPLACE_DB':'/data/db.sqlite','RIGHTPLACE_PERSISTENT_DISK':'yes'})
        self.assertEqual(a['configured_providers'],['OpenAI'])
        self.assertNotIn('secret-123',str(a))
        self.assertTrue(a['persistent_storage_verified'])
        self.assertFalse(a['ready_for_public_paid_launch'])
    def test_disk_path_alone_is_not_proof(self):
        self.assertFalse(audit({'RIGHTPLACE_DB':'/data/db.sqlite'})['persistent_storage_verified'])
if __name__=='__main__':unittest.main()
