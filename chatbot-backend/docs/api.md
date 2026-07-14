# API Documentation

## Base URL

- Local Development: `http://localhost:8001/api/v1`

## Interactive Docs

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Endpoints

### Health Check

`GET /health`

Response:
```json
{ "status": "healthy" }
```

### Initialize Patient Session

`POST /api/v1/start_session`

Request:
```json
{
  "nome_completo": "João Silva",
  "endereco": "Rua Exemplo, 123, Cidade-UF",
  "idade": 35
}
```

Response:
```json
{
  "session_id": "uuid-gerado",
  "message": "Atendimento iniciado com sucesso"
}
```

### Get Smartwatch Data

`GET /api/v1/get_smartwatch_data/{smartwatch_id}`

Notes:
- The identifier comes from the device/database that stores the physiological data.
- The endpoint remains mocked and does not depend on the patient session.

Response:
```json
{
  "dados_fisiologicos": {
    "frequencia_cardiaca": 75,
    "saturacao_oxigenio": 98,
    "pressao_arterial_sistolica": 120,
    "pressao_arterial_diastolica": 80,
    "temperatura_corporal": 36.5
  }
}
```

### Chat

`POST /api/v1/chat`

Request:
```json
{
  "message": "Estou com febre e dor de cabeça há 2 dias",
  "engine": "nemotron"
}
```

Response:
```json
{
  "job_id": "uuid-v4-string",
  "chat_id": "uuid-v4-string",
  "status": "pending",
  "idempotency_key": "hash-da-requisicao",
  "queue": "chat-rag-microservice"
}
```

### Chat Status

`GET /api/v1/chat/status/{job_id}`

Response:
```json
{
  "job_id": "uuid-v4-string",
  "chat_id": "uuid-v4-string",
  "status": "completed",
  "idempotency_key": "hash-da-requisicao",
  "created_at": "2026-07-07T12:00:00",
  "content": {
    "answer": "...",
    "processing_time_ms": 1240.3,
    "diagnosis_status": "ongoing"
  },
  "error": null
}
```

### Resume Conversation

`GET /api/v1/chat/{chat_id}`

Response:
```json
{
  "chat_id": "uuid-v4-string",
  "messages": [
    { "role": "user", "content": "Estou com febre" },
    { "role": "assistant", "content": "Há quanto tempo você está com febre?" }
  ]
}
```

### Get Complete Medical Record

`GET /api/v1/obter_ficha_completa/{session_id}`

## Data Models

- `PacienteData`: patient profile used to open a session.
- `DadosFisiologicos`: mocked smartwatch vitals.
- `ChatNemotronRequest`: chat payload with `message`, `engine`, and optional `chat_id`.
- `NLPJobStatusResponse`: async job status, `chat_id`, and optional `content`.
