"""Tests for correlating /get_smartwatch_data with the patient session.

Covers the fix for the gap found by RELATORIO_EXECUCAO_SIMULADOR_VITAIS.md:
session_manager.add_smartwatch_data() existed but was never called, so
patient_context.dados_fisiologicos never reached the LLM. Also regression
-covers /chat building patient_context from the populated session.
"""
from fastapi.testclient import TestClient

import app.api.v1.endpoints as endpoints_module
from app.services.session_manager import session_manager
from main import app

client = TestClient(app)


def limpar_sessoes():
    """Reset the module-level session_manager singleton between tests."""
    session_manager.sessions.clear()
    session_manager.conversation_history.clear()
    session_manager.chat_jobs.clear()


def iniciar_sessao() -> str:
    resp = client.post(
        "/api/v1/start_session",
        json={"nome_completo": "Paciente Teste", "endereco": "Rua Teste, 123", "idade": 40},
    )
    assert resp.status_code == 200
    return resp.json()["session_id"]


def test_get_smartwatch_data_preenche_dados_fisiologicos_da_sessao():
    limpar_sessoes()
    session_id = iniciar_sessao()

    resp = client.get(f"/api/v1/get_smartwatch_data/sim-1?session_id={session_id}")

    assert resp.status_code == 200
    dados_retornados = resp.json()["dados_fisiologicos"]

    sessao = session_manager.get_session(session_id)
    assert sessao.dados_fisiologicos is not None
    assert sessao.dados_fisiologicos.model_dump() == dados_retornados


def test_get_smartwatch_data_com_session_id_invalido_retorna_404():
    limpar_sessoes()

    resp = client.get("/api/v1/get_smartwatch_data/sim-1?session_id=sessao-que-nao-existe")

    assert resp.status_code == 404


def test_get_smartwatch_data_sem_session_id_e_erro_de_validacao():
    limpar_sessoes()

    resp = client.get("/api/v1/get_smartwatch_data/sim-1")

    assert resp.status_code == 422


def test_chat_inclui_dados_fisiologicos_no_patient_context(monkeypatch):
    limpar_sessoes()
    session_id = iniciar_sessao()
    client.get(f"/api/v1/get_smartwatch_data/sim-1?session_id={session_id}")

    payloads_enviados = []

    async def enqueue_chat_fake(payload, mode):
        payloads_enviados.append(payload)
        return {"job_id": "job-1", "status": "pending", "idempotency_key": "abc"}

    monkeypatch.setattr(endpoints_module.chatbot_microservice_client, "enqueue_chat", enqueue_chat_fake)

    # chat_id igual ao session_id: é assim que o frontend agora semeia o
    # primeiro turno (ver nemotron-chat.service.ts), para que a sessão seja
    # encontrada por session_manager.get_session(chat_id).
    resp = client.post(
        "/api/v1/chat",
        json={"message": "Estou com dor no peito", "engine": "nemotron", "chat_id": session_id},
    )

    assert resp.status_code == 202
    assert len(payloads_enviados) == 1

    patient_context = payloads_enviados[0]["patient_context"]
    sessao = session_manager.get_session(session_id)
    assert patient_context["dados_fisiologicos"] == sessao.dados_fisiologicos.model_dump()
