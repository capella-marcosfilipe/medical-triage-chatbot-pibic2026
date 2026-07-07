"""Index building utilities for offline RAG workflows."""
from __future__ import annotations

from app.rag.indexing.embedder import Embedder


def build_index(chunks: list[str], embedder: Embedder) -> dict[str, object]:
    """Create an in-memory index payload for persistence."""
    vectors = embedder.embed_documents(chunks)
    return {
        "chunks": chunks,
        "vectors": vectors,
    }
