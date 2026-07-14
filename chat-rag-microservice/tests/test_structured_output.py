"""Tests for the structured-output parsing/sanitization contract.

See docs/structured_output_contract.md for the full contract this function
implements.
"""
import pytest

from app.llm.structured_output import ESPECIALIDADES_CONHECIDAS, parse_structured_response


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
    assert result.message == malformado
    assert result.specialty is None
    assert result.orientation is None


def test_texto_vazio_cai_no_fallback():
    result = parse_structured_response("")
    assert result.status == "ongoing"
    assert result.message == ""
    assert result.specialty is None


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
