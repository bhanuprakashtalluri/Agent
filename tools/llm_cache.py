"""Helpers for caching tool outputs, LLM responses and SQL query results.

Provides a small shared CacheManager instance, a generic `cached_tool` decorator
that can be applied to any tool function, and the existing helpers for
LLM invokes and SQL query caching. The decorator builds a stable key from the
function name and its args/kwargs using JSON + SHA256.
"""
from __future__ import annotations

import hashlib
import json
import functools
import inspect
from typing import Any, Callable, Optional, Tuple

from .cache_manager import CacheManager
from .query_store import DEFAULT_QUERY_STORE, QueryStore
from .in_memory_cache import DEFAULT_IN_MEMORY_CACHE
from .embeddings_cache import DEFAULT_EMBEDDINGS_CACHE


# Shared cache instance for the tools module
DEFAULT_CACHE = CacheManager()


def _make_key(parts: list) -> str:
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, (dict, list, tuple)):
            s = json.dumps(p, sort_keys=True, ensure_ascii=False)
        else:
            s = str(p)
        h.update(s.encode("utf-8"))
        h.update(b"\x1e")
    return h.hexdigest()


def cached_tool(ttl_seconds: Optional[int] = None, cache_type: str = "tool", write_to_query_store: bool = False):
    """Decorator to cache the return value of a tool function.

    Usage:
        @cached_tool(ttl_seconds=300, cache_type='visit_web')
        def visit_web(url: str) -> str: ...

    The decorator constructs a key as: {func.__name__} + args + kwargs.
    It uses DEFAULT_CACHE by default but allows callers to pass a different
    CacheManager instance via keyword arg `cache` when invoking the function.
    """

    def decorator(func: Callable):
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # allow explicit cache override
            cache: CacheManager = kwargs.pop("cache", DEFAULT_CACHE)
            # allow optional query_store override
            query_store: Optional[QueryStore] = kwargs.pop("query_store", None)
            effective_ttl = kwargs.pop("ttl_seconds", ttl_seconds)

            try:
                bound = sig.bind_partial(*args, **kwargs)
                bound.apply_defaults()
                key_parts = [func.__name__]
                for name, val in bound.arguments.items():
                    # Skip non-serializable arguments like objects that are likely
                    # to be a model instance; instead, include their repr or id
                    try:
                        json.dumps(val)
                        key_parts.append({name: val})
                    except Exception:
                        # Fall back to string repr
                        key_parts.append({name: repr(val)})

                key = _make_key(key_parts)

                def provider():
                    return func(*args, **kwargs)

                # Use 'tool' + func name as namespace by default
                ns = f"{cache_type}_{func.__name__}" if cache_type else func.__name__
                result = cache.get_or_set(ns, key, provider, ttl_seconds=effective_ttl)

                # decide which query_store to use: explicit override, or decorator-level flag
                try:
                    qs = query_store
                    if qs is None and write_to_query_store:
                        qs = DEFAULT_QUERY_STORE
                    if qs is not None:
                        # store bytes: JSON payload with minimal metadata
                        payload = json.dumps({"tool": func.__name__, "key": key, "result": result}).encode("utf-8")
                        qs.set(ns, key, payload, ttl_seconds=effective_ttl)
                except Exception:
                    # best-effort; ignore errors writing to query store
                    pass

                return result

            except Exception as e:
                # On cache-related or key-building errors, fallback to direct call
                try:
                    return func(*args, **kwargs)
                except Exception:
                    # Re-raise original error for visibility
                    raise

        return wrapper

    return decorator


def cached_invoke(
    model: Any,
    prompt: str,
    cache: Optional[CacheManager] = None,
    cache_type: str = "llm_response",
    ttl_seconds: Optional[int] = 3600,
    model_name: Optional[str] = None,
) -> str:
    """Invoke an LLM model with caching. Returns the text content.

    If `cache` is None the DEFAULT_CACHE is used.
    """
    if cache is None:
        cache = DEFAULT_CACHE

    key = _make_key([model_name or getattr(model, "model", "default"), prompt])

    # hot in-memory layer first
    hot = DEFAULT_IN_MEMORY_CACHE.get(key)
    if hot is not None:
        return hot

    def provider():
        resp = model.invoke(prompt)
        if hasattr(resp, "content"):
            return resp.content
        return str(resp)

    result = cache.get_or_set(cache_type, key, provider, ttl_seconds=ttl_seconds)
    try:
        DEFAULT_IN_MEMORY_CACHE.set(key, result, ttl_seconds)
    except Exception:
        pass
    return result


def cached_sql_query(
    sql: str,
    executor: Callable[[], Tuple[list, list]],
    cache: Optional[CacheManager] = None,
    cache_type: str = "sql",
    ttl_seconds: Optional[int] = 300,
) -> Tuple[list, list]:
    """Cache results of a SQL executor. Executor should return (columns, rows).

    We key by the SQL string. If `cache` is None the DEFAULT_CACHE is used.
    """
    if cache is None:
        cache = DEFAULT_CACHE

    key = _make_key([sql])

    # hot in-memory first
    hot = DEFAULT_IN_MEMORY_CACHE.get(key)
    if hot is not None:
        data = hot
    else:
        def provider():
            cols, rows = executor()
            # store as a JSON-serializable tuple
            return {"cols": cols, "rows": rows}

        data = cache.get_or_set(cache_type, key, provider, ttl_seconds=ttl_seconds)
        try:
            DEFAULT_IN_MEMORY_CACHE.set(key, data, ttl_seconds)
        except Exception:
            pass
    # data should be a dict with cols and rows
    if isinstance(data, dict) and "cols" in data and "rows" in data:
        return data["cols"], data["rows"]
    # fallback if stored differently
    return [], []


def get_or_set_embedding(content: str, model_name: str, provider: callable, config: Optional[dict] = None):
    """Return embedding vector either from embeddings cache or by calling provider().

    - content: the text to embed
    - model_name: identifier for the embedding model
    - provider: callable that returns the embedding vector
    - config: optional embedding config used in key
    """
    # try hot in-memory first
    key = _make_key([model_name, content, json.dumps(config or {}, sort_keys=True)])
    hot = DEFAULT_IN_MEMORY_CACHE.get(key)
    if hot is not None:
        return hot

    # try persistent embeddings cache
    stored = DEFAULT_EMBEDDINGS_CACHE.get(content, model_name, config=config)
    if stored is not None:
        try:
            DEFAULT_IN_MEMORY_CACHE.set(key, stored, None)
        except Exception:
            pass
        return stored

    # compute and store
    vector = provider()
    try:
        DEFAULT_EMBEDDINGS_CACHE.set(content, model_name, vector, config=config)
    except Exception:
        pass
    try:
        DEFAULT_IN_MEMORY_CACHE.set(key, vector, None)
    except Exception:
        pass
    return vector
