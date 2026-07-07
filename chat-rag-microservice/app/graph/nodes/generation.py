"""Generation nodes that call the LLM layer."""
from __future__ import annotations

from app.graph.state import ConversationState


def generate_reply(state: ConversationState) -> ConversationState:
    """Generate the assistant reply from the current state.

    Placeholder implementation for the LLM integration point.
    """
    return state