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
import csv
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv

# Loads chatbot-backend/.env (same directory as this script, regardless of
# cwd) so NVIDIA_API_KEY doesn't have to be exported manually — this script
# runs standalone in a local shell, unlike the FastAPI app and docker
# compose, which already load their own .env files on their own.
# Vars already exported in the shell still take precedence (override=False).
load_dotenv(Path(__file__).resolve().parent / ".env")

# logging.getLogger(__name__) is a de facto singleton — every call with the
# same name returns the same logger instance, and basicConfig only attaches
# a handler to the root logger once. This replaces the old scattered
# print(..., file=sys.stderr) calls with visible per-step progress logs.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# httpx/httpcore also log at INFO ("HTTP Request: ...") — one line per call,
# duplicating the more informative per-step logs below. Silenced separately
# instead of lowering the root level, so warnings from those libraries still
# surface if something goes wrong at the transport layer.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

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


_CAMPOS_CSV_RESUMO = [
    "perfil_id",
    "nome_ficticio",
    "sinais_vitais_fixos",
    "especialidade_esperada",
    "especialidade_retornada",
    "especialidade_bateu",
    "especialidade_nula_apesar_de_concluido",
    "nivel_urgencia_esperado",
    "nivel_urgencia_obtido",
    "nivel_urgencia_bateu",
    "diagnosis_status_final",
    "turnos",
    "limite_de_turnos_atingido",
    "session_id",
    "chat_id",
    "erro",
]

_CAMPOS_CSV_CHAMADAS = ["perfil_id", "chamada", "endpoint", "duracao_ms", "status_code"]

# Normaliza "chat_enqueue_turno_3" / "chat_status_turno_3" para "chat_enqueue" /
# "chat_status", agrupando chamadas do mesmo endpoint entre turnos para o
# cálculo de latência (média/mediana/p95/máxima) por endpoint.
_PADRAO_SUFIXO_TURNO = re.compile(r"_turno_\d+$")


def escrever_csv_resumo(resultados: list[dict], caminho: str) -> None:
    """Write one summary row per simulated patient, for spreadsheet/plotting tools.

    Uses `restval=""` since a patient that failed early (e.g. start_session
    raised) won't have fields set past that point in its log dict.
    """
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=_CAMPOS_CSV_RESUMO, restval="", extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(resultados)


def escrever_csv_chamadas(resultados: list[dict], caminho: str) -> None:
    """Write one row per HTTP call across all patients.

    Kept granular (not pre-aggregated) so latency stats (mean/median/p95/max)
    can be computed per endpoint afterwards, e.g. with pandas groupby.
    """
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=_CAMPOS_CSV_CHAMADAS)
        escritor.writeheader()
        for resultado in resultados:
            perfil_id = resultado.get("perfil_id")
            for chamada in resultado.get("chamadas_http", []):
                escritor.writerow(
                    {
                        "perfil_id": perfil_id,
                        "chamada": chamada["chamada"],
                        "endpoint": _PADRAO_SUFIXO_TURNO.sub("", chamada["chamada"]),
                        "duracao_ms": chamada["duracao_ms"],
                        "status_code": chamada["status_code"],
                    }
                )


def formatar_contexto_vitais(dados_fisiologicos: dict) -> str:
    """Format physiological data as a short bracketed note.

    Prefixed to the first `/chat` message of a simulated patient, standing in
    for a smartwatch reading attached to the start of a triage conversation
    (the production wiring from smartwatch data into the chat context does
    not exist yet — see `RELATORIO_EXECUCAO_SIMULADOR_VITAIS.md`).
    """
    return (
        "[Dados do smartwatch: FC {frequencia_cardiaca} bpm, "
        "SpO2 {saturacao_oxigenio}%, "
        "PA {pressao_arterial_sistolica}/{pressao_arterial_diastolica} mmHg, "
        "Temp {temperatura_corporal}°C]"
    ).format(**dados_fisiologicos)


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
    messages = [
        {"role": "system", "content": "/no_think"},
        {"role": "system", "content": system_prompt},
        *historico,
    ]
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
    conteudo = dados["choices"][0]["message"]["content"]
    if not conteudo:
        logger.warning(f"[{perfil['nome_ficticio']}] resposta vazia do paciente-ator; usando fala de fallback")
        return "Sim, é isso mesmo. Não tenho mais nada a acrescentar."
    return conteudo.strip()


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
    dados_fisiologicos_fixos = perfil.get("dados_fisiologicos_esperados")
    sinais_vitais_fixos = dados_fisiologicos_fixos is not None

    log: dict = {
        "perfil_id": perfil["id"],
        "nome_ficticio": perfil["nome_ficticio"],
        "especialidade_esperada": perfil["especialidade_esperada"],
        "nivel_urgencia_esperado": perfil.get("nivel_urgencia_esperado"),
        "sinais_vitais_fixos": sinais_vitais_fixos,
        "chamadas_http": [],
        "especialidade_nula_apesar_de_concluido": False,
        "erro": None,
    }

    def registrar_chamada(nome: str, duracao_ms: float, status_code: int) -> None:
        log["chamadas_http"].append(
            {"chamada": nome, "duracao_ms": round(duracao_ms, 2), "status_code": status_code}
        )

    nome = perfil["nome_ficticio"]
    logger.info(f"[{nome}] iniciando sessão")

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
        session_id = resp.json()["session_id"]
        log["session_id"] = session_id
        logger.info(f"[{nome}] session_id={session_id}")

        smartwatch_id = f"sim-{perfil['id']}"
        inicio = time.perf_counter()
        resp = await client.get(
            f"{BACKEND_BASE_URL}/get_smartwatch_data/{smartwatch_id}",
            params={"session_id": session_id},
        )
        resp.raise_for_status()
        registrar_chamada("get_smartwatch_data", (time.perf_counter() - inicio) * 1000, resp.status_code)
        logger.info(f"[{nome}] dados do smartwatch obtidos")

        chat_id: str | None = session_id
        historico_llm: list[dict] = []
        especialidade_retornada: str | None = None
        nivel_urgencia_obtido: str | None = None
        diagnosis_status = "ongoing"
        turno = 0
        mensagem_paciente = perfil["sintomas"]

        while turno < MAX_TURNS and diagnosis_status != "diagnosis_concluded":
            turno += 1
            historico_llm.append({"role": "user", "content": mensagem_paciente})

            # Sinais vitais fixos entram só na mensagem enviada ao chatbot em
            # teste (primeiro turno), não no histórico do paciente-ator
            # simulado — este continua vendo/gerando apenas os sintomas
            # verbais. Perfis sem sinais vitais fixos não sofrem alteração.
            mensagem_para_chatbot = mensagem_paciente
            if turno == 1 and sinais_vitais_fixos:
                mensagem_para_chatbot = (
                    f"{formatar_contexto_vitais(dados_fisiologicos_fixos)} {mensagem_paciente}"
                )
            logger.info(f"[{nome}] turno {turno}: enviando: {mensagem_para_chatbot!r}")

            inicio = time.perf_counter()
            resp = await client.post(
                f"{BACKEND_BASE_URL}/chat",
                json={
                    "message": mensagem_para_chatbot,
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
            logger.info(f"[{nome}] turno {turno}: job {enqueue['job_id']} enfileirado, aguardando conclusão")

            inicio = time.perf_counter()
            status_payload = await aguardar_conclusao_job(client, enqueue["job_id"])
            registrar_chamada(f"chat_status_turno_{turno}", (time.perf_counter() - inicio) * 1000, 200)

            if status_payload["status"] == "failed":
                raise SimulacaoError(f"Job {enqueue['job_id']} falhou: {status_payload.get('error')}")

            content = status_payload.get("content") or {}
            resposta_bot = content.get("answer", "")
            diagnosis_status = content.get("diagnosis_status", "ongoing")
            historico_llm.append({"role": "assistant", "content": resposta_bot})
            logger.info(
                f"[{nome}] turno {turno}: recebido (diagnosis_status={diagnosis_status}): {resposta_bot!r}"
            )

            if diagnosis_status == "diagnosis_concluded":
                # Lê o campo estruturado direto (ver docs/structured_output_contract.md
                # no chat-rag-microservice) em vez de extrair por substring do texto livre.
                especialidade_retornada = content.get("specialty")
                nivel_urgencia_obtido = content.get("risk_level")
                if especialidade_retornada is None:
                    # status concluído sem specialty indica falha de parsing do JSON
                    # estruturado no chat-rag-microservice — dado relevante para a
                    # análise de qualidade, não um bug deste script.
                    log["especialidade_nula_apesar_de_concluido"] = True
                logger.info(
                    f"[{nome}] triagem concluída: specialty={especialidade_retornada!r} "
                    f"risk_level={nivel_urgencia_obtido!r}"
                )
                break

            mensagem_paciente = await gerar_resposta_paciente(client, api_key, perfil, historico_llm)

        if diagnosis_status != "diagnosis_concluded":
            logger.info(f"[{nome}] limite de turnos atingido ({turno}) sem concluir a triagem")

        log["turnos"] = turno
        log["diagnosis_status_final"] = diagnosis_status
        log["especialidade_retornada"] = especialidade_retornada
        log["especialidade_bateu"] = (
            especialidade_retornada is not None
            and especialidade_retornada.lower() == perfil["especialidade_esperada"].lower()
        )
        log["nivel_urgencia_obtido"] = nivel_urgencia_obtido
        nivel_urgencia_esperado = log["nivel_urgencia_esperado"]
        log["nivel_urgencia_bateu"] = (
            nivel_urgencia_obtido is not None
            and nivel_urgencia_esperado is not None
            and nivel_urgencia_obtido.lower() == nivel_urgencia_esperado.lower()
        )
        log["limite_de_turnos_atingido"] = turno >= MAX_TURNS and diagnosis_status != "diagnosis_concluded"
    except (httpx.HTTPError, SimulacaoError) as exc:
        logger.error(f"[{nome}] falhou: {exc}")
        log["erro"] = str(exc)

    return log


async def executar(perfis: list[dict], mode: str, api_key: str | None) -> list[dict]:
    resultados = []
    async with httpx.AsyncClient() as client:
        for indice, perfil in enumerate(perfis, start=1):
            logger.info(f"=== Paciente {indice}/{len(perfis)}: {perfil['nome_ficticio']} ===")
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
    parser.add_argument(
        "--saida-csv-resumo", default="resultados_resumo.csv", help="CSV com uma linha por paciente simulado."
    )
    parser.add_argument(
        "--saida-csv-chamadas",
        default="resultados_chamadas.csv",
        help="CSV com uma linha por chamada HTTP (granular, para análise de latência por endpoint).",
    )
    args = parser.parse_args()

    caminho_perfis = Path(args.perfis)
    dados = json.loads(caminho_perfis.read_text(encoding="utf-8"))
    perfis = dados["pacientes"]
    if args.limit is not None:
        perfis = perfis[: args.limit]

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.warning(
            "NVIDIA_API_KEY não definida — o paciente sintético vai responder de forma "
            "determinística (sem LLM), apenas para validar que o script não quebra."
        )

    logger.info(f"Iniciando simulação de {len(perfis)} paciente(s) (mode={args.mode})")
    resultados = asyncio.run(executar(perfis, args.mode, api_key))

    Path(args.saida).write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_csv_resumo(resultados, args.saida_csv_resumo)
    escrever_csv_chamadas(resultados, args.saida_csv_chamadas)
    logger.info(
        f"Log salvo em {args.saida}, resumo em {args.saida_csv_resumo} e chamadas em "
        f"{args.saida_csv_chamadas} ({len(resultados)} paciente(s) simulado(s))."
    )


if __name__ == "__main__":
    main()
