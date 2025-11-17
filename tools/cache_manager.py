"""Persistent SQLite-backed cache used throughout the agent.

The cache stores values under a ``(type, key)`` composite primary key and
supports optional expiry, schema migrations, and basic pruning. Values are
serialized with :mod:`msgpack` when available and fall back to pickled bytes.
"""

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
    """Thread-safe key/value cache with optional TTL support."""

    def __init__(self, db_path: str = "cache/cache.db") -> None:
        """Create a cache pointing at *db_path* and initialize the schema."""
        self.db_path = db_path
        # ensure directory exists
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Create required tables and migrate older schemas when possible."""
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
        """Store *value* under ``(cache_type, key)`` with an optional TTL.

        Args:
            cache_type: Namespace for the cached entry (e.g., ``"tool"``).
            key: Unique key within the namespace.
            value: Serializable value to persist. Exceptions are ignored for
                safety so that failures are not cached.
            ttl_seconds: Optional time-to-live in seconds.
        """
        # Never cache exception objects — treat them as non-cacheable results.
        if isinstance(value, BaseException):
            return
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
        """Return the cached value when present and not expired."""
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

    def get_or_set(
        self,
        cache_type: str,
        key: str,
        provider: Callable[[], Any],
        ttl_seconds: Optional[int] = None,
    ) -> Any:
        """Return cached value or compute via *provider* and store the result.

        Args:
            cache_type: Namespace for the cached entry.
            key: Unique key within the namespace.
            provider: Callable returning the value when the cache misses.
            ttl_seconds: Optional TTL for the stored entry.

        Returns:
            Cached value or freshly computed value from *provider*.
        """
        val = self.get(cache_type, key)
        if val is not None:
            return val
        value = provider()
        # If provider returned an exception object, do not cache it; return directly.
        if isinstance(value, BaseException):
            return value
        try:
            self.set(cache_type, key, value, ttl_seconds=ttl_seconds)
        except Exception:
            # don't raise on caching error
            pass
        return value

    def delete(self, cache_type: str, key: str) -> None:
        """Remove a specific cache entry if it exists."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cache WHERE type=? AND key=?", (cache_type, key))
            conn.commit()

    def clear(self, cache_type: Optional[str] = None) -> None:
        """Remove all entries or all entries for *cache_type*."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("DELETE FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("DELETE FROM cache")
            conn.commit()

    def keys(self, cache_type: Optional[str] = None) -> List[str]:
        """Return stored keys optionally filtered by *cache_type*."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("SELECT key FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("SELECT type || ':' || key FROM cache")
            rows = c.fetchall()
            return [r[0] for r in rows]

    def prune(self, remove_all_expired: bool = True, keep_most_recent: Optional[int] = None) -> None:
        """Remove expired entries and optionally trim to *keep_most_recent*.

        Args:
            remove_all_expired: When ``True`` delete everything past ``expires_at``.
            keep_most_recent: If provided, keep only the most recently accessed
                ``N`` entries across all cache types.
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
