# Medical Triage Chatbot

LLM-powered chatbot that conducts the initial triage of emergency-room patients, grounded on the **Manchester Triage Protocol** through RAG. Developed as a scientific initiation research project (**PIBIC 2025–2026**) at the Catholic University of Pernambuco (UNICAP).

The patient talks to the chatbot in natural language; the system combines the conversation with (simulated) smartwatch vital signs, retrieves the relevant Manchester criteria and produces a structured triage record: urgency level (red → blue) and recommended medical specialty.

> ⚠️ Research prototype. Not a medical device and not meant for real clinical use.

## Architecture

```text
┌────────────────────┐     ┌────────────────────┐     ┌──────────────────────────────┐
│  chatbot-frontend  │────▶│  chatbot-backend   │────▶│     chat-rag-microservice     │
│  Angular (4200)    │     │  FastAPI (8001)    │     │  FastAPI edge (8010)          │
│  patient flow, LGPD│     │  sessions, vitals  │     │  LangGraph + RAG + Nemotron   │
│  consent, chat UI  │     │  simulator, record │     └──────┬─────────────────┬──────┘
└────────────────────┘     └────────────────────┘            │ jobs            │ status / memory
                                                     ┌──────▼──────┐   ┌──────▼──────┐
                                                     │  RabbitMQ   │   │    Redis    │
                                                     └──────┬──────┘   └─────────────┘
                                                     ┌──────▼──────────────────────┐
                                                     │ Workers: NVIDIA API / GPU   │
                                                     └─────────────────────────────┘
```

| Service | Role | Stack |
|---|---|---|
| [`chatbot-frontend`](chatbot-frontend) | Patient journey: welcome, LGPD consent, name/age/address, smartwatch reading, chat, final record | Angular |
| [`chatbot-backend`](chatbot-backend) | Patient sessions, smartwatch vital-signs simulator, structured data collection, triage record generation | FastAPI, Pydantic |
| [`chat-rag-microservice`](chat-rag-microservice) | Conversational orchestration with LangGraph, RAG over the Manchester protocol, async LLM jobs | FastAPI, LangGraph, ChromaDB, Sentence Transformers, RabbitMQ, Redis, NVIDIA Nemotron |

### RAG over the Manchester Protocol

- **Source:** Manchester-based risk classification protocol (24 flowcharts) parsed into **415 structured rules** (`flowchart`, `color`, `target time`, `criterion`, `descriptor`).
- **Chunking:** one rule = one chunk.
- **Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2`, run locally (no external API in the indexing/retrieval path).
- **Vector store:** ChromaDB with cosine similarity, metadata stored alongside each vector.
- **Output:** the LLM answers following a structured output contract, validated before reaching the backend.

### Async LLM execution

`POST /v1/chat?mode={auto|gpu|api}` returns a `job_id` right away; the job is routed to a GPU or NVIDIA API queue on RabbitMQ, processed by a worker and its result stored in Redis, polled via `GET /v1/chat/status/{job_id}`. Redis also keeps the LangGraph conversation memory window.

## Evaluation

The repository includes the research tooling used to evaluate the system:

- **Synthetic patients** (`chatbot-backend/pacientes_sinteticos.json`): profiles with expected specialty and urgency level.
- **Patient-actor simulator** (`chatbot-backend/simulador.py`): a second LLM role-plays each patient against the real stack, logging latency, turns, and whether specialty and urgency match the expected values.
- **Load testing** with Locust (`chatbot-backend/locustfile.py`).
- **Unit tests** for structured output, Manchester retrieval and memory window (`pytest`).
- Pilot transcripts for qualitative analysis (`chatbot-backend/transcricoes`).

## Running

Requirements: Docker and a free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com).

```bash
cp .env.example .env          # set NVIDIA_API_KEY
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:4200 | Frontend |
| http://localhost:8001/docs | Backend Swagger |
| http://localhost:8010/docs | RAG microservice Swagger |
| http://localhost:15672 | RabbitMQ management (guest/guest) |

Each service README documents how to run it standalone.

## Author

**Marcos Filipe Capella** — [LinkedIn](https://www.linkedin.com/in/capella-marcosfilipe) · [marcoscapella.com.br](https://marcoscapella.com.br)
PIBIC 2025–2026, Universidade Católica de Pernambuco.
