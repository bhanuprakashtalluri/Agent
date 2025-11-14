"""Simple in-memory LRU cache wrapper using cachetools.

Provides a tiny API: get(key), set(key, value, ttl), get_or_set(key, provider, ttl)
"""
from cachetools import TTLCache
import threading
from typing import Any, Callable, Optional


class InMemoryCache:
    def __init__(self, maxsize: int = 1024, default_ttl: int = 300):
        self.cache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # cachetools' TTLCache uses a global ttl; ignore per-item ttl for simplicity
        with self.lock:
            self.cache[key] = value

    def get_or_set(self, key: str, provider: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        v = self.get(key)
        if v is not None:
            return v
        v = provider()
        try:
            self.set(key, v, ttl)
        except Exception:
            pass
        return v


DEFAULT_IN_MEMORY_CACHE = InMemoryCache()
