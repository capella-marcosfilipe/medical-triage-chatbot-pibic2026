"""Tests for LangGraphRAGService._apply_memory_window.

Regression coverage for a real bug found during investigation: a plain
`messages[-window:]` slice silently dropped the leading SystemMessage (the
JSON output contract + closed specialty list) once a conversation grew past
`LANGGRAPH_MEMORY_WINDOW` total messages. `_apply_memory_window` is a pure
staticmethod, so it's tested directly without instantiating the full
service (which would require Redis/ChromaDB).
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.langgraph_rag_service import LangGraphRAGService
from app.infrastructure.settings import settings


def _turns(n: int) -> list:
    """Build n Human/AI message pairs."""
    messages = []
    for i in range(n):
        messages.append(HumanMessage(content=f"paciente turno {i}"))
        messages.append(AIMessage(content=f"assistente turno {i}"))
    return messages


def test_janela_menor_que_limite_nao_corta_nada():
    messages = [SystemMessage(content="contrato")] + _turns(3)
    result = LangGraphRAGService._apply_memory_window(messages)
    assert result == messages


def test_janela_no_limite_exato_nao_corta_nada():
    window = settings.LANGGRAPH_MEMORY_WINDOW
    messages = [SystemMessage(content="contrato")] + _turns((window - 1) // 2)
    while len(messages) < window:
        messages.append(HumanMessage(content="preenchimento"))
    assert len(messages) == window
    result = LangGraphRAGService._apply_memory_window(messages)
    assert result == messages


def test_janela_excedida_preserva_mensagem_de_sistema():
    window = settings.LANGGRAPH_MEMORY_WINDOW
    system = SystemMessage(content="contrato")
    messages = [system] + _turns(window)  # window + 1 + 2*window messages, well past the limit

    result = LangGraphRAGService._apply_memory_window(messages)

    assert len(result) == window
    assert result[0] is system
    assert result[1:] == messages[-(window - 1):]


def test_sem_mensagem_de_sistema_apenas_corta_pelo_final():
    window = settings.LANGGRAPH_MEMORY_WINDOW
    messages = _turns(window)  # no SystemMessage at index 0

    result = LangGraphRAGService._apply_memory_window(messages)

    assert len(result) == window
    assert result == messages[-window:]


def test_lista_vazia_retorna_vazia():
    assert LangGraphRAGService._apply_memory_window([]) == []
