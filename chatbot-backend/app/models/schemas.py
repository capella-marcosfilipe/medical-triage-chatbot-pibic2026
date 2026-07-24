"""Pydantic models for request/response data validation."""
from pydantic import BaseModel, Field
from typing import Optional

from app.models.async_schemas import NLPJobStatus


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


class ObterFichaCompletaResponse(BaseModel):
    """Response with complete medical record."""
    ficha_de_atendimento: FichaDeAtendimento


class ChatNemotronRequest(BaseModel):
    """Request for chatting with Nemotron through async workers."""

    message: str = Field(..., min_length=1, description="User message")
    engine: str = Field(default="nemotron", description="Chat engine to use")
    chat_id: Optional[str] = Field(default=None, description="Conversation identifier")


class ChatNemotronEnqueueResponse(BaseModel):
    """Immediate async response for Nemotron chat requests."""

    job_id: str
    chat_id: str
    status: NLPJobStatus = NLPJobStatus.PENDING
    idempotency_key: str
    queue: str
