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
        print(f"\n[CacheManager.set] Input: cache_type={cache_type}, key={key}, value={value}")
        data = pickle.dumps(value)
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO cache (type, key, value) VALUES (?, ?, ?)", (cache_type, key, data))
            conn.commit()
        print(f"[CacheManager.set] Value set for type={cache_type}, key={key}")

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        print(f"\n[CacheManager.get] Input: cache_type={cache_type}, key={key}")
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM cache WHERE type=? AND key=?", (cache_type, key))
            row = c.fetchone()
            if row:
                value = pickle.loads(row[0])
                print(f"[CacheManager.get] Output: {value}")
                return value
        print(f"[CacheManager.get] Output: None")
        return None

    def delete(self, cache_type: str, key: str):
        print(f"\n[CacheManager.delete] Input: cache_type={cache_type}, key={key}")
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cache WHERE type=? AND key=?", (cache_type, key))
            conn.commit()
        print(f"[CacheManager.delete] Deleted value for type={cache_type}, key={key}")

    def clear(self, cache_type: Optional[str] = None):
        print(f"\n[CacheManager.clear] Input: cache_type={cache_type}")
        with self._lock, sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if cache_type:
                c.execute("DELETE FROM cache WHERE type=?", (cache_type,))
            else:
                c.execute("DELETE FROM cache")
            conn.commit()
        print(f"[CacheManager.clear] Cleared cache for type={cache_type if cache_type else 'ALL'}")

# Usage:
# cache = CacheManager()
# cache.set('llm_response', 'some_query', response)
# cache.get('llm_response', 'some_query')
# cache.set('vector', 'doc_id', vector_data)
# cache.get('vector', 'doc_id')
