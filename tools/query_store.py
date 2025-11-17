"""Simple SQLite-backed store for persisting tool query payloads."""

import os
import sqlite3
import time
from typing import Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DB_DIR, exist_ok=True)
QUERY_DB_PATH = os.path.join(DB_DIR, 'query_store.sqlite3')


class QueryStore:
    """Simple SQLite-backed store for caching queries and tool responses.

    Schema:
        queries(id INTEGER PRIMARY KEY, tool TEXT, key TEXT, payload BLOB, created_at INTEGER, expires_at INTEGER NULL)
    """

    def __init__(self, db_path: Optional[str] = None):
        """Create a store pointing at *db_path* (defaults to the project DB)."""
        self.db_path = db_path or QUERY_DB_PATH
        self._init_db()

    def _conn(self):
        """Return a new SQLite connection to the configured database."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Ensure the required schema exists."""
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY,
                tool TEXT NOT NULL,
                key TEXT NOT NULL,
                payload BLOB,
                created_at INTEGER NOT NULL,
                expires_at INTEGER
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tool_key ON queries(tool, key);")
        conn.commit()
        conn.close()

    def set(self, tool: str, key: str, payload: bytes, ttl_seconds: Optional[int] = None):
        """Persist *payload* for a tool/key pair with an optional expiry."""
        now = int(time.time())
        expires = int(now + ttl_seconds) if ttl_seconds else None
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO queries (tool, key, payload, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (tool, key, payload, now, expires),
        )
        conn.commit()
        conn.close()

    def get(self, tool: str, key: str) -> Optional[bytes]:
        """Return the newest payload for *tool* and *key* if not expired."""
        now = int(time.time())
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT payload, expires_at FROM queries WHERE tool=? AND key=? ORDER BY id DESC LIMIT 1", (tool, key))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        payload, expires_at = row
        if expires_at and expires_at < now:
            return None
        return payload

    def clear(self):
        """Remove all stored query rows."""
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM queries;")
        conn.commit()
        conn.close()


DEFAULT_QUERY_STORE = QueryStore()
