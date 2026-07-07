"""Embedding adapters for offline RAG indexing."""
from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    """Protocol for embedding backends."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""
        ...
