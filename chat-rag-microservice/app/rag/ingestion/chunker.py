"""Chunking utilities for offline RAG preparation."""
from __future__ import annotations

from typing import Iterable


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Split text into overlapping chunks.

    Placeholder implementation to be replaced by the project-specific chunker.
    """
    if not text:
        return []
    return [text[i : i + chunk_size] for i in range(0, len(text), max(chunk_size - overlap, 1))]
