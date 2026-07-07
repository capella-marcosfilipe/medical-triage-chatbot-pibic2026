# API Documentation

## Base URL

- **Local Development**: `http://localhost:8001/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Interactive Documentation

Once the server is running, access the interactive documentation at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy"
}
```

---

### 2. Initialize Patient Session

Start a new medical triage session.

**Endpoint**: `POST /api/v1/iniciar_atendimento`

**Request Body**:
```json
{
  "nome_completo": "João Silva",
  "endereco": "Rua Exemplo, 123, Cidade-UF",
  "idade": 35
}
```

**Response**: `200 OK`
```json
{
  "session_id": "uuid-v4-string",
  "message": "Atendimento iniciado com sucesso"
}
```

**Errors**:
- `422 Unprocessable Entity`: Invalid input data
- `500 Internal Server Error`: Server error

---

### 3. Get Smartwatch Data

Retrieve simulated physiological data from a smartwatch.

**Endpoint**: `GET /api/v1/obter_dados_smartwatch/{session_id}`

**Parameters**:
- `session_id` (path, required): Session UUID

**Response**: `200 OK`
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

**Errors**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Server error

**Notes**:
- Data is simulated with realistic values
- Each call may return different values
- Values are within normal physiological ranges

---

### 4. Chat with Nemotron AI

Send a message and receive AI-powered medical triage response.

**Endpoint**: `POST /api/v1/chat`

**Request Body**:
```json
{
  "message": "Estou com febre e dor de cabeça há 2 dias",
  "engine": "nemotron"
}
```

**Response**: `202 Accepted`
```json
{
  "job_id": "uuid-v4-string",
  "chat_id": "uuid-v4-string",
  "status": "pending",
  "idempotency_key": "hash-da-requisicao",
  "queue": "chatbot-microservice"
}
```

**Errors**:
- `500 Internal Server Error`: Server error or AI service unavailable

**Notes**:
- Requires Google Gemini API key to be configured
- `chat_id` is omitted on the first request and returned by the backend
- The backend now returns an asynchronous job reference instead of the final AI answer

### 5. Chat Status

Check the current state of a chat job.

**Endpoint**: `GET /api/v1/chat/status/{job_id}`

**Response**:
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

**Notes**:
- `content` only appears after the LLM response is available
- `diagnosis_status` is either `ongoing` or `diagnosis_concluded`

### 6. Resume Conversation

Retrieve the full message history for a chat session.

**Endpoint**: `GET /api/v1/chat/{chat_id}`

**Response**:
```json
{
  "chat_id": "uuid-v4-string",
  "messages": [
    { "role": "user", "content": "Estou com febre" },
    { "role": "assistant", "content": "Há quanto tempo você está com febre?" }
  ]
}
```

---

### 7. Get Complete Medical Record

Retrieve the complete medical record for a session.

**Endpoint**: `GET /api/v1/obter_ficha_completa/{session_id}`

**Parameters**:
- `session_id` (path, required): Session UUID

**Response**: `200 OK`
```json
{
  "ficha_de_atendimento": {
    "session_id": "uuid-v4-string",
    "nome_completo": "João Silva",
    "endereco": "Rua Exemplo, 123, Cidade-UF",
    "idade": 35,
    "dados_fisiologicos": {
      "frequencia_cardiaca": 75,
      "saturacao_oxigenio": 98,
      "pressao_arterial_sistolica": 120,
      "pressao_arterial_diastolica": 80,
      "temperatura_corporal": 36.5
    },
    "queixa_principal": "Febre e dor de cabeça",
    "historico_sintomas": "Sintomas iniciaram há 2 dias com febre de 38.5°C",
    "historico_doencas_previas": "Hipertensão controlada",
    "alergias": "Penicilina",
    "medicamentos_em_uso": "Losartana 50mg",
    "nivel_urgencia": "MÉDIA",
    "especialidade_medica": "Clínica Geral",
    "orientacao_ao_medico": "Paciente apresenta quadro febril com cefaleia. Avaliar sinais de infecção viral ou bacteriana."
  }
}
```

**Errors**:
- `404 Not Found`: Session not found

**Notes**:
- Can be called at any time during or after the session
- Medical information may be incomplete if called before conversation finalization

---

## Data Models

### PacienteData

```typescript
{
  nome_completo: string;  // Full name
  endereco: string;       // Full address
  idade: number;          // Age (0-120)
}
```

### DadosFisiologicos

```typescript
{
  frequencia_cardiaca: number;       // Heart rate (BPM)
  saturacao_oxigenio: number;        // O2 saturation (0-100%)
  pressao_arterial_sistolica: number; // Systolic BP (mmHg)
  pressao_arterial_diastolica: number; // Diastolic BP (mmHg)
  temperatura_corporal: number;      // Body temp (°C)
}
```

### FichaDeAtendimento

```typescript
{
  session_id: string;
  nome_completo: string;
  endereco: string;
  idade: number;
  dados_fisiologicos: DadosFisiologicos | null;
  queixa_principal: string | null;
  historico_sintomas: string | null;
  historico_doencas_previas: string | null;
  alergias: string | null;
  medicamentos_em_uso: string | null;
  nivel_urgencia: "BAIXA" | "MÉDIA" | "ALTA" | null;
  especialidade_medica: string | null;
  orientacao_ao_medico: string | null;
}
```

---

## Typical Workflow

1. **Start Session**: Call `POST /api/v1/iniciar_atendimento` with patient data
2. **Get Vitals**: Call `GET /api/v1/obter_dados_smartwatch/{session_id}`
3. **Chat Loop**: Call `POST /api/v1/chat` repeatedly, reusing the returned `chat_id`
4. **Get Record**: (Optional) Call `GET /api/v1/obter_ficha_completa/{session_id}`

---

## Example Usage

### JavaScript/Fetch

```javascript
const BASE_URL = 'http://localhost:8001/api/v1';

// 1. Start session
const response1 = await fetch(`${BASE_URL}/iniciar_atendimento`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nome_completo: 'João Silva',
    endereco: 'Rua Exemplo, 123',
    idade: 35
  })
});
const { session_id } = await response1.json();

// 2. Get smartwatch data
const response2 = await fetch(`${BASE_URL}/obter_dados_smartwatch/${session_id}`);
const smartwatch = await response2.json();

// 3. Chat
const response3 = await fetch(`${BASE_URL}/chat_with_gemini`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    user_message: 'Estou com febre'
  })
});
const chat = await response3.json();
```

### Python/Requests

```python
import requests

BASE_URL = 'http://localhost:8001/api/v1'

# 1. Start session
response = requests.post(f'{BASE_URL}/iniciar_atendimento', json={
    'nome_completo': 'João Silva',
    'endereco': 'Rua Exemplo, 123',
    'idade': 35
})
session_id = response.json()['session_id']

# 2. Get smartwatch data
response = requests.get(f'{BASE_URL}/obter_dados_smartwatch/{session_id}')
smartwatch = response.json()

# 3. Chat
response = requests.post(f'{BASE_URL}/chat_with_gemini', json={
    'session_id': session_id,
    'user_message': 'Estou com febre'
})
chat = response.json()
```

### cURL

```bash
# 1. Start session
SESSION_ID=$(curl -s -X POST http://localhost:8001/api/v1/iniciar_atendimento \
  -H "Content-Type: application/json" \
  -d '{"nome_completo":"João Silva","endereco":"Rua Exemplo, 123","idade":35}' \
  | jq -r '.session_id')

# 2. Get smartwatch data
curl http://localhost:8001/api/v1/obter_dados_smartwatch/$SESSION_ID

# 3. Chat
curl -X POST http://localhost:8001/api/v1/chat_with_gemini \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"user_message\":\"Estou com febre\"}"
```

---

## Rate Limiting

Currently, there are no rate limits. For production use, consider implementing:
- Per-IP rate limiting
- Per-session rate limiting
- API key authentication

---

## CORS

The API allows all origins by default. In production, update `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message here"
}
```
