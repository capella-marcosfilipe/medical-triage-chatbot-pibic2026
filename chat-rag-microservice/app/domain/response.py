from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatResponse(BaseModel):
    response: str = Field(description="Sanitized message text shown to the patient (mirrors `message`).")
    mode: str = Field(description="Execution mode (gpu or api)")
    latency_ms: Optional[float] = None

    # Structured-output contract fields (see docs/structured_output_contract.md).
    # `response` is kept for backward compatibility with existing consumers
    # (e.g. LangGraphRAGService.sync_assistant_from_job reads `.response`).
    status: Literal["ongoing", "diagnosis_concluded"] = "ongoing"
    message: str = Field(default="", description="Same text as `response`, named per the structured contract.")
    specialty: Optional[str] = Field(default=None, description="One of the 12 known specialties, or None.")
    orientation: Optional[str] = Field(default=None, description="Clinical summary for the attending physician.")


class ChatAsyncResponse(BaseModel):
    job_id: str
    status: JobStatus
    idempotency_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[ChatResponse] = None
    error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    available_modes: dict[str, bool]
    default_mode: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
