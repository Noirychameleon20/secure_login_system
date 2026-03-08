"""
security.py
===========
Cryptographic operations:
  - PBKDF2-HMAC-SHA256 password hashing
  - Constant-time password verification (anti-timing attack)
  - Cryptographic session token generation
  - Password strength & input validation
  - Brute-force lockout logic
"""

import hashlib
import hmac
import secrets
import re
import time
from datetime import datetime


class SecurityManager:
    """
    Handles all cryptographic and validation operations.
    Uses PBKDF2-HMAC-SHA256 with 260,000 iterations (OWASP 2023 recommendation).
    """

    MAX_ATTEMPTS   = 5
    LOCKOUT_WINDOW = 300   # seconds (5 minutes)
    SESSION_TTL    = 3600  # seconds (1 hour)
    ITERATIONS     = 260_000
    HASH_ALGO      = "sha256"

    # ── Password hashing ─────────────────────

    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generate a cryptographically secure random salt (hex string)."""
        return secrets.token_hex(length)

    @classmethod
    def hash_password(cls, password: str, salt: str) -> str:
        """
        Hash a password using PBKDF2-HMAC-SHA256.
        Returns a hex-encoded digest string.
        """
        dk = hashlib.pbkdf2_hmac(
            cls.HASH_ALGO,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            cls.ITERATIONS
        )
        return dk.hex()

    @classmethod
    def verify_password(cls, password: str, salt: str,
                        stored_hash: str) -> bool:
        """
        Verify a password using constant-time comparison.
        Prevents timing attacks via hmac.compare_digest().
        """
        candidate = cls.hash_password(password, salt)
        return hmac.compare_digest(candidate, stored_hash)

    # ── Validation ───────────────────────────

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Enforce password policy:
        - Min 8 characters
        - At least one uppercase, lowercase, digit, special character
        Returns (is_valid, error_message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain an uppercase letter."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain a lowercase letter."
        if not re.search(r"\d", password):
            return False, "Password must contain a digit."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain a special character."
        return True, ""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic regex email format check."""
        return bool(re.match(r"^[\w.\-+]+@[\w\-]+\.[a-zA-Z]{2,}$", email))

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Username rules: 3–20 chars, alphanumeric + underscore only.
        Returns (is_valid, error_message).
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        if len(username) > 20:
            return False, "Username must be at most 20 characters."
        if not re.match(r"^\w+$", username):
            return False, "Username can only contain letters, digits, underscores."
        return True, ""

    # ── Lockout logic ────────────────────────

    @classmethod
    def check_lockout(cls, user: dict) -> tuple[bool, str]:
        """
        Check if user account is locked.
        Auto-unlocks after LOCKOUT_WINDOW seconds.
        Returns (is_locked, message). Message 'auto_unlock' means caller
        should reset the user's failed attempts in DB.
        """
        if not user["is_locked"]:
            return False, ""

        last_failed = user.get("last_failed")
        if last_failed:
            elapsed = time.time() - datetime.fromisoformat(
                last_failed).timestamp()
            if elapsed > cls.LOCKOUT_WINDOW:
                return False, "auto_unlock"

        return True, (
            f"Account locked after {cls.MAX_ATTEMPTS} failed attempts. "
            f"Try again in {cls.LOCKOUT_WINDOW // 60} minutes."
        )

    # ── Session token ────────────────────────

    @classmethod
    def generate_session_token(cls) -> tuple[str, str]:
        """
        Generate a secure session token.
        Returns (token_hex_64, expires_at_iso_string).
        """
        token      = secrets.token_hex(32)
        expires_at = datetime.fromtimestamp(
            time.time() + cls.SESSION_TTL
        ).isoformat()
        return token, expires_at

    @classmethod
    def is_session_valid(cls, session: dict) -> bool:
        """Return True if session exists, is active, and not expired."""
        if not session or not session["is_active"]:
            return False
        return datetime.now() < datetime.fromisoformat(session["expires_at"])
