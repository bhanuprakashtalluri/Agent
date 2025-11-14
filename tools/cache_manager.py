from __future__ import annotations

import os
import sqlite3
import threading
import pickle
import time
from typing import Any, Optional, Callable, Iterable, List, Tuple
try:
    import msgpack
    _HAS_MSGPACK = True
except Exception:
    msgpack = None
    _HAS_MSGPACK = False


class CacheManager:
    def __init__(self, db_path: str = "cache/cache.db") -> None:
        self.db_path = db_path
        # ensure directory exists
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Create table if missing (best-effort)
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    type TEXT,
                    key TEXT,
                    value BLOB,
                    format TEXT DEFAULT 'pickle',
                    timestamp INTEGER DEFAULT (strftime('%s','now')),
                    expires_at INTEGER DEFAULT NULL,
                    last_accessed INTEGER DEFAULT (strftime('%s','now')),
                    PRIMARY KEY (type, key)
                )
                """
            )
            conn.commit()

            # Ensure migration: if older schema missing columns, add them
            try:
                c.execute("PRAGMA table_info(cache)")
                cols = [row[1] for row in c.fetchall()]
                if 'expires_at' not in cols:
                    c.execute("ALTER TABLE cache ADD COLUMN expires_at INTEGER DEFAULT NULL")
                if 'last_accessed' not in cols:
                    c.execute("ALTER TABLE cache ADD COLUMN last_accessed INTEGER DEFAULT (strftime('%s','now'))")
                if 'format' not in cols:
                    c.execute("ALTER TABLE cache ADD COLUMN format TEXT DEFAULT 'pickle'")
                conn.commit()
            except Exception:
                # best-effort migration; if it fails, continue
                pass

    def set(self, cache_type: str, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store a value with optional TTL (seconds)."""
        now = int(time.time())
        expires_at = (now + int(ttl_seconds)) if ttl_seconds is not None else None
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Inspect table columns and build a compatible REPLACE statement
            c.execute("PRAGMA table_info(cache)")
            cols = [r[1] for r in c.fetchall()]

            # Decide serialization based on whether 'format' column exists
            if 'format' in cols and _HAS_MSGPACK:
                try:
                    blob = msgpack.packb(value, use_bin_type=True)
                    fmt = 'msgpack'
                except Exception:
                    blob = pickle.dumps(value)
                    fmt = 'pickle'
            else:
                # older schema or no msgpack: use pickle for compatibility
                blob = pickle.dumps(value)
                fmt = 'pickle'

            # columns we may provide
            all_cols = ["type", "key", "value", "format", "timestamp", "expires_at", "last_accessed"]
            use_cols = [cname for cname in all_cols if cname in cols]
            placeholders = ", ".join(["?"] * len(use_cols))
            col_list = ", ".join(use_cols)
            values = []
            for cname in use_cols:
                if cname == 'type':
                    values.append(cache_type)
                elif cname == 'key':
                    values.append(key)
                elif cname == 'value':
                    values.append(blob)
                elif cname == 'format':
                    values.append(fmt)
                elif cname == 'timestamp':
                    values.append(now)
                elif cname == 'expires_at':
                    values.append(expires_at)
                elif cname == 'last_accessed':
                    values.append(now)

            stmt = f"REPLACE INTO cache ({col_list}) VALUES ({placeholders})"
            c.execute(stmt, tuple(values))
            conn.commit()

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """Return value if present and not expired, else None."""
        now = int(time.time())
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT value, expires_at, format FROM cache WHERE type=? AND key=?", (cache_type, key))
                row = c.fetchone()
            except sqlite3.OperationalError:
                # Older schema without 'format' column
                c.execute("SELECT value, expires_at FROM cache WHERE type=? AND key=?", (cache_type, key))
                row = c.fetchone()
                if row:
                    # append default format
                    row = (row[0], row[1], 'pickle')
            if not row:
                return None
            value_blob, expires_at, fmt = row
            if expires_at is not None and expires_at <= now:
                # expired: remove and return None
                c.execute("DELETE FROM cache WHERE type=? AND key=?", (cache_type, key))
                conn.commit()
                return None
            # update last_accessed if column exists
            try:
                c.execute("PRAGMA table_info(cache)")
                cols = [r[1] for r in c.fetchall()]
                if 'last_accessed' in cols:
                    c.execute("UPDATE cache SET last_accessed=? WHERE type=? AND key=?", (now, cache_type, key))
                    conn.commit()
            except Exception:
                # best-effort; ignore
                pass
            try:
                if fmt == 'msgpack' and _HAS_MSGPACK:
                    return msgpack.unpackb(value_blob, raw=False)
                else:
                    return pickle.loads(value_blob)
            except Exception:
                return None

    def get_or_set(self, cache_type: str, key: str, provider: Callable[[], Any], ttl_seconds: Optional[int] = None) -> Any:
        """Return cached value or compute via provider and cache result."""
        val = self.get(cache_type, key)
        if val is not None:
            return val
        value = provider()
        try:
            self.set(cache_type, key, value, ttl_seconds=ttl_seconds)
        except Exception:
            # don't raise on caching error
            pass
        return value

    def delete(self, cache_type: str, key: str) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cache WHERE type=? AND key=?", (cache_type, key))
            conn.commit()

    def clear(self, cache_type: Optional[str] = None) -> None:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("DELETE FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("DELETE FROM cache")
            conn.commit()

    def keys(self, cache_type: Optional[str] = None) -> List[str]:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("SELECT key FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("SELECT type || ':' || key FROM cache")
            rows = c.fetchall()
            return [r[0] for r in rows]

    def prune(self, remove_all_expired: bool = True, keep_most_recent: Optional[int] = None) -> None:
        """Prune expired entries and optionally keep only the most recent N entries.

        - remove_all_expired: deletes entries whose expires_at <= now
        - keep_most_recent: keeps only this many entries (by last_accessed) across all types
        """
        now = int(time.time())
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if remove_all_expired:
                c.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at<=?", (now,))
            if keep_most_recent is not None:
                c.execute("SELECT COUNT(*) FROM cache")
                total = c.fetchone()[0]
                if total > keep_most_recent:
                    to_remove = total - keep_most_recent
                    c.execute(
                        "SELECT type, key FROM cache ORDER BY last_accessed ASC LIMIT ?",
                        (to_remove,)
                    )
                    rows: List[Tuple[str, str]] = c.fetchall()
                    for t, k in rows:
                        c.execute("DELETE FROM cache WHERE type=? AND key=?", (t, k))
            conn.commit()


__all__ = ["CacheManager"]
__all__ = ["CacheManager"]
