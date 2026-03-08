"""
tests/test_security.py
======================
Unit tests for SecurityManager (hashing, validation, sessions, lockout).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from core.security import SecurityManager


class TestPasswordHashing(unittest.TestCase):

    def test_salt_length(self):
        self.assertEqual(len(SecurityManager.generate_salt()), 64)

    def test_salt_uniqueness(self):
        self.assertNotEqual(
            SecurityManager.generate_salt(),
            SecurityManager.generate_salt()
        )

    def test_hash_is_string(self):
        salt = SecurityManager.generate_salt()
        h = SecurityManager.hash_password("Test@123", salt)
        self.assertIsInstance(h, str)
        self.assertTrue(len(h) > 0)

    def test_hash_deterministic(self):
        salt = SecurityManager.generate_salt()
        self.assertEqual(
            SecurityManager.hash_password("Test@123", salt),
            SecurityManager.hash_password("Test@123", salt)
        )

    def test_different_salts_differ(self):
        s1, s2 = SecurityManager.generate_salt(), SecurityManager.generate_salt()
        self.assertNotEqual(
            SecurityManager.hash_password("Test@123", s1),
            SecurityManager.hash_password("Test@123", s2)
        )

    def test_verify_correct(self):
        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password("Correct@1", salt)
        self.assertTrue(SecurityManager.verify_password("Correct@1", salt, phash))

    def test_verify_wrong(self):
        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password("Correct@1", salt)
        self.assertFalse(SecurityManager.verify_password("Wrong@1", salt, phash))


class TestPasswordStrength(unittest.TestCase):

    def test_too_short(self):
        ok, msg = SecurityManager.validate_password_strength("Ab1!")
        self.assertFalse(ok)
        self.assertIn("8 characters", msg)

    def test_no_uppercase(self):
        ok, _ = SecurityManager.validate_password_strength("nouppercase1!")
        self.assertFalse(ok)

    def test_no_digit(self):
        ok, _ = SecurityManager.validate_password_strength("NoDigitHere!")
        self.assertFalse(ok)

    def test_no_special(self):
        ok, _ = SecurityManager.validate_password_strength("NoSpecial1a")
        self.assertFalse(ok)

    def test_strong_passes(self):
        ok, msg = SecurityManager.validate_password_strength("Secure@123")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


class TestValidation(unittest.TestCase):

    def test_valid_email(self):
        self.assertTrue(SecurityManager.validate_email("user@example.com"))

    def test_invalid_email(self):
        self.assertFalse(SecurityManager.validate_email("notanemail"))

    def test_valid_username(self):
        ok, _ = SecurityManager.validate_username("alice_99")
        self.assertTrue(ok)

    def test_short_username(self):
        ok, _ = SecurityManager.validate_username("ab")
        self.assertFalse(ok)

    def test_username_special_chars(self):
        ok, _ = SecurityManager.validate_username("user@name")
        self.assertFalse(ok)


class TestSessionToken(unittest.TestCase):

    def test_token_length(self):
        token, _ = SecurityManager.generate_session_token()
        self.assertEqual(len(token), 64)

    def test_token_unique(self):
        t1, _ = SecurityManager.generate_session_token()
        t2, _ = SecurityManager.generate_session_token()
        self.assertNotEqual(t1, t2)

    def test_session_valid(self):
        token, expires = SecurityManager.generate_session_token()
        self.assertTrue(SecurityManager.is_session_valid(
            {"token": token, "is_active": 1, "expires_at": expires}
        ))

    def test_inactive_session_invalid(self):
        token, expires = SecurityManager.generate_session_token()
        self.assertFalse(SecurityManager.is_session_valid(
            {"token": token, "is_active": 0, "expires_at": expires}
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
