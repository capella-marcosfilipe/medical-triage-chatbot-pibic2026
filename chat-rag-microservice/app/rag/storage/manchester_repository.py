"""ChromaDB-backed repository for the Manchester/Maringá triage rules.

Centralizes all ChromaDB access for this knowledge base in one place, so
callers (the indexing script and the conversation service) depend on this
repository instead of each constructing a chromadb client and embedding
function directly. See docs/RAG_KNOWLEDGE_BASE.md.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import Embeddable, EmbeddingFunction, Metadata
from chromadb.utils import embedding_functions

from app.infrastructure.constants import CHROMA_DISTANCE_METRIC


class ManchesterRulesReader(Protocol):
    """Read-side interface consumed by LangGraphRAGService.

    Exists so the service can depend on this abstraction (constructor
    injection) instead of a concrete ChromaDB client, and so tests can pass
    in a fake reader without touching a real collection.
    """

    def query(self, text: str, top_k: int) -> list[Metadata]: ...


class ManchesterRulesRepository:
    """Owns the ChromaDB collection for the Manchester/Maringá knowledge base."""

    def __init__(self, chroma_path: str | Path, collection_name: str, embedding_model: str) -> None:
        self._chroma_path = Path(chroma_path)
        self._collection_name = collection_name
        self._embedding_model = embedding_model
        self._client: ClientAPI | None = None
        self._embedding_function: embedding_functions.SentenceTransformerEmbeddingFunction | None = None

    def _get_client(self) -> ClientAPI:
        if self._client is None:
            self._chroma_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._chroma_path))
        return self._client

    def _get_embedding_function(self):
        if self._embedding_function is None:
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self._embedding_model
            )
        return self._embedding_function

    def _get_collection(self, *, create: bool):
        """`create=True` (indexing) uses get_or_create; `create=False` (reads)
        uses get_collection, so a not-yet-built collection surfaces as an
        error instead of silently behaving like an empty collection."""
        client = self._get_client()
        embedding_function = cast(EmbeddingFunction[Embeddable], self._get_embedding_function())
        if create:
            return client.get_or_create_collection(
                name=self._collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": CHROMA_DISTANCE_METRIC},
            )
        return client.get_collection(name=self._collection_name, embedding_function=embedding_function)

    def upsert(self, ids: list[str], documents: list[str], metadatas: Sequence[Metadata]) -> None:
        """Create or overwrite records. Safe to call repeatedly with the same IDs."""
        collection = self._get_collection(create=True)
        collection.upsert(ids=ids, documents=documents, metadatas=list(metadatas))

    def query(self, text: str, top_k: int) -> list[Metadata]:
        """Return the top-k most similar rule records, as metadata dicts.

        Raises if the collection doesn't exist yet or the query otherwise
        fails. Callers that want a "no rules available" fallback instead of
        an exception (LangGraphRAGService) catch around this call.
        """
        collection = self._get_collection(create=False)
        result = collection.query(query_texts=[text], n_results=top_k)
        metadatas = result.get("metadatas") or [[]]
        return metadatas[0] if metadatas else []

    def count(self) -> int:
        return self._get_collection(create=False).count()
