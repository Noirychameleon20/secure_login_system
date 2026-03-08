"""
tests/test_database.py
======================
Unit tests for the Database layer (users, sessions, audit logs).
Each test uses a fresh temp SQLite file.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import tempfile
from core.database import Database
from core.security import SecurityManager


def make_db():
    # close=True keeps file closed so Windows doesn't hold a lock
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Database(path), path


def seed_user(db, username="alice", email="alice@test.com",
              password="Alice@123"):
    salt  = SecurityManager.generate_salt()
    phash = SecurityManager.hash_password(password, salt)
    db.create_user(username, email, phash, salt)
    return db.get_user(username)


class TestUserCRUD(unittest.TestCase):

    def setUp(self):
        self.db, self.path = make_db()

    def tearDown(self):
        self.db.close()          # explicitly close connection first
        try:
            os.unlink(self.path)
        except PermissionError:
            pass                 # skip if Windows still holds it

    def test_create_user_success(self):
        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password("Pass@123", salt)
        self.assertTrue(self.db.create_user("bob", "bob@b.com", phash, salt))

    def test_create_duplicate_fails(self):
        seed_user(self.db)
        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password("Pass@123", salt)
        self.assertFalse(
            self.db.create_user("alice", "alice@test.com", phash, salt)
        )

    def test_get_user_exists(self):
        seed_user(self.db)
        user = self.db.get_user("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "alice")

    def test_get_user_missing(self):
        self.assertIsNone(self.db.get_user("nobody"))

    def test_lock_user(self):
        seed_user(self.db)
        self.db.lock_user("alice")
        self.assertEqual(self.db.get_user("alice")["is_locked"], 1)

    def test_reset_failed_attempts(self):
        seed_user(self.db)
        self.db.lock_user("alice")
        self.db.reset_failed_attempts("alice")
        user = self.db.get_user("alice")
        self.assertEqual(user["is_locked"], 0)
        self.assertEqual(user["failed_attempts"], 0)

    def test_delete_user(self):
        seed_user(self.db)
        self.db.delete_user("alice")
        self.assertIsNone(self.db.get_user("alice"))

    def test_update_password(self):
        seed_user(self.db)
        new_salt  = SecurityManager.generate_salt()
        new_hash  = SecurityManager.hash_password("New@456", new_salt)
        self.db.update_password("alice", new_hash, new_salt)
        user = self.db.get_user("alice")
        self.assertEqual(user["password_hash"], new_hash)


class TestSessions(unittest.TestCase):

    def setUp(self):
        self.db, self.path = make_db()
        self.user = seed_user(self.db)

    def tearDown(self):
        self.db.close()
        try:
            os.unlink(self.path)
        except PermissionError:
            pass

    def test_create_and_retrieve_session(self):
        token, exp = SecurityManager.generate_session_token()
        self.assertTrue(self.db.create_session(self.user["id"], token, exp))
        session = self.db.get_session(token)
        self.assertIsNotNone(session)
        self.assertEqual(session["token"], token)

    def test_invalidate_session(self):
        token, exp = SecurityManager.generate_session_token()
        self.db.create_session(self.user["id"], token, exp)
        self.db.invalidate_session(token)
        self.assertIsNone(self.db.get_session(token))

    def test_invalidate_all_sessions(self):
        for _ in range(3):
            token, exp = SecurityManager.generate_session_token()
            self.db.create_session(self.user["id"], token, exp)
        self.db.invalidate_all_sessions(self.user["id"])
        token, exp = SecurityManager.generate_session_token()
        self.db.create_session(self.user["id"], token, exp)
        self.db.invalidate_all_sessions(self.user["id"])
        self.assertIsNone(self.db.get_session(token))


class TestAuditLogs(unittest.TestCase):

    def setUp(self):
        self.db, self.path = make_db()

    def tearDown(self):
        self.db.close()
        try:
            os.unlink(self.path)
        except PermissionError:
            pass

    def test_log_created(self):
        self.db.log_action("alice", "LOGIN", "SUCCESS", "ok")
        logs = self.db.get_audit_logs()
        self.assertGreater(len(logs), 0)

    def test_log_most_recent_first(self):
        self.db.log_action("alice", "LOGIN",  "SUCCESS")
        self.db.log_action("alice", "LOGOUT", "SUCCESS")
        logs = self.db.get_audit_logs()
        self.assertEqual(logs[0]["action"], "LOGOUT")


if __name__ == "__main__":
    unittest.main(verbosity=2)