"""Routing nodes for conversation flow decisions."""
from __future__ import annotations

from app.graph.state import ConversationState


def route_conversation(state: ConversationState) -> str:
    """Choose the next node or branch.

    Placeholder for future routing logic.
    """
    return "retrieve"
