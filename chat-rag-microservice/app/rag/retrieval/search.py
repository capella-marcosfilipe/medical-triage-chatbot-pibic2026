"""Similarity search helpers for runtime RAG retrieval."""
from __future__ import annotations

from typing import Sequence


def similarity_search(query: str, chunks: Sequence[str], top_k: int = 3) -> list[str]:
    """Return the most relevant chunks for a query.

    Placeholder implementation for the future vector search backend.
    """
    if not query or not chunks:
        return []
    return list(chunks[:top_k])
