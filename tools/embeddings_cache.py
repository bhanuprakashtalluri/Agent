"""Persistence for embeddings to avoid recomputing vectors for the same content.

Stores embeddings in the persistent CacheManager under namespace 'embeddings'.
Keying uses SHA256(content + model_name + config_json).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from .cache_manager import CacheManager


def _emb_key(content: str, model_name: str, config: Optional[dict] = None) -> str:
    parts = [content, model_name, json.dumps(config or {}, sort_keys=True, ensure_ascii=False)]
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode('utf-8'))
        h.update(b'\x1f')
    return h.hexdigest()


class EmbeddingsCache:
    def __init__(self, cache: Optional[CacheManager] = None):
        self.cache = cache or CacheManager()
        self.namespace = "embeddings"

    def get(self, content: str, model_name: str, config: Optional[dict] = None) -> Optional[Any]:
        key = _emb_key(content, model_name, config)
        return self.cache.get(self.namespace, key)

    def set(self, content: str, model_name: str, vector: Any, config: Optional[dict] = None) -> None:
        key = _emb_key(content, model_name, config)
        # embeddings can be large lists of floats; we rely on pickling
        self.cache.set(self.namespace, key, vector, ttl_seconds=None)

    def get_or_set(self, content: str, model_name: str, provider: callable, config: Optional[dict] = None):
        key = _emb_key(content, model_name, config)
        return self.cache.get_or_set(self.namespace, key, lambda: provider())


DEFAULT_EMBEDDINGS_CACHE = EmbeddingsCache()
