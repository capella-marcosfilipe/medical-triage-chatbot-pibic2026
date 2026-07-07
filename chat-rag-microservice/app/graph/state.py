"""Conversation state for LangGraph workflows."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    """Mutable state carried through the conversation graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    chat_id: str
