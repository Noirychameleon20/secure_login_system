"""
auth_service.py
===============
Business logic layer — orchestrates register, login,
logout, change password, and delete account operations.
Sits between the GUI and the core (Database + SecurityManager).
"""

from datetime import datetime
from core.database import Database
from core.security import SecurityManager


class AuthService:
    """
    Coordinates authentication workflows.
    All methods return (success: bool, message: str) or
    (success, message, token) for login.
    """

    def __init__(self, db: Database, sec: SecurityManager):
        self.db  = db
        self.sec = sec

    def register(self, username: str, email: str,
                 password: str) -> tuple[bool, str]:
        """Validate inputs, hash password, persist new user."""
        ok, msg = SecurityManager.validate_username(username)
        if not ok:
            return False, msg

        if not SecurityManager.validate_email(email):
            return False, "Invalid email address."

        ok, msg = SecurityManager.validate_password_strength(password)
        if not ok:
            return False, msg

        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password(password, salt)

        if not self.db.create_user(username, email, phash, salt):
            return False, "Username or email already exists."

        self.db.log_action(username, "REGISTER", "SUCCESS")
        return True, "Account created successfully!"

    def login(self, username: str,
              password: str) -> tuple[bool, str, str]:
        """
        Authenticate user. Returns (success, message, session_token).
        Token is empty string on failure.
        """
        user = self.db.get_user(username)
        if not user:
            self.db.log_action(username, "LOGIN", "FAIL", "User not found")
            return False, "Invalid username or password.", ""

        # ── Lockout check ────────────────────
        locked, reason = SecurityManager.check_lockout(user)
        if locked:
            self.db.log_action(username, "LOGIN", "BLOCKED", reason)
            return False, reason, ""
        if reason == "auto_unlock":
            self.db.reset_failed_attempts(username)
            user = self.db.get_user(username)

        # ── Password verification ────────────
        if not SecurityManager.verify_password(
                password, user["salt"], user["password_hash"]):
            attempts = user["failed_attempts"] + 1
            self.db.update_failed_attempts(
                username, attempts, datetime.now().isoformat()
            )
            if attempts >= SecurityManager.MAX_ATTEMPTS:
                self.db.lock_user(username)
                self.db.log_action(username, "LOGIN", "LOCKED",
                                   f"Locked after {attempts} attempts")
                return False, (
                    f"Too many failed attempts. Account locked for "
                    f"{SecurityManager.LOCKOUT_WINDOW // 60} minutes."
                ), ""
            remaining = SecurityManager.MAX_ATTEMPTS - attempts
            self.db.log_action(username, "LOGIN", "FAIL",
                                f"Wrong password, {remaining} left")
            return False, (
                f"Invalid username or password. "
                f"{remaining} attempt(s) remaining."
            ), ""

        # ── Success ──────────────────────────
        self.db.reset_failed_attempts(username)
        token, expires_at = SecurityManager.generate_session_token()
        self.db.create_session(user["id"], token, expires_at)
        self.db.log_action(username, "LOGIN", "SUCCESS")
        return True, f"Welcome back, {username}!", token

    def logout(self, token: str, username: str):
        """Invalidate session token."""
        self.db.invalidate_session(token)
        self.db.log_action(username, "LOGOUT", "SUCCESS")

    def change_password(self, username: str, old_pw: str,
                        new_pw: str) -> tuple[bool, str]:
        """Verify old password, enforce policy, update hash, kill sessions."""
        user = self.db.get_user(username)
        if not user:
            return False, "User not found."

        if not SecurityManager.verify_password(
                old_pw, user["salt"], user["password_hash"]):
            return False, "Current password is incorrect."

        ok, msg = SecurityManager.validate_password_strength(new_pw)
        if not ok:
            return False, msg

        if old_pw == new_pw:
            return False, "New password must differ from the current one."

        salt  = SecurityManager.generate_salt()
        phash = SecurityManager.hash_password(new_pw, salt)
        self.db.update_password(username, phash, salt)
        self.db.invalidate_all_sessions(user["id"])
        self.db.log_action(username, "CHANGE_PASSWORD", "SUCCESS")
        return True, "Password changed successfully. Please log in again."

    def delete_account(self, username: str,
                       password: str) -> tuple[bool, str]:
        """Confirm password then permanently delete user and sessions."""
        user = self.db.get_user(username)
        if not user:
            return False, "User not found."

        if not SecurityManager.verify_password(
                password, user["salt"], user["password_hash"]):
            return False, "Incorrect password."

        self.db.invalidate_all_sessions(user["id"])
        self.db.delete_user(username)
        self.db.log_action(username, "DELETE_ACCOUNT", "SUCCESS")
        return True, "Account deleted."
