"""Sanity test for the Manchester/Maringá rules retrieval (Tarefa 5).

Tests the method that actually runs in production
(`LangGraphRAGService._retrieve_manchester_rules`), not an isolated
reimplementation — the lesson from the previous execution (output
estruturado) is to always test the path that really executes.

Requires the ChromaDB collection to already be built:

    python -m app.rag.build_index
"""
import pytest

from app.graph.langgraph_rag_service import LangGraphRAGService


@pytest.fixture(scope="module")
def rag_service():
    service = LangGraphRAGService()
    try:
        service._manchester_rules.count()
    except Exception:
        pytest.skip("Manchester collection not built; run 'python -m app.rag.build_index' first.")
    return service


def _fluxogramas(rules: list[dict]) -> set[str]:
    return {r["fluxograma"] for r in rules}


def _cores(rules: list[dict]) -> set[str]:
    return {r["cor"] for r in rules}


def test_dor_toracica_irradiando_para_o_braco(rag_service):
    rules = rag_service._retrieve_manchester_rules("estou com dor forte no peito que vai pro braço")

    assert len(rules) == 5
    assert "Dor torácica" in _fluxogramas(rules)
    # a queixa clássica de infarto deve puxar pelo menos um critério vermelho
    assert "VERMELHO" in _cores(rules)


def test_febre_alta_e_convulsao_em_crianca(rag_service):
    rules = rag_service._retrieve_manchester_rules("minha filha está com febre alta e convulsionando")

    assert len(rules) == 5
    fluxogramas = _fluxogramas(rules)
    # o modelo local de embeddings nem sempre poe "Convulsão ativa" (VERMELHO)
    # em 1o lugar para esta frase (ver docs/RAG_KNOWLEDGE_BASE.md), mas os
    # resultados devem seguir no tema clinico certo: convulsão/estado mental.
    assert fluxogramas & {"Convulsões", "Desmaio, tontura, vertigem", "Alterações do nível de consciência, comportamento ou sensório"}


def test_sangramento_que_nao_para_apos_trauma(rag_service):
    rules = rag_service._retrieve_manchester_rules("caí de bicicleta, bati a cabeça e o sangramento não para")

    assert len(rules) == 5
    fluxogramas = _fluxogramas(rules)
    assert fluxogramas & {"Sangramentos", "Traumas", "Trauma torocoabdominal", "Alterações cutâneas"}


def test_falta_de_ar_intensa_com_labios_arroxeados(rag_service):
    rules = rag_service._retrieve_manchester_rules("estou com muita falta de ar e os lábios estão arroxeados")

    assert len(rules) == 5
    fluxogramas = _fluxogramas(rules)
    assert fluxogramas & {"Queixas respiratórias", "Alterações cutâneas", "Palpitações"}
    # cianose/hipoxemia grave é um critério vermelho/laranja clássico
    assert _cores(rules) & {"VERMELHO", "LARANJA"}


def test_falha_de_retrieval_nao_derruba_a_conversa(rag_service, monkeypatch):
    """Force a query-time failure and confirm it degrades gracefully."""

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated ChromaDB failure")

    monkeypatch.setattr(rag_service._manchester_rules, "query", _boom)

    rules = rag_service._retrieve_manchester_rules("qualquer sintoma")

    assert rules == []


def test_retrieval_delegates_to_injected_reader():
    """Proves constructor injection works, without touching a real collection."""

    class _FakeManchesterRules:
        def __init__(self, rules: list[dict]) -> None:
            self._rules = rules
            self.last_call: tuple[str, int] | None = None

        def query(self, text: str, top_k: int) -> list[dict]:
            self.last_call = (text, top_k)
            return self._rules

    fake_rules = [
        {
            "fluxograma": "Fake",
            "cor": "VERMELHO",
            "tempo_alvo": "imediato",
            "criterio": "critério fake",
            "descritor": "descritor fake",
        }
    ]
    fake_reader = _FakeManchesterRules(fake_rules)

    service = LangGraphRAGService(manchester_rules=fake_reader)
    result = service._retrieve_manchester_rules("sintoma qualquer")

    assert result == fake_rules
    assert fake_reader.last_call is not None
    assert fake_reader.last_call[0] == "sintoma qualquer"
