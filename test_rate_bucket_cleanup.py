import unittest
from unittest.mock import patch
import server

class RateBucketCleanupTests(unittest.TestCase):
    def setUp(self):
        self.original=server.RATE_BUCKETS
        server.RATE_BUCKETS={}
    def tearDown(self):
        server.RATE_BUCKETS=self.original
    def test_expired_clients_removed_when_capacity_reached(self):
        server.RATE_BUCKETS.update({('/api/ask',str(i)):[0.] for i in range(1024)})
        with patch('server.time.monotonic',return_value=4000.):
            self.assertTrue(server.permit_request('/api/ask','new'))
        self.assertEqual(server.RATE_BUCKETS,{('/api/ask','new'):[4000.]})
    def test_active_client_retains_limit(self):
        with patch('server.time.monotonic',return_value=100.):
            for _ in range(12):self.assertTrue(server.permit_request('/api/ask','active'))
            self.assertFalse(server.permit_request('/api/ask','active'))
    def test_different_routes_remain_independent(self):
        with patch('server.time.monotonic',return_value=100.):
            for _ in range(4):self.assertTrue(server.permit_request('/api/benchmark','active'))
            self.assertFalse(server.permit_request('/api/benchmark','active'))
            self.assertTrue(server.permit_request('/api/ask','active'))
if __name__=='__main__':unittest.main()
