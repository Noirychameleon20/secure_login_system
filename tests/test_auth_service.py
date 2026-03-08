"""
tests/test_auth_service.py
==========================
Integration tests for AuthService (register, login, logout,
change password, delete account, brute-force lockout).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
from core.database     import Database
from core.security     import SecurityManager
from core.auth_service import AuthService


def make_auth():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)                  # release Windows file handle immediately
    db   = Database(path)
    sec  = SecurityManager()
    auth = AuthService(db, sec)
    return auth, db, path


def safe_teardown(db, path):
    """Close DB then delete temp file — safe on Windows."""
    db.close()
    try:
        os.unlink(path)
    except PermissionError:
        pass


class TestRegister(unittest.TestCase):

    def setUp(self):
        self.auth, self.db, self.path = make_auth()

    def tearDown(self):
        safe_teardown(self.db, self.path)

    def test_register_success(self):
        ok, msg = self.auth.register("alice", "alice@a.com", "Alice@123")
        self.assertTrue(ok)

    def test_register_duplicate(self):
        self.auth.register("alice", "alice@a.com", "Alice@123")
        ok, _ = self.auth.register("alice", "alice@a.com", "Alice@123")
        self.assertFalse(ok)

    def test_register_invalid_email(self):
        ok, _ = self.auth.register("bob", "notanemail", "Bob@1234")
        self.assertFalse(ok)

    def test_register_weak_password(self):
        ok, _ = self.auth.register("charlie", "c@c.com", "weak")
        self.assertFalse(ok)

    def test_register_short_username(self):
        ok, _ = self.auth.register("ab", "ab@ab.com", "Ab@12345")
        self.assertFalse(ok)


class TestLogin(unittest.TestCase):

    def setUp(self):
        self.auth, self.db, self.path = make_auth()
        self.auth.register("alice", "alice@a.com", "Alice@123")

    def tearDown(self):
        safe_teardown(self.db, self.path)

    def test_login_success(self):
        ok, _, token = self.auth.login("alice", "Alice@123")
        self.assertTrue(ok)
        self.assertNotEqual(token, "")

    def test_login_wrong_password(self):
        ok, _, token = self.auth.login("alice", "Wrong@000")
        self.assertFalse(ok)
        self.assertEqual(token, "")

    def test_login_nonexistent_user(self):
        ok, _, _ = self.auth.login("nobody", "Pass@123")
        self.assertFalse(ok)

    def test_lockout_after_max_attempts(self):
        for _ in range(SecurityManager.MAX_ATTEMPTS):
            self.auth.login("alice", "Wrong@000")
        ok, msg, _ = self.auth.login("alice", "Alice@123")
        self.assertFalse(ok)
        self.assertIn("locked", msg.lower())

    def test_login_creates_session(self):
        _, _, token = self.auth.login("alice", "Alice@123")
        session = self.db.get_session(token)
        self.assertIsNotNone(session)
        self.assertEqual(session["is_active"], 1)


class TestLogout(unittest.TestCase):

    def setUp(self):
        self.auth, self.db, self.path = make_auth()
        self.auth.register("alice", "alice@a.com", "Alice@123")
        _, _, self.token = self.auth.login("alice", "Alice@123")

    def tearDown(self):
        safe_teardown(self.db, self.path)

    def test_logout_invalidates_session(self):
        self.auth.logout(self.token, "alice")
        self.assertIsNone(self.db.get_session(self.token))


class TestChangePassword(unittest.TestCase):

    def setUp(self):
        self.auth, self.db, self.path = make_auth()
        self.auth.register("alice", "alice@a.com", "Alice@123")

    def tearDown(self):
        safe_teardown(self.db, self.path)

    def test_change_success(self):
        ok, _ = self.auth.change_password("alice", "Alice@123", "NewAlice@456")
        self.assertTrue(ok)

    def test_change_wrong_old_password(self):
        ok, _ = self.auth.change_password("alice", "Wrong@000", "NewAlice@456")
        self.assertFalse(ok)

    def test_change_same_password(self):
        ok, msg = self.auth.change_password("alice", "Alice@123", "Alice@123")
        self.assertFalse(ok)
        self.assertIn("differ", msg.lower())

    def test_change_weak_new_password(self):
        ok, _ = self.auth.change_password("alice", "Alice@123", "weak")
        self.assertFalse(ok)

    def test_change_invalidates_old_sessions(self):
        _, _, token = self.auth.login("alice", "Alice@123")
        self.auth.change_password("alice", "Alice@123", "NewAlice@456")
        self.assertIsNone(self.db.get_session(token))


class TestDeleteAccount(unittest.TestCase):

    def setUp(self):
        self.auth, self.db, self.path = make_auth()
        self.auth.register("alice", "alice@a.com", "Alice@123")

    def tearDown(self):
        safe_teardown(self.db, self.path)

    def test_delete_success(self):
        ok, _ = self.auth.delete_account("alice", "Alice@123")
        self.assertTrue(ok)
        self.assertIsNone(self.db.get_user("alice"))

    def test_delete_wrong_password(self):
        ok, _ = self.auth.delete_account("alice", "Wrong@000")
        self.assertFalse(ok)
        self.assertIsNotNone(self.db.get_user("alice"))


if __name__ == "__main__":
    unittest.main(verbosity=2)