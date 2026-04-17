"""API v1 endpoints for medical triage chatbot."""
from fastapi import APIRouter, HTTPException
import httpx

from app.models.async_schemas import (
    NLPJobStatusResponse,
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


@router.post("/iniciar_atendimento", response_model=IniciarAtendimentoResponse)
async def iniciar_atendimento(paciente_data: PacienteData):
    """Initialize a new patient session."""
    try:
        session_id = session_manager.create_session(paciente_data)
        return IniciarAtendimentoResponse(
            session_id=session_id,
            message="Atendimento iniciado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar atendimento: {str(e)}")


@router.get("/obter_dados_smartwatch/{session_id}", response_model=ObterDadosSmartWatchResponse)
async def obter_dados_smartwatch(session_id: str):
    """Get simulated smartwatch data for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    try:
        # Simulate smartwatch data
        dados = smartwatch_simulator.generate_data()
        session_manager.add_smartwatch_data(session_id, dados)
        
        return ObterDadosSmartWatchResponse(dados_fisiologicos=dados)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados do smartwatch: {str(e)}")


@router.post("/chat_with_nemotron", response_model=ChatNemotronEnqueueResponse)
async def chat_with_nemotron(
    request: ChatNemotronRequest,
):
    """Delegate Nemotron chat processing to chatbot-microservice."""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    try:
        session_manager.add_conversation_message(request.session_id, "user", request.user_message)

        queue_request = {
            "session_id": request.session_id,
            "message": request.user_message,
            "idempotency_key": request.idempotency_key,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "use_reasoning": request.use_reasoning,
            "mode": request.mode.value,
            "priority": request.priority,
            "patient_context": {
                "nome_completo": session.nome_completo,
                "idade": session.idade,
                "endereco": session.endereco,
            },
        }

        if session.dados_fisiologicos:
            queue_request["patient_context"]["dados_fisiologicos"] = session.dados_fisiologicos.model_dump()

        microservice_response = await chatbot_microservice_client.enqueue_chat(
            payload=queue_request,
            mode=request.mode.value,
        )

        response = ChatNemotronEnqueueResponse(
            job_id=microservice_response["job_id"],
            status=microservice_response["status"],
            idempotency_key=microservice_response["idempotency_key"],
            queue="chatbot-microservice",
        )

        return response
    except httpx.HTTPStatusError as e:
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(status_code=502, detail=f"Erro no chatbot-microservice: {detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Falha de comunicação com chatbot-microservice: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao comunicar com Nemotron: {str(e)}")


@router.get("/chat_with_nemotron/status/{job_id}", response_model=NLPJobStatusResponse)
async def chat_with_nemotron_status(
    job_id: str,
):
    """Get Nemotron job status from chatbot-microservice."""
    try:
        result = await chatbot_microservice_client.get_chat_status(job_id)
        return NLPJobStatusResponse(**result)
    except httpx.HTTPStatusError as e:
        status_code = 404 if e.response.status_code == 404 else 502
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(status_code=status_code, detail=f"Erro no chatbot-microservice: {detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Falha de comunicação com chatbot-microservice: {str(e)}")


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
        detail="Endpoint descontinuado. Use /api/v1/chat_with_nemotron.",
    )
