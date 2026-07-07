"""Document loading utilities for offline RAG ingestion."""
from __future__ import annotations

from pathlib import Path


def load_text(path: str | Path) -> str:
    """Load a UTF-8 text document from disk."""
    return Path(path).read_text(encoding="utf-8")
