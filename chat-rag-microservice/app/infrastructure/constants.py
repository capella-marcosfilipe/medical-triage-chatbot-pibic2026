"""Project-wide constants for chat-rag-microservice.

Fixed values that describe *what* the system is (model identifiers, the
closed specialty list, the vector similarity metric) as opposed to *how
it's deployed* (app/infrastructure/settings.py, which is meant to be
overridden via environment variables). Everything here should be imported
from this module rather than re-declared or hardcoded at the call site.
"""
from __future__ import annotations

# --- Nemotron model identifiers ---

# API model slug (https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2),
# used by app/llm/nemotron_service.py's API-mode calls.
NEMOTRON_API_MODEL = "nvidia/nvidia-nemotron-nano-9b-v2"

# HuggingFace Hub repo id for the same model, used by app/llm/engine.py's
# local/GPU mode. Different casing convention than the API slug above — that
# is expected, not an inconsistency (NVIDIA's API catalog and the HF Hub
# name the same model differently).
NEMOTRON_GPU_MODEL = "nvidia/NVIDIA-Nemotron-Nano-9B-v2"

NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"

# --- Nemotron reasoning mode ---

# System-message tokens that toggle the model's chain-of-thought reasoning
# on/off (see app/llm/nemotron_service.py's _build_messages). This model
# defaults to reasoning ON when neither token is sent, so one of the two
# must always be present — REASONING_DISABLE_TOKEN is what keeps the
# structured-output contract (status/message/specialty/orientation JSON)
# from competing with chain-of-thought tokens for the same max_tokens budget.
REASONING_TRIGGER_TOKEN = "/think"
REASONING_DISABLE_TOKEN = "/no_think"
REASONING_MIN_THINKING_TOKENS = 256
REASONING_MAX_THINKING_TOKENS = 1024

# --- Structured-output contract (see docs/structured_output_contract.md) ---

# Closed list of specialties the LLM must choose from when
# status == "diagnosis_concluded". Duplicated intentionally in
# chatbot-backend/pacientes_sinteticos.json and simulador.py: those live in
# a separate Python package with no shared module, so keeping one literal
# list in each place is simpler than introducing a cross-service dependency.
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

# --- ChromaDB (Manchester/Maringá knowledge base) ---

CHROMA_DISTANCE_METRIC = "cosine"
