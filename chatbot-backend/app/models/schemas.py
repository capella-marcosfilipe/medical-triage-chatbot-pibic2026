"""Pydantic models for request/response data validation."""
from pydantic import BaseModel, Field
from typing import Optional

from app.models.async_schemas import NLPExecutionMode, NLPJobStatus


class PacienteData(BaseModel):
    """Patient personal data."""
    nome_completo: str = Field(..., description="Full name of the patient")
    endereco: str = Field(..., description="Patient's address")
    idade: int = Field(..., ge=0, le=120, description="Patient's age")


class IniciarAtendimentoResponse(BaseModel):
    """Response for starting a new medical session."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(default="Atendimento iniciado com sucesso")


class DadosFisiologicos(BaseModel):
    """Physiological data from smartwatch."""
    frequencia_cardiaca: int = Field(..., description="Heart rate in BPM")
    saturacao_oxigenio: int = Field(..., ge=0, le=100, description="Oxygen saturation percentage")
    pressao_arterial_sistolica: int = Field(..., description="Systolic blood pressure")
    pressao_arterial_diastolica: int = Field(..., description="Diastolic blood pressure")
    temperatura_corporal: float = Field(..., description="Body temperature in Celsius")


class ObterDadosSmartWatchResponse(BaseModel):
    """Response with smartwatch physiological data."""
    dados_fisiologicos: DadosFisiologicos


class ChatGeminiRequest(BaseModel):
    """Request for chatting with Gemini AI."""
    session_id: str = Field(..., description="Session identifier")
    user_message: str = Field(..., description="User's message")


class FichaDeAtendimento(BaseModel):
    """Complete medical record."""
    session_id: str
    nome_completo: str
    endereco: str
    idade: int
    dados_fisiologicos: Optional[DadosFisiologicos] = None
    queixa_principal: Optional[str] = None
    historico_sintomas: Optional[str] = None
    historico_doencas_previas: Optional[str] = None
    alergias: Optional[str] = None
    medicamentos_em_uso: Optional[str] = None
    nivel_urgencia: Optional[str] = None
    especialidade_medica: Optional[str] = None
    orientacao_ao_medico: Optional[str] = None


class ChatGeminiResponse(BaseModel):
    """Response from chat with Gemini AI."""
    bot_message: str = Field(..., description="Bot's response message")
    status: str = Field(..., description="Conversation status: 'ongoing' or 'final'")
    ficha_de_atendimento: Optional[FichaDeAtendimento] = None


class ObterFichaCompletaResponse(BaseModel):
    """Response with complete medical record."""
    ficha_de_atendimento: FichaDeAtendimento


class ChatNemotronRequest(BaseModel):
    """Request for chatting with Nemotron through async workers."""

    session_id: str = Field(..., description="Session identifier")
    user_message: str = Field(..., min_length=1, description="User message")
    idempotency_key: str = Field(..., min_length=8, description="Idempotency key")
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.6, ge=0.0, le=1.0)
    use_reasoning: bool = Field(default=False)
    mode: NLPExecutionMode = Field(default=NLPExecutionMode.AUTO)
    priority: int = Field(default=5, ge=1, le=10)


class ChatNemotronEnqueueResponse(BaseModel):
    """Immediate async response for Nemotron chat requests."""

    job_id: str
    status: NLPJobStatus = NLPJobStatus.PENDING
    idempotency_key: str
    queue: str
