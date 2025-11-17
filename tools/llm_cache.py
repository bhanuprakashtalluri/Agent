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
from .token_utils import estimate_tokens, truncate_to_tokens


# Global defaults per model provider: (max_input_tokens, max_output_tokens)
DEFAULT_MODEL_TOKEN_LIMITS = {
    "ChatOllama": (1000, 250),
    "ChatGroq": (2000, 500),
}


def _detect_model_provider(model: Any, model_name: Optional[str] = None) -> Optional[str]:
    """Try to infer the model provider key (e.g., 'ollama' or 'chatgroq').

    This uses class name and model_name heuristics and is intentionally
    permissive to handle different wrappers.
    """
    try:
        cls_name = getattr(model, "__class__", type(model)).__name__ or ""
        mn = (model_name or getattr(model, "model", "") or "").lower()
        cls = cls_name.lower()
        if "ollama" in cls or "ollama" in mn or "qwen" in mn:
            return "ChatOllama"
        if "groq" in cls or "groq" in mn or "chatgroq" in mn:
            return "ChatGroq"
    except Exception:
        pass
    return None


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
    """Cache the result of a tool function.

    Args:
        ttl_seconds: Expiry for the cached entry. ``None`` keeps it forever.
        cache_type: Namespace prefix for stored keys.
        write_to_query_store: Persist successful results to the query store.

    Returns:
        Decorator that can be applied to any callable with serializable
        arguments.
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
    query_store: Optional[QueryStore] = None,
    max_input_tokens: Optional[int] = None,
    max_output_tokens: Optional[int] = None,
    allow_function_calls: bool = False,
) -> str:
    """Invoke an LLM model with caching and optional token constraints.

    Args:
        model: Chat model exposing an ``invoke`` method.
        prompt: Prompt text to send to the model.
        cache: Cache manager instance to reuse.
        cache_type: Namespace for stored responses.
        ttl_seconds: Expiry for cached entries.
        model_name: Optional descriptive name used for keying and heuristics.
        query_store: Optional secondary persistence for analytics.
        max_input_tokens: Soft limit for prompt length.
        max_output_tokens: Soft limit for response length.
        allow_function_calls: If ``False`` instructs the model to avoid tools.

    Returns:
        Text content produced by the model, truncated if necessary.
    """
    if cache is None:
        cache = DEFAULT_CACHE

    # If limits not provided, apply provider-specific defaults
    if max_input_tokens is None or max_output_tokens is None:
        prov = _detect_model_provider(model, model_name)
        if prov and prov in DEFAULT_MODEL_TOKEN_LIMITS:
            inp_def, out_def = DEFAULT_MODEL_TOKEN_LIMITS[prov]
            if max_input_tokens is None:
                max_input_tokens = inp_def
            if max_output_tokens is None:
                max_output_tokens = out_def

    # If function calls are not allowed, prepend an explicit instruction to the prompt
    if not allow_function_calls:
        no_call_instruction = "IMPORTANT: Do not call any external functions or tools. Return the answer directly as plain text."
        if no_call_instruction not in prompt:
            prompt = no_call_instruction + "\n\n" + prompt

    # Optionally truncate the prompt to fit input token budget
    if max_input_tokens is not None:
        prompt = truncate_to_tokens(prompt, max_input_tokens, model_name)

    key = _make_key([model_name or getattr(model, "model", "default"), prompt])

    # hot in-memory layer first
    hot = DEFAULT_IN_MEMORY_CACHE.get(key)
    if hot is not None:
        return hot

    def provider():
        try:
            resp = model.invoke(prompt)
        except Exception as e:
            # If the model failed due to attempted function calling (tool_use_failed / failed_generation),
            # retry with an explicit instruction to avoid function calls. If retry fails, re-raise.
            se = str(e)
            if 'failed_generation' in se or 'tool_use_failed' in se or 'Failed to call a function' in se:
                try:
                    fallback_prompt = (
                        prompt
                        + "\n\nIMPORTANT: Do not call any external functions or tools. Return the answer directly as plain text."
                    )
                    resp = model.invoke(fallback_prompt)
                except Exception:
                    # re-raise original exception to avoid caching an error string
                    raise
            else:
                # Not a function-call failure; re-raise
                raise

        if hasattr(resp, "content"):
            content = resp.content
        else:
            # If the response is some other object (dict/string), try to extract text
            try:
                # If it's a dict-like with 'content' or 'text'
                if isinstance(resp, dict):
                    content = resp.get('content') or resp.get('text') or str(resp)
                else:
                    content = str(resp)
            except Exception:
                content = str(resp)
        # If the model produced more tokens than allowed, truncate the output
        if max_output_tokens is not None:
            est = estimate_tokens(content, model_name)
            if est > max_output_tokens:
                try:
                    content = truncate_to_tokens(content, max_output_tokens, model_name)
                except Exception:
                    # Best-effort: fallback to slice
                    content = content[: max_output_tokens * 4]
        return content

    result = cache.get_or_set(cache_type, key, provider, ttl_seconds=ttl_seconds)
    try:
        DEFAULT_IN_MEMORY_CACHE.set(key, result, ttl_seconds)
    except Exception:
        pass
    # write to query_store if provided
    try:
        qs = query_store
        if qs is not None:
            payload = json.dumps({"model": model_name or getattr(model, "model", "default"), "prompt": prompt, "key": key, "result": result}).encode("utf-8")
            qs.set(cache_type, key, payload, ttl_seconds=ttl_seconds)
    except Exception:
        pass
    return result


def cached_sql_query(
    sql: str,
    executor: Callable[[], Tuple[list, list]],
    cache: Optional[CacheManager] = None,
    cache_type: str = "sql",
    ttl_seconds: Optional[int] = 300,
    query_store: Optional[QueryStore] = None,
) -> Tuple[list, list]:
    """Cache results of an executor that runs a SQL statement.

    Args:
        sql: SQL string used as the cache key.
        executor: Callable returning ``(columns, rows)`` when executed.
        cache: Cache manager instance to reuse.
        cache_type: Namespace for the stored payload.
        ttl_seconds: Expiry for cached results.
        query_store: Optional secondary persistence for analytics.

    Returns:
        Tuple of columns and rows, aligned with the executor's output.
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
    # write to query_store if provided
    try:
        qs = query_store
        if qs is not None:
            payload = json.dumps({"sql": sql, "key": key, "result": data}).encode("utf-8")
            qs.set(cache_type, key, payload, ttl_seconds=ttl_seconds)
    except Exception:
        pass
    # data should be a dict with cols and rows
    if isinstance(data, dict) and "cols" in data and "rows" in data:
        return data["cols"], data["rows"]
    # fallback if stored differently
    return [], []


def get_or_set_embedding(content: str, model_name: str, provider: callable, config: Optional[dict] = None):
    """Return an embedding vector from cache or compute a fresh copy.

    Args:
        content: Text that was embedded.
        model_name: Identifier of the embedding model.
        provider: Callable invoked when the cache misses.
        config: Optional serializer configuration that influences the key.

    Returns:
        Embedding vector produced by *provider* or loaded from cache.
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
