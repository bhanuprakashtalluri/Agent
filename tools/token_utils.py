"""Token utilities for estimating and constraining language-model inputs.

When :mod:`tiktoken` is available the helpers use the model-specific
encoders for accurate counts and truncation. Otherwise they fall back to a
conservative four characters per token heuristic so the caller can still
enforce roughly correct limits.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    import tiktoken  # type: ignore
    _HAS_TIKTOKEN = True
except Exception:
    tiktoken = None
    _HAS_TIKTOKEN = False


def estimate_tokens(text: str, model_name: Optional[str] = None) -> int:
    """Estimate how many tokens *text* would consume for a given model.

    Args:
        text: Raw content to measure.
        model_name: Optional model identifier passed to :mod:`tiktoken`.

    Returns:
        Approximate token count using the model encoder when available and a
        four-characters-per-token fallback otherwise.
    """
    if not text:
        return 0
    if _HAS_TIKTOKEN:
        try:
            enc = tiktoken.encoding_for_model(model_name) if model_name else tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            logging.debug("tiktoken encode failed, falling back to heuristic")
    # conservative fallback: 4 chars per token average
    return max(1, len(text) // 4)


def truncate_to_tokens(text: str, max_tokens: int, model_name: Optional[str] = None) -> str:
    """Return *text* trimmed so the result is at most *max_tokens* long.

    Args:
        text: Text to truncate.
        max_tokens: Desired upper bound on the number of tokens.
        model_name: Optional model identifier for :mod:`tiktoken`.

    Returns:
        A best-effort truncation that keeps token boundaries when
        :mod:`tiktoken` is installed and otherwise trims on character
        boundaries, favoring whitespace splits.
    """
    if not text or max_tokens is None:
        return text
    if max_tokens <= 0:
        return ""
    if _HAS_TIKTOKEN:
        try:
            enc = tiktoken.encoding_for_model(model_name) if model_name else tiktoken.get_encoding("cl100k_base")
            tokens = enc.encode(text)
            truncated = enc.decode(tokens[:max_tokens])
            return truncated
        except Exception:
            logging.debug("tiktoken truncate failed, falling back to heuristic")
    # Fallback: truncate by characters (conservative)
    approx_chars = max_tokens * 4
    if len(text) <= approx_chars:
        return text
    # Try not to cut mid-word: cut at last whitespace before the limit
    candidate = text[:approx_chars]
    last_space = candidate.rfind(" ")
    if last_space > int(approx_chars * 0.6):
        return candidate[:last_space]
    return candidate
