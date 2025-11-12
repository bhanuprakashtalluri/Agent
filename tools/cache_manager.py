import sqlite3
import threading
import pickle
from typing import Any, Optional

class CacheManager:
    def __init__(self, db_path: str = "cache/cache.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                type TEXT,
                key TEXT,
                value BLOB,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (type, key)
            )
            """)
            conn.commit()

    def set(self, cache_type: str, key: str, value: Any):
        data = pickle.dumps(value)
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO cache (type, key, value) VALUES (?, ?, ?)", (cache_type, key, data))
            conn.commit()

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM cache WHERE type=? AND key=?", (cache_type, key))
            row = c.fetchone()
            if row:
                return pickle.loads(row[0])
        return None

    def delete(self, cache_type: str, key: str):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cache WHERE type=? AND key=?", (cache_type, key))
            conn.commit()

    def clear(self, cache_type: Optional[str] = None):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("DELETE FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("DELETE FROM cache")
            conn.commit()

# Usage:
# cache = CacheManager()
# cache.set('llm_response', 'some_query', response)
# cache.get('llm_response', 'some_query')
# cache.set('vector', 'doc_id', vector_data)
# cache.get('vector', 'doc_id')
