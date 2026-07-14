"""Script de simulação automatizada (Dia 11, PIBIC 2025-2026).

Um "paciente sintético" (perfil de `pacientes_sinteticos.json`, com as
respostas geradas por uma chamada separada ao Nemotron, com um system
prompt diferente do chatbot de triagem) conversa com o chatbot de triagem
real (`chatbot-backend` + `chat-rag-microservice`), permitindo medir tempos
de resposta e taxa de acerto da especialidade recomendada.

Não é código de produção: é um script de pesquisa acadêmica, não idempotente,
pensado para rodar localmente contra uma pilha já no ar.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal

import httpx

BACKEND_BASE_URL = os.getenv("CHATBOT_BACKEND_URL", "http://localhost:8001/api/v1")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/nvidia-nemotron-nano-9b-v2"
MAX_TURNS = 15
POLL_INTERVAL_SECONDS = 0.5
POLL_TIMEOUT_SECONDS = 30.0

PATIENT_SYSTEM_PROMPT_TEMPLATE = """Você é um(a) paciente simulado(a) para teste de um chatbot de triagem médica.
Perfil: {nome_ficticio}, {idade} anos, sexo {sexo}.
Condição simulada (NÃO revele o nome da condição, apenas descreva sintomas como um paciente real faria): {condicao_simulada}.
Sintomas de referência: {sintomas}.

Responda SEMPRE em português do Brasil, em 1 a 2 frases curtas, como um paciente
real responderia à pergunta do atendente virtual. Nunca diga que você é uma
simulação."""


class SimulacaoError(Exception):
    """Falha esperada do domínio da simulação (não um bug do script)."""


async def gerar_resposta_paciente(
    client: httpx.AsyncClient,
    api_key: str | None,
    perfil: dict,
    historico: list[dict],
) -> str:
    """Gera a próxima fala do paciente sintético via uma chamada separada ao
    Nemotron (NVIDIA API), com um system prompt de "atuação de paciente" —
    isso é deliberadamente independente do /chat do chatbot em teste."""
    if not api_key:
        # Sem NVIDIA_API_KEY: modo determinístico, só para permitir um
        # smoke-test do script sem credenciais reais.
        if not historico:
            return perfil["sintomas"]
        return "Sim, é isso mesmo. Não tenho mais nada a acrescentar."

    system_prompt = PATIENT_SYSTEM_PROMPT_TEMPLATE.format(**perfil)
    messages = [{"role": "system", "content": system_prompt}, *historico]
    resposta = await client.post(
        NVIDIA_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": NVIDIA_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 128,
        },
        timeout=30.0,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    return dados["choices"][0]["message"]["content"].strip()


async def aguardar_conclusao_job(client: httpx.AsyncClient, job_id: str) -> dict:
    inicio = time.perf_counter()
    while True:
        resp = await client.get(f"{BACKEND_BASE_URL}/chat/status/{job_id}")
        resp.raise_for_status()
        status_payload = resp.json()
        if status_payload["status"] in ("completed", "failed"):
            return status_payload
        if time.perf_counter() - inicio > POLL_TIMEOUT_SECONDS:
            raise SimulacaoError(f"Timeout aguardando o job {job_id}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def simular_paciente(
    client: httpx.AsyncClient,
    perfil: dict,
    api_key: str | None,
    mode: Literal["api", "gpu"],
) -> dict:
    log: dict = {
        "perfil_id": perfil["id"],
        "nome_ficticio": perfil["nome_ficticio"],
        "especialidade_esperada": perfil["especialidade_esperada"],
        "chamadas_http": [],
        "especialidade_nula_apesar_de_concluido": False,
        "erro": None,
    }

    def registrar_chamada(nome: str, duracao_ms: float, status_code: int) -> None:
        log["chamadas_http"].append(
            {"chamada": nome, "duracao_ms": round(duracao_ms, 2), "status_code": status_code}
        )

    try:
        inicio = time.perf_counter()
        resp = await client.post(
            f"{BACKEND_BASE_URL}/start_session",
            json={
                "nome_completo": perfil["nome_ficticio"],
                "endereco": "Endereço simulado para fins de teste, s/n",
                "idade": perfil["idade"],
            },
        )
        resp.raise_for_status()
        registrar_chamada("start_session", (time.perf_counter() - inicio) * 1000, resp.status_code)
        log["session_id"] = resp.json()["session_id"]

        smartwatch_id = f"sim-{perfil['id']}"
        inicio = time.perf_counter()
        resp = await client.get(f"{BACKEND_BASE_URL}/get_smartwatch_data/{smartwatch_id}")
        resp.raise_for_status()
        registrar_chamada("get_smartwatch_data", (time.perf_counter() - inicio) * 1000, resp.status_code)

        chat_id: str | None = None
        historico_llm: list[dict] = []
        especialidade_retornada: str | None = None
        diagnosis_status = "ongoing"
        turno = 0
        mensagem_paciente = perfil["sintomas"]

        while turno < MAX_TURNS and diagnosis_status != "diagnosis_concluded":
            turno += 1
            historico_llm.append({"role": "user", "content": mensagem_paciente})

            inicio = time.perf_counter()
            resp = await client.post(
                f"{BACKEND_BASE_URL}/chat",
                json={
                    "message": mensagem_paciente,
                    "engine": "nemotron",
                    "chat_id": chat_id,
                    # nota: o /chat do chatbot-backend hoje ignora este campo
                    # e sempre usa mode="auto" internamente — ver RELATORIO_EXECUCAO.
                    "mode": mode,
                },
            )
            resp.raise_for_status()
            enqueue = resp.json()
            registrar_chamada(f"chat_enqueue_turno_{turno}", (time.perf_counter() - inicio) * 1000, resp.status_code)
            chat_id = enqueue["chat_id"]
            log["chat_id"] = chat_id

            inicio = time.perf_counter()
            status_payload = await aguardar_conclusao_job(client, enqueue["job_id"])
            registrar_chamada(f"chat_status_turno_{turno}", (time.perf_counter() - inicio) * 1000, 200)

            if status_payload["status"] == "failed":
                raise SimulacaoError(f"Job {enqueue['job_id']} falhou: {status_payload.get('error')}")

            content = status_payload.get("content") or {}
            resposta_bot = content.get("answer", "")
            diagnosis_status = content.get("diagnosis_status", "ongoing")
            historico_llm.append({"role": "assistant", "content": resposta_bot})

            if diagnosis_status == "diagnosis_concluded":
                # Lê o campo estruturado direto (ver docs/structured_output_contract.md
                # no chat-rag-microservice) em vez de extrair por substring do texto livre.
                especialidade_retornada = content.get("specialty")
                if especialidade_retornada is None:
                    # status concluído sem specialty indica falha de parsing do JSON
                    # estruturado no chat-rag-microservice — dado relevante para a
                    # análise de qualidade, não um bug deste script.
                    log["especialidade_nula_apesar_de_concluido"] = True
                break

            mensagem_paciente = await gerar_resposta_paciente(client, api_key, perfil, historico_llm)

        log["turnos"] = turno
        log["diagnosis_status_final"] = diagnosis_status
        log["especialidade_retornada"] = especialidade_retornada
        log["especialidade_bateu"] = (
            especialidade_retornada is not None
            and especialidade_retornada.lower() == perfil["especialidade_esperada"].lower()
        )
        log["limite_de_turnos_atingido"] = turno >= MAX_TURNS and diagnosis_status != "diagnosis_concluded"
    except (httpx.HTTPError, SimulacaoError) as exc:
        log["erro"] = str(exc)

    return log


async def executar(perfis: list[dict], mode: str, api_key: str | None) -> list[dict]:
    resultados = []
    async with httpx.AsyncClient() as client:
        for perfil in perfis:
            resultado = await simular_paciente(client, perfil, api_key, mode)
            resultados.append(resultado)
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simula pacientes sintéticos conversando com o chatbot de triagem real."
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Executa apenas os N primeiros perfis (útil para um piloto rápido)."
    )
    parser.add_argument(
        "--mode", choices=["api", "gpu"], default="api", help="Modo de execução repassado no payload do /chat."
    )
    parser.add_argument(
        "--perfis", default="pacientes_sinteticos.json", help="Caminho para o JSON de pacientes sintéticos."
    )
    parser.add_argument("--saida", default="log_simulacao.json", help="Arquivo de log JSON de saída.")
    args = parser.parse_args()

    caminho_perfis = Path(args.perfis)
    dados = json.loads(caminho_perfis.read_text(encoding="utf-8"))
    perfis = dados["pacientes"]
    if args.limit is not None:
        perfis = perfis[: args.limit]

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print(
            "[AVISO] NVIDIA_API_KEY não definida — o paciente sintético vai responder de forma "
            "determinística (sem LLM), apenas para validar que o script não quebra.",
            file=sys.stderr,
        )

    resultados = asyncio.run(executar(perfis, args.mode, api_key))

    Path(args.saida).write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Log salvo em {args.saida} ({len(resultados)} paciente(s) simulado(s)).")


if __name__ == "__main__":
    main()
