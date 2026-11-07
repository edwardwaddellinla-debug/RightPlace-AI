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
    def test_explicit_override(self):
        self.assertTrue(check_public_launch({'HOST':'0.0.0.0','GEMINI_API_KEY':'dummy','RIGHTPLACE_ALLOW_PUBLIC_PAID':'yes'})['billable_provider_configured'])
    def test_ipv6_public_refused(self):
        with self.assertRaises(RuntimeError):
            check_public_launch({'HOST':'::','ANTHROPIC_API_KEY':'dummy'})

if __name__=='__main__': unittest.main()
