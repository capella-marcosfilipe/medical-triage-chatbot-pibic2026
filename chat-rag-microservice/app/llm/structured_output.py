"""Parsing and sanitization for the LLM structured-output contract.

Every triage LLM turn is expected to return a single JSON object shaped like
`{"status": ..., "message": ..., "specialty": ..., "orientation": ...}` (see
`docs/structured_output_contract.md`). This module is deliberately free of
any heavy dependency (no LangGraph/Redis/OpenAI imports) so it stays trivial
to unit test in isolation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

from app.infrastructure.logger import logger

DiagnosisStatus = Literal["ongoing", "diagnosis_concluded"]

# Same 12 specialties used in chatbot-backend/pacientes_sinteticos.json (Dia 10).
# Kept as a literal duplicate across services on purpose: chat-rag-microservice
# and chatbot-backend/simulador.py are separate Python packages with no shared
# module today, and this list is small and stable enough that duplicating it is
# simpler than introducing a cross-service dependency for one constant.
ESPECIALIDADES_CONHECIDAS = (
    "Cardiologia",
    "Neurologia",
    "Pneumologia",
    "Gastroenterologia",
    "Ortopedia",
    "Pediatria",
    "Clínica Geral",
    "Urologia",
    "Dermatologia",
    "Psiquiatria",
    "Oftalmologia",
    "Otorrinolaringologia",
)

_MARKDOWN_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class StructuredLLMOutput:
    """Result of parsing one LLM turn against the structured-output contract."""

    status: DiagnosisStatus
    message: str
    specialty: str | None
    orientation: str | None


def _strip_markdown_fences(raw_text: str) -> str:
    """Remove accidental ```json ... ``` (or ``` ... ```) fences around the JSON."""
    return _MARKDOWN_FENCE_PATTERN.sub("", raw_text).strip()


def _fallback(raw_text: str, reason: str) -> StructuredLLMOutput:
    logger.warning(f"[structured_output] Falling back to raw text: {reason}")
    return StructuredLLMOutput(status="ongoing", message=raw_text, specialty=None, orientation=None)


def parse_structured_response(raw_text: str) -> StructuredLLMOutput:
    """Parse one LLM turn against the structured-output contract.

    Never raises: any parsing problem (invalid JSON, missing/invalid fields,
    a `specialty` outside the closed list) degrades to a safe fallback that
    keeps the conversation going with `status="ongoing"` and the raw model
    text as the message, logged via `logger.warning` for later monitoring of
    the parsing failure rate.

    Args:
        raw_text: Raw text returned by the LLM for this turn.

    Returns:
        A `StructuredLLMOutput` with either the parsed fields or the fallback
        shape described above.
    """
    if not raw_text or not raw_text.strip():
        return _fallback(raw_text, "empty response from the model")

    sanitized = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(sanitized)
    except json.JSONDecodeError as exc:
        return _fallback(raw_text, f"invalid JSON ({exc})")

    if not isinstance(data, dict):
        return _fallback(raw_text, f"parsed JSON is not an object (got {type(data).__name__})")

    status = data.get("status")
    if status not in ("ongoing", "diagnosis_concluded"):
        return _fallback(raw_text, f"unexpected status value: {status!r}")

    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return _fallback(raw_text, "missing or empty 'message' field")

    specialty = data.get("specialty")
    if specialty is not None:
        if not isinstance(specialty, str) or specialty not in ESPECIALIDADES_CONHECIDAS:
            logger.warning(
                f"[structured_output] specialty {specialty!r} is not in the closed list; discarding it"
            )
            specialty = None

    orientation = data.get("orientation")
    if orientation is not None and not isinstance(orientation, str):
        logger.warning(f"[structured_output] orientation had an unexpected type: {type(orientation).__name__}")
        orientation = None

    return StructuredLLMOutput(
        status=status,
        message=message,
        specialty=specialty,
        orientation=orientation,
    )
