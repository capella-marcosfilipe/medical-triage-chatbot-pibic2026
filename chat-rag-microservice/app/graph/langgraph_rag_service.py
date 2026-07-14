"""LangGraph + lightweight RAG service for conversation state management."""
from __future__ import annotations

import json
import os
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.infrastructure.settings import settings
from app.infrastructure.cache import redis_cache
from app.infrastructure.logger import logger
from app.llm.structured_output import ESPECIALIDADES_CONHECIDAS


class ConversationState(TypedDict):
    """State tracked by LangGraph."""

    messages: Annotated[list[BaseMessage], add_messages]


class LangGraphRAGService:
    """Centralize conversational memory and RAG augmentation."""

    def __init__(self) -> None:
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()
        self._knowledge_chunks = self._load_knowledge_chunks(settings.RAG_KB_PATH)

    @staticmethod
    def _build_graph():
        builder = StateGraph(ConversationState)
        builder.add_node("persist", lambda state: state)
        builder.add_edge(START, "persist")
        builder.add_edge("persist", END)
        return builder.compile(checkpointer=MemorySaver())

    @staticmethod
    def _thread_config(session_id: str) -> dict:
        return {"configurable": {"thread_id": session_id}}

    @staticmethod
    def _message_key(session_id: str) -> str:
        return f"lg:session:{session_id}:messages"

    @staticmethod
    def _job_key(job_id: str) -> str:
        return f"lg:job:{job_id}:context"

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    def _load_knowledge_chunks(self, path: str) -> list[str]:
        if not os.path.exists(path):
            logger.warning(f"RAG knowledge base not found at {path}; continuing without retrieval context")
            return []

        with open(path, "r", encoding="utf-8") as kb_file:
            text = kb_file.read()

        chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        return chunks

    def _retrieve_context(self, query: str, top_k: int = 3) -> list[str]:
        if not self._knowledge_chunks:
            return []

        query_tokens = self._tokenize(query)
        scored: list[tuple[int, str]] = []
        for chunk in self._knowledge_chunks:
            score = len(query_tokens & self._tokenize(chunk))
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for score, chunk in scored[:top_k] if score > 0]

    async def _ensure_redis_connected(self) -> None:
        if redis_cache.client is None:
            await redis_cache.connect()

    async def _rehydrate_if_needed(self, session_id: str) -> None:
        current = self.get_state(session_id)
        if current:
            return

        await self._ensure_redis_connected()
        history_raw = await redis_cache.get(self._message_key(session_id))
        if not history_raw:
            return

        try:
            history = json.loads(history_raw)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON history for session {session_id}")
            return

        replay_messages: list[BaseMessage] = []
        for entry in history:
            role = entry.get("role")
            content = entry.get("content", "")
            if role == "system":
                replay_messages.append(SystemMessage(content=content))
            elif role == "user":
                replay_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                replay_messages.append(AIMessage(content=content))

        if replay_messages:
            self._graph.invoke({"messages": replay_messages}, config=self._thread_config(session_id))

    async def _persist_history(self, session_id: str) -> None:
        await self._ensure_redis_connected()
        messages = self.get_state(session_id)

        serialized: list[dict[str, str]] = []
        for message in messages[-settings.LANGGRAPH_MEMORY_WINDOW :]:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "assistant"
            serialized.append({"role": role, "content": str(message.content)})

        await redis_cache.set(
            self._message_key(session_id),
            json.dumps(serialized),
            ttl=settings.JOB_TTL,
        )

    async def register_user_message(
        self,
        session_id: str,
        user_message: str,
        patient_context: dict | None = None,
    ) -> None:
        """Register user message and ensure session system context exists."""
        await self._rehydrate_if_needed(session_id)

        new_messages: list[BaseMessage] = []
        if not self.get_state(session_id):
            context_text = ""
            if patient_context:
                context_text = "\n".join(f"- {key}: {value}" for key, value in patient_context.items())

            especialidades_lista = ", ".join(ESPECIALIDADES_CONHECIDAS)
            system_prompt = (
                "Você é um assistente de triagem médica. Não forneça diagnóstico final. "
                "Colete dados com empatia e objetividade para encaminhamento clínico.\n"
                "Use o contexto recuperado apenas como apoio e priorize segurança clínica.\n\n"
                "FORMATO DE SAÍDA OBRIGATÓRIO: responda SEMPRE com um único objeto JSON, "
                "sem cercas de código Markdown e sem texto fora do JSON, no formato:\n"
                '{"status": "ongoing" | "diagnosis_concluded", "message": "texto para o paciente", '
                '"specialty": null ou uma das especialidades abaixo, "orientation": null ou um resumo '
                "clínico objetivo para o médico}.\n"
                f"Quando status for \"diagnosis_concluded\", 'specialty' deve ser exatamente uma destas "
                f"{len(ESPECIALIDADES_CONHECIDAS)} opções (nunca uma variação livre): {especialidades_lista}. "
                "Use \"Clínica Geral\" quando nenhuma especialidade mais específica se aplicar claramente."
            )
            if context_text:
                system_prompt += f"\n\nContexto do paciente:\n{context_text}"
            new_messages.append(SystemMessage(content=system_prompt))

        new_messages.append(HumanMessage(content=user_message))
        self._graph.invoke({"messages": new_messages}, config=self._thread_config(session_id))
        await self._persist_history(session_id)

    async def register_assistant_message(self, session_id: str, assistant_message: str) -> None:
        """Register assistant reply in LangGraph memory."""
        await self._rehydrate_if_needed(session_id)
        self._graph.invoke(
            {"messages": [AIMessage(content=assistant_message)]},
            config=self._thread_config(session_id),
        )
        await self._persist_history(session_id)

    def get_state(self, session_id: str) -> list[BaseMessage]:
        snapshot = self._graph.get_state(config=self._thread_config(session_id))
        if not snapshot or not snapshot.values:
            return []
        return snapshot.values.get("messages", [])

    async def build_augmented_prompt(self, session_id: str, query: str) -> str:
        """Build final prompt combining memory window and RAG context."""
        await self._rehydrate_if_needed(session_id)
        messages = self.get_state(session_id)
        memory_window = messages[-settings.LANGGRAPH_MEMORY_WINDOW :]

        lines: list[str] = []
        for message in memory_window:
            if isinstance(message, SystemMessage):
                lines.append(f"[SYSTEM]\n{message.content}")
            elif isinstance(message, HumanMessage):
                lines.append(f"[PACIENTE]\n{message.content}")
            elif isinstance(message, AIMessage):
                lines.append(f"[ASSISTENTE]\n{message.content}")

        retrieved = self._retrieve_context(query, top_k=settings.RAG_TOP_K)
        if retrieved:
            lines.append("[RAG_CONTEXT]")
            for idx, chunk in enumerate(retrieved, start=1):
                lines.append(f"Fonte {idx}: {chunk}")

        lines.append(
            "Continue a triagem com perguntas curtas e seguras. Se não houver dados suficientes, peça mais detalhes."
        )
        return "\n\n".join(lines)

    async def remember_job_context(self, job_id: str, session_id: str) -> None:
        """Store mapping between job and session for post-processing sync."""
        await self._ensure_redis_connected()
        await redis_cache.set(
            self._job_key(job_id),
            json.dumps({"session_id": session_id, "assistant_synced": False}),
            ttl=settings.JOB_TTL,
        )

    async def sync_assistant_from_job(self, job_id: str, assistant_message: str) -> None:
        """Sync worker response into session memory exactly once."""
        await self._ensure_redis_connected()
        raw = await redis_cache.get(self._job_key(job_id))
        if not raw:
            return

        try:
            context = json.loads(raw)
        except json.JSONDecodeError:
            return

        if context.get("assistant_synced"):
            return

        session_id = context.get("session_id")
        if not session_id:
            return

        await self.register_assistant_message(session_id, assistant_message)
        context["assistant_synced"] = True
        await redis_cache.set(self._job_key(job_id), json.dumps(context), ttl=settings.JOB_TTL)


langgraph_rag_service = LangGraphRAGService()
