"""API v1 endpoints for medical triage chatbot."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
import httpx

from app.models.async_schemas import (
    NLPJobStatusResponse,
    NLPJobContent,
    NLPJobStatus,
    ChatHistoryResponse,
    ChatHistoryMessage,
)
from app.models.schemas import (
    PacienteData,
    IniciarAtendimentoResponse,
    ObterDadosSmartWatchResponse,
    ChatNemotronRequest,
    ChatNemotronEnqueueResponse,
    ObterFichaCompletaResponse
)
from app.services.session_manager import session_manager
from app.services.smartwatch_simulator import smartwatch_simulator
from app.services.microservice_client import chatbot_microservice_client

router = APIRouter()


@router.post("/start_session", response_model=IniciarAtendimentoResponse)
async def start_session(paciente_data: PacienteData):
    """Initialize a new patient session."""
    try:
        session_id = session_manager.create_session(paciente_data)
        return IniciarAtendimentoResponse(
            session_id=session_id,
            message="Atendimento iniciado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar atendimento: {str(e)}")


@router.post("/iniciar_atendimento", response_model=IniciarAtendimentoResponse)
async def iniciar_atendimento(paciente_data: PacienteData):
    """Legacy alias for starting a patient session."""
    return await start_session(paciente_data)


@router.get("/get_smartwatch_data/{smartwatch_id}", response_model=ObterDadosSmartWatchResponse)
async def get_smartwatch_data(smartwatch_id: str):
    """Get simulated smartwatch data by smartwatch device id."""
    try:
        dados = smartwatch_simulator.generate_data()
        return ObterDadosSmartWatchResponse(dados_fisiologicos=dados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados do smartwatch: {str(e)}")


@router.get("/obter_dados_smartwatch/{session_id}", response_model=ObterDadosSmartWatchResponse)
async def obter_dados_smartwatch(session_id: str):
    """Legacy alias for smartwatch data retrieval."""
    return await get_smartwatch_data(session_id)


def _build_idempotency_key(chat_id: str, engine: str, message: str) -> str:
    digest = hashlib.sha256(f"{chat_id}:{engine}:{message}".encode("utf-8")).hexdigest()
    return digest


def _infer_diagnosis_status(answer: str) -> Literal["ongoing", "diagnosis_concluded"]:
    normalized = answer.lower()
    concluding_markers = (
        "triagem conclu",
        "conversa finalizada",
        "ficha de atendimento",
        "encaminhamento",
        "procure atendimento",
        "procure um serviço de urgência",
        "diagnóstico final",
        "diagnóstico conclu",
    )
    return "diagnosis_concluded" if any(marker in normalized for marker in concluding_markers) else "ongoing"


@router.post("/chat", response_model=ChatNemotronEnqueueResponse, status_code=202)
async def chat(
    request: ChatNemotronRequest,
):
    """Delegate chat processing to chat-rag-microservice."""
    chat_id = request.chat_id or str(uuid.uuid4())
    idempotency_key = _build_idempotency_key(chat_id, request.engine, request.message)

    session = session_manager.get_session(chat_id)

    try:
        session_manager.add_conversation_message(chat_id, "user", request.message)

        queue_request: dict[str, object] = {
            "session_id": chat_id,
            "message": request.message,
            "idempotency_key": idempotency_key,
            "engine": request.engine,
        }

        if session:
            patient_context: dict[str, object] = {
                "nome_completo": session.nome_completo,
                "idade": session.idade,
                "endereco": session.endereco,
            }

            if session.dados_fisiologicos:
                patient_context["dados_fisiologicos"] = session.dados_fisiologicos.model_dump()

            queue_request["patient_context"] = patient_context

        microservice_response = await chatbot_microservice_client.enqueue_chat(
            payload=queue_request,
            mode="auto",
        )

        session_manager.register_chat_job(microservice_response["job_id"], chat_id)

        response = ChatNemotronEnqueueResponse(
            job_id=microservice_response["job_id"],
            chat_id=chat_id,
            status=microservice_response["status"],
            idempotency_key=microservice_response.get("idempotency_key", idempotency_key),
            queue="chat-rag-microservice",
        )

        return response
    except httpx.HTTPStatusError as e:
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(status_code=502, detail=f"Erro no chat-rag-microservice: {detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Falha de comunicação com chat-rag-microservice: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao comunicar com Nemotron: {str(e)}")


@router.get("/chat/status/{job_id}", response_model=NLPJobStatusResponse)
async def chat_with_nemotron_status(
    job_id: str,
):
    """Get chat job status from chat-rag-microservice."""
    try:
        result = await chatbot_microservice_client.get_chat_status(job_id)
        chat_id = session_manager.get_chat_id_by_job(job_id) or result.get("chat_id") or ""

        content = None
        response_payload = result.get("result")
        if response_payload:
            answer = response_payload.get("response", "")
            session_manager.sync_assistant_message(chat_id, answer)
            content = NLPJobContent(
                answer=answer,
                processing_time_ms=response_payload.get("latency_ms"),
                diagnosis_status=_infer_diagnosis_status(answer),
            )

        return NLPJobStatusResponse(
            job_id=result["job_id"],
            chat_id=chat_id,
            status=NLPJobStatus(result["status"]),
            idempotency_key=result.get("idempotency_key", job_id),
            created_at=datetime.fromisoformat(result["created_at"]),
            content=content,
            error=result.get("error"),
        )
    except httpx.HTTPStatusError as e:
        status_code = 404 if e.response.status_code == 404 else 502
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(status_code=status_code, detail=f"Erro no chat-rag-microservice: {detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Falha de comunicação com chat-rag-microservice: {str(e)}")


@router.get("/chat/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_history(chat_id: str):
    """Get the full conversation history for a chat id."""
    history = session_manager.get_conversation_history(chat_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    return ChatHistoryResponse(
        chat_id=chat_id,
        messages=[ChatHistoryMessage.model_validate(message) for message in history],
    )


@router.get("/chat_with_nemotron/status/{job_id}", response_model=NLPJobStatusResponse)
async def chat_with_nemotron_status_legacy(
    job_id: str,
):
    """Legacy alias for chat job status."""
    return await chat_with_nemotron_status(job_id)


@router.get("/obter_ficha_completa/{session_id}", response_model=ObterFichaCompletaResponse)
async def obter_ficha_completa(session_id: str):
    """Get the complete medical record for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    return ObterFichaCompletaResponse(ficha_de_atendimento=session)


@router.post("/chat_with_gemini")
async def chat_with_gemini_deprecated():
    """Deprecated endpoint kept for compatibility with old clients."""
    raise HTTPException(
        status_code=410,
        detail="Endpoint descontinuado. Use /api/v1/chat.",
    )
