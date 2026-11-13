"""Verify database handles are closed and failures roll back."""
import os, sqlite3, tempfile, unittest
from unittest.mock import patch
import server

class DatabaseLifecycleTests(unittest.TestCase):
    def test_connection_closed_after_success(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, 'DB', server.Path(tmp)/'db.sqlite'):
            with server.connect() as conn:
                conn.execute('CREATE TABLE test (value TEXT)')
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute('SELECT 1')

    def test_connection_rollback_and_close_on_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, 'DB', server.Path(tmp)/'db.sqlite'):
            with server.connect() as conn:
                conn.execute('CREATE TABLE test (value TEXT)')
            with self.assertRaisesRegex(RuntimeError, 'abort'):
                with server.connect() as conn:
                    conn.execute("INSERT INTO test VALUES ('should rollback')")
                    raise RuntimeError('abort')
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute('SELECT 1')
            with server.connect() as check:
                self.assertEqual(check.execute('SELECT count(*) FROM test').fetchone()[0], 0)
