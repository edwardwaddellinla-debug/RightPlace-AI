import unittest
from public_launch_guard import check_public_launch

class PublicLaunchGuardTests(unittest.TestCase):
    def test_local_ai_allowed(self):
        self.assertFalse(check_public_launch({'HOST':'127.0.0.1','OPENAI_API_KEY':'dummy'})['public_bind'])
    def test_public_without_ai_allowed(self):
        self.assertTrue(check_public_launch({'HOST':'0.0.0.0'})['public_bind'])
    def test_public_with_ai_refused(self):
        with self.assertRaisesRegex(RuntimeError,'Refusing public'):
            check_public_launch({'HOST':'0.0.0.0','OPENAI_API_KEY':'dummy'})
    def test_legacy_override_does_not_open_public_access(self):
        with self.assertRaises(RuntimeError):
            check_public_launch({'HOST':'0.0.0.0','GEMINI_API_KEY':'dummy','RIGHTPLACE_ALLOW_PUBLIC_PAID':'yes'})
    def test_private_password_allows_private_pilot(self):
        env={'HOST':'0.0.0.0','OPENAI_API_KEY':'dummy','RIGHTPLACE_PRIVATE_PASSWORD':'a-local-test-password-only'}
        self.assertTrue(check_public_launch(env)['billable_provider_configured'])
    def test_ipv6_public_refused(self):
        with self.assertRaises(RuntimeError):
            check_public_launch({'HOST':'::','ANTHROPIC_API_KEY':'dummy'})

if __name__=='__main__': unittest.main()
