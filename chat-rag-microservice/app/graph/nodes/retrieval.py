"""Retrieval nodes that fetch RAG context at runtime."""
from __future__ import annotations

from app.graph.state import ConversationState


def retrieve_context(state: ConversationState) -> ConversationState:
    """Attach retrieved context to the current state.

    Placeholder implementation for the RAG integration point.
    """
    return state