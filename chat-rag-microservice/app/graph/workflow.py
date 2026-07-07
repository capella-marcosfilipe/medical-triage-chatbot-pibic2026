"""Graph assembly for the chat orchestration layer."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.state import ConversationState


def build_chat_graph():
    """Build the LangGraph workflow.

    This module stays intentionally thin so nodes can evolve independently.
    """
    builder = StateGraph(ConversationState)
    builder.add_edge(START, END)
    return builder.compile()
