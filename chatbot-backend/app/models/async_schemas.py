"""Schemas for asynchronous NLP job communication."""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class NLPExecutionMode(str, Enum):
    """Execution mode for NLP processing workers."""

    AUTO = "auto"
    API = "api"
    GPU = "gpu"


class NLPJobStatus(str, Enum):
    """Possible states for asynchronous NLP jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NLPJobContent(BaseModel):
    """Structured content returned after the LLM responds."""

    answer: str
    processing_time_ms: Optional[float] = None
    diagnosis_status: Literal["ongoing", "diagnosis_concluded"]


class ChatHistoryMessage(BaseModel):
    """Single message in a chat history."""

    role: Literal["user", "assistant", "system"]
    content: str


class ChatHistoryResponse(BaseModel):
    """Full chat history for a resumed conversation."""

    chat_id: str
    messages: list[ChatHistoryMessage]


class NLPChatRequest(BaseModel):
    """Payload accepted by the gateway for asynchronous NLP processing."""

    session_id: str = Field(..., description="Patient session identifier")
    message: str = Field(..., min_length=1, description="User message to process")
    idempotency_key: str = Field(..., min_length=8, description="Request key to prevent duplicate processing")
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.6, ge=0.0, le=1.0)
    use_reasoning: bool = Field(default=False, description="Enable reasoning tokens when API mode is used")
    mode: NLPExecutionMode = Field(default=NLPExecutionMode.AUTO)
    priority: int = Field(default=5, ge=1, le=10)


class NLPJobEnqueueResponse(BaseModel):
    """Response returned immediately after enqueueing a request."""

    job_id: str
    status: NLPJobStatus = NLPJobStatus.PENDING
    idempotency_key: str
    queue: str


class NLPJobResult(BaseModel):
    """Result payload returned by worker service when job is completed."""

    response: str
    mode: str
    latency_ms: Optional[float] = None


class NLPJobStatusResponse(BaseModel):
    """Current status and optional result for asynchronous NLP jobs."""

    job_id: str
    chat_id: str
    status: NLPJobStatus
    idempotency_key: str
    created_at: datetime
    content: Optional[NLPJobContent] = None
    error: Optional[str] = None
