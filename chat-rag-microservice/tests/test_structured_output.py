"""Tests for the structured-output parsing/sanitization contract.

See docs/structured_output_contract.md for the full contract this function
implements.
"""
import pytest

from app.infrastructure.constants import ESPECIALIDADES_CONHECIDAS
from app.llm.structured_output import _SAFE_FALLBACK_MESSAGE, parse_structured_response


def test_parseia_json_limpo_ongoing():
    raw = '{"status": "ongoing", "message": "Há quanto tempo você sente essa dor?", "specialty": null, "orientation": null}'
    result = parse_structured_response(raw)
    assert result.status == "ongoing"
    assert result.message == "Há quanto tempo você sente essa dor?"
    assert result.specialty is None
    assert result.orientation is None


def test_parseia_json_limpo_concluido_com_especialidade_valida():
    raw = (
        '{"status": "diagnosis_concluded", "message": "Triagem concluída.", '
        '"specialty": "Cardiologia", "orientation": "Paciente com dor torácica típica."}'
    )
    result = parse_structured_response(raw)
    assert result.status == "diagnosis_concluded"
    assert result.specialty == "Cardiologia"
    assert result.orientation == "Paciente com dor torácica típica."


@pytest.mark.parametrize(
    "cercas",
    [
        '```json\n{"status": "ongoing", "message": "oi", "specialty": null, "orientation": null}\n```',
        '```\n{"status": "ongoing", "message": "oi", "specialty": null, "orientation": null}\n```',
    ],
)
def test_remove_cercas_markdown_antes_do_parse(cercas):
    result = parse_structured_response(cercas)
    assert result.status == "ongoing"
    assert result.message == "oi"


@pytest.mark.parametrize(
    "malformado",
    [
        "isso não é JSON de jeito nenhum",
        '{"status": "ongoing", "message": "faltando fechar chave"',
        '{"status": "ongoing"}',  # falta message
        '{"message": "sem status"}',  # falta status
        '{"status": "valor_invalido", "message": "oi"}',
        "[1, 2, 3]",  # JSON válido mas não é um objeto
    ],
)
def test_json_malformado_cai_no_fallback_sem_excecao(malformado):
    result = parse_structured_response(malformado)
    assert result.status == "ongoing"
    assert result.message == _SAFE_FALLBACK_MESSAGE
    assert result.specialty is None
    assert result.orientation is None


def test_texto_vazio_cai_no_fallback():
    result = parse_structured_response("")
    assert result.status == "ongoing"
    assert result.message == _SAFE_FALLBACK_MESSAGE
    assert result.specialty is None


def test_raciocinio_bruto_vazado_cai_no_fallback_seguro():
    """Regression test for a real production incident: from the 2nd turn of
    a conversation onward, the model sometimes exhausted max_tokens during
    chain-of-thought before emitting the final JSON, and the raw English
    reasoning text (mid-sentence, never meant to be patient-facing) was
    returned to the patient as the answer. This must always degrade to the
    fixed safe message instead, never the raw model text.
    """
    raciocinio_vazado = (
        "Okay, let's tackle this. The patient has a headache in the middle of the eyes, "
        "started this morning, severe, never experienced before. I need to continue the "
        "triage with short, safe questions. First, I should ask about associated symptoms "
        "like nausea, vomiting, visual disturbances, or photophobia, since these could "
        "indicate a more serious condition like a migraine with aura or even something "
        "more urgent. Also, checking if there's any history of similar episodes, recent "
        "trauma, or medication use is important. I need to determine "
        "if there are red flags (like sudden onset, severe symptoms, or new"
    )
    result = parse_structured_response(raciocinio_vazado)
    assert result.status == "ongoing"
    assert result.message == _SAFE_FALLBACK_MESSAGE
    assert "headache" not in result.message
    assert result.specialty is None
    assert result.orientation is None


def test_especialidade_fora_da_lista_fechada_e_descartada():
    raw = (
        '{"status": "diagnosis_concluded", "message": "Triagem concluída.", '
        '"specialty": "cardiologista", "orientation": "resumo"}'
    )
    result = parse_structured_response(raw)
    assert result.status == "diagnosis_concluded"
    assert result.specialty is None
    assert result.orientation == "resumo"


def test_todas_as_12_especialidades_sao_aceitas():
    assert len(ESPECIALIDADES_CONHECIDAS) == 12
    for especialidade in ESPECIALIDADES_CONHECIDAS:
        raw = (
            f'{{"status": "diagnosis_concluded", "message": "ok", '
            f'"specialty": "{especialidade}", "orientation": null}}'
        )
        result = parse_structured_response(raw)
        assert result.specialty == especialidade
