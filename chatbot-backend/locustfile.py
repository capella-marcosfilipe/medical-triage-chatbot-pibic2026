"""Teste de carga (Dia 12, PIBIC 2025-2026) do início do fluxo de triagem.

Simula usuários chamando, em sequência: POST /start_session,
GET /get_smartwatch_data/{smartwatch_id} e POST /chat (uma mensagem).

Não é código de produção — script de pesquisa acadêmica para medir
comportamento do chatbot-backend sob carga concorrente. Requer a pilha
completa no ar (chatbot-backend + chat-rag-microservice + RabbitMQ + Redis)
para que /chat seja de fato processado; sem o microserviço, as chamadas a
/chat vão falhar com 502, o que é esperado e não é um bug deste script.

Uso: rodar de dentro de chatbot-backend/.

    locust -f locustfile.py --host http://localhost:8001/api/v1

Os três cenários de concorrência pedidos (10, 25 e 50 usuários) — os
comandos exatos também estão documentados no RELATORIO_EXECUCAO_CLAUDE_CODE.md:

    locust -f locustfile.py --host http://localhost:8001/api/v1 \
        --users 10 --spawn-rate 2 --run-time 2m --headless

    locust -f locustfile.py --host http://localhost:8001/api/v1 \
        --users 25 --spawn-rate 5 --run-time 2m --headless

    locust -f locustfile.py --host http://localhost:8001/api/v1 \
        --users 50 --spawn-rate 10 --run-time 2m --headless
"""
import random
import uuid

from locust import HttpUser, between, task


class PacienteTriagemUser(HttpUser):
    """Simula um paciente percorrendo o início do fluxo de triagem."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.smartwatch_id = f"locust-{uuid.uuid4().hex[:8]}"

    @task
    def fluxo_completo(self) -> None:
        payload_sessao = {
            "nome_completo": f"Paciente Locust {random.randint(1, 100_000)}",
            "endereco": "Rua de Teste de Carga, s/n",
            "idade": random.randint(1, 120),
        }
        with self.client.post(
            "/start_session", json=payload_sessao, name="/start_session", catch_response=True
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"start_session retornou {resposta.status_code}")
                return

        with self.client.get(
            f"/get_smartwatch_data/{self.smartwatch_id}",
            name="/get_smartwatch_data/[id]",
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"get_smartwatch_data retornou {resposta.status_code}")

        with self.client.post(
            "/chat",
            json={
                "message": "Estou com dor de cabeça e febre desde ontem.",
                "engine": "nemotron",
                "chat_id": None,
            },
            name="/chat",
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 202:
                resposta.failure(f"chat retornou {resposta.status_code}")
