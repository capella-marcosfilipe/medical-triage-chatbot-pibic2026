"""Vector store adapters for persistent similarity search."""
from __future__ import annotations

from typing import Protocol


class VectorStore(Protocol):
    """Protocol for vector store implementations."""

    def upsert(self, chunks: list[str], vectors: list[list[float]]) -> None:
        """Persist an indexed corpus."""
        ...

    def search(self, query_vector: list[float], top_k: int = 3) -> list[str]:
        """Search for similar chunks."""
        ...
