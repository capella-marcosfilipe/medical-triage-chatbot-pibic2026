"""Tests for _infer_diagnosis_status, the keyword heuristic that decides
whether the frontend transitions from nemotron_chat to final_display."""
import pytest

from app.api.v1.endpoints import _infer_diagnosis_status


@pytest.mark.parametrize(
    "answer",
    [
        "Triagem concluída. Encaminhamento sugerido: Clínica Geral.",
        "A conversa finalizada com sucesso.",
        "Segue a ficha de atendimento para o médico.",
        "Recomendo encaminhamento para um cardiologista.",
        "Procure atendimento em uma unidade de saúde o quanto antes.",
        "Procure um serviço de urgência imediatamente.",
        "Este é o diagnóstico final do caso.",
        "O diagnóstico concluído aponta para uma infecção viral.",
        "TRIAGEM CONCLUÍDA, sem mais perguntas.",
    ],
)
def test_marca_como_concluido_quando_ha_marcador(answer):
    assert _infer_diagnosis_status(answer) == "diagnosis_concluded"


@pytest.mark.parametrize(
    "answer",
    [
        "Pode me contar há quanto tempo você sente essa dor?",
        "",
        "a",
        "Estou aqui para ajudar, descreva seus sintomas.",
    ],
)
def test_mantem_ongoing_sem_marcador(answer):
    assert _infer_diagnosis_status(answer) == "ongoing"


def test_nao_conclui_por_engano_em_queixa_muito_longa_sem_marcador():
    # A very long free-text complaint (stress-testing Tarefa 3's "queixa
    # muito longa" scenario) should not accidentally match a concluding
    # marker just because of its length.
    long_answer = "Sinto dor no peito e falta de ar " * 200
    assert _infer_diagnosis_status(long_answer) == "ongoing"
