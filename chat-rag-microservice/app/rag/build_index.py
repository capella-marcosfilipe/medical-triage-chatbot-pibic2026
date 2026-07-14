"""Populate the ChromaDB collection for the Manchester/Maringá knowledge base.

Reads the structured records produced by `extract_manchester_rules.py` and
indexes them with a local, multilingual sentence-embedding model (see
docs/RAG_KNOWLEDGE_BASE.md for why a local model was chosen over the NVIDIA
API for embeddings).

Run as a script (from chat-rag-microservice/):

    python -m app.rag.build_index

Safe to re-run: each record's ID is a deterministic hash of its content, so
`collection.upsert()` overwrites in place instead of duplicating entries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.infrastructure.settings import settings
from app.infrastructure.logger import logger
from app.rag.storage.manchester_repository import ManchesterRulesRepository

REPO_ROOT = Path(__file__).resolve().parents[2]


def _record_id(record: dict, position_in_group: int) -> str:
    """Deterministic ID so re-running this script upserts instead of duplicating.

    `position_in_group` (this record's index among same-fluxograma/same-cor
    records, in extraction order) disambiguates the rare case of the source
    PDF listing the same criterio text twice under one color (confirmed in
    "Queixas respiratórias"/VERMELHO: items 4 and 5 are both "Respiração
    inadequada" — a duplicate in the source document itself, kept faithfully
    per Tarefa 1's "não valide clinicamente, apenas extraia fielmente").
    """
    key = f"{record['fluxograma']}|{record['cor']}|{position_in_group}|{record['criterio']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _document_text(record: dict) -> str:
    """Concatenate fluxograma + criterio + descritor, per Tarefa 2."""
    return f"{record['fluxograma']} {record['criterio']} {record['descritor']}"


def build_index() -> int:
    rules_path = REPO_ROOT / settings.MANCHESTER_RULES_PATH
    if not rules_path.exists():
        raise SystemExit(
            f"{rules_path} não encontrado. Rode 'python -m app.rag.extract_manchester_rules' primeiro."
        )

    records = json.loads(rules_path.read_text(encoding="utf-8"))

    repository = ManchesterRulesRepository(
        chroma_path=REPO_ROOT / settings.MANCHESTER_CHROMA_PATH,
        collection_name=settings.MANCHESTER_COLLECTION_NAME,
        embedding_model=settings.MANCHESTER_EMBEDDING_MODEL,
    )

    group_counters: dict[tuple[str, str], int] = {}
    ids: list[str] = []
    for r in records:
        group_key = (r["fluxograma"], r["cor"])
        position_in_group = group_counters.get(group_key, 0)
        group_counters[group_key] = position_in_group + 1
        ids.append(_record_id(r, position_in_group))

    documents = [_document_text(r) for r in records]
    metadatas = [
        {
            "fluxograma": r["fluxograma"],
            "cor": r["cor"],
            "tempo_alvo": r["tempo_alvo"],
            "criterio": r["criterio"],
            "descritor": r["descritor"],
        }
        for r in records
    ]

    repository.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info(
        f"[build_index] {len(records)} registros indexados em '{settings.MANCHESTER_COLLECTION_NAME}' "
        f"({REPO_ROOT / settings.MANCHESTER_CHROMA_PATH})"
    )
    return len(records)


if __name__ == "__main__":
    total = build_index()
    print(f"{total} registros indexados em {settings.MANCHESTER_CHROMA_PATH}")
