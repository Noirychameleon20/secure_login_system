"""
database.py
===========
Handles all SQLite database operations.
Tables: users, sessions, audit_logs
"""

import sqlite3
from datetime import datetime


class Database:
    """Manages persistent storage using SQLite."""

    def __init__(self, db_path: str = "secure_login.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Create tables if they do not exist."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    username         TEXT    UNIQUE NOT NULL,
                    email            TEXT    UNIQUE NOT NULL,
                    password_hash    TEXT    NOT NULL,
                    salt             TEXT    NOT NULL,
                    created_at       TEXT    NOT NULL,
                    is_locked        INTEGER DEFAULT 0,
                    failed_attempts  INTEGER DEFAULT 0,
                    last_failed      TEXT    DEFAULT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    token       TEXT    UNIQUE NOT NULL,
                    created_at  TEXT    NOT NULL,
                    expires_at  TEXT    NOT NULL,
                    is_active   INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    username  TEXT NOT NULL,
                    action    TEXT NOT NULL,
                    status    TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details   TEXT DEFAULT ''
                )
            """)
            conn.commit()

    # ── User CRUD ────────────────────────────

    def create_user(self, username, email, password_hash, salt) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash, salt, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (username, email, password_hash, salt,
                     datetime.now().isoformat())
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username: str) -> dict | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        return dict(row) if row else None

    def get_all_users(self) -> list:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, username, email, created_at, is_locked, "
                "failed_attempts FROM users"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_failed_attempts(self, username, attempts, last_failed):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET failed_attempts=?, last_failed=? "
                "WHERE username=?",
                (attempts, last_failed, username)
            )
            conn.commit()

    def lock_user(self, username: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET is_locked=1 WHERE username=?", (username,)
            )
            conn.commit()

    def reset_failed_attempts(self, username: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET failed_attempts=0, is_locked=0, "
                "last_failed=NULL WHERE username=?", (username,)
            )
            conn.commit()

    def update_password(self, username, new_hash, new_salt):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash=?, salt=? WHERE username=?",
                (new_hash, new_salt, username)
            )
            conn.commit()

    def delete_user(self, username: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()

    # ── Session CRUD ─────────────────────────

    def create_session(self, user_id, token, expires_at) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO sessions (user_id, token, created_at, expires_at) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, token, datetime.now().isoformat(), expires_at)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_session(self, token: str) -> dict | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE token=? AND is_active=1",
                (token,)
            ).fetchone()
        return dict(row) if row else None

    def invalidate_session(self, token: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET is_active=0 WHERE token=?", (token,)
            )
            conn.commit()

    def invalidate_all_sessions(self, user_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET is_active=0 WHERE user_id=?", (user_id,)
            )
            conn.commit()

    # ── Audit log ────────────────────────────

    def log_action(self, username, action, status, details=""):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs (username, action, status, timestamp, details) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, action, status,
                 datetime.now().isoformat(), details)
            )
            conn.commit()

    def get_audit_logs(self, limit: int = 50) -> list:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        """No-op — connections are opened/closed per query. Exists for test compatibility."""
        pass
