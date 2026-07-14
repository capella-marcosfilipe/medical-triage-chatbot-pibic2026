"""Tests for _resolve_diagnosis_content, added when chat-rag-microservice
started returning the structured-output contract fields
(status/specialty/orientation). Prefers those fields; only falls back to
the legacy _infer_diagnosis_status keyword heuristic when the microservice
response doesn't carry them (defense in depth during the transition)."""
from app.api.v1.endpoints import _resolve_diagnosis_content


def test_usa_campos_estruturados_quando_presentes():
    payload = {
        "response": "texto qualquer",
        "status": "diagnosis_concluded",
        "specialty": "Cardiologia",
        "orientation": "resumo clínico",
    }
    status, specialty, orientation = _resolve_diagnosis_content(payload)
    assert status == "diagnosis_concluded"
    assert specialty == "Cardiologia"
    assert orientation == "resumo clínico"


def test_usa_campos_estruturados_ongoing():
    payload = {"response": "Pode me dizer mais sobre a dor?", "status": "ongoing", "specialty": None, "orientation": None}
    status, specialty, orientation = _resolve_diagnosis_content(payload)
    assert status == "ongoing"
    assert specialty is None
    assert orientation is None


def test_cai_no_fallback_quando_status_estruturado_ausente():
    # Simula uma versão antiga do chat-rag-microservice que ainda não
    # retorna os campos estruturados (apenas response/mode/latency_ms).
    payload = {"response": "Recomendo encaminhamento para Cardiologia.", "mode": "api", "latency_ms": 120.0}
    status, specialty, orientation = _resolve_diagnosis_content(payload)
    assert status == "diagnosis_concluded"
    assert specialty is None
    assert orientation is None


def test_cai_no_fallback_quando_status_estruturado_e_invalido():
    payload = {"response": "Pode me dizer mais sobre a dor?", "status": "valor_desconhecido"}
    status, specialty, orientation = _resolve_diagnosis_content(payload)
    assert status == "ongoing"
    assert specialty is None
    assert orientation is None
