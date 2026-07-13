# Chatbot Triagem Médica - Backend API

Sistema de triagem médica inteligente usando FastAPI e Google Gemini AI. Este projeto é compatível com o frontend legado [chatbot-triagem-medica-front](https://github.com/capella-marcosfilipe/chatbot-triagem-medica-front).

## 🏗️ Arquitetura

- **FastAPI**: Framework web moderno e rápido para construção de APIs
- **Google Gemini AI**: LLM (Large Language Model) para conversação inteligente
- **Pydantic**: Validação de dados e serialização
- **Python 3.8+**: Linguagem de programação

## 📋 Funcionalidades

- ✅ API REST completa para triagem médica
- ✅ Integração com Google Gemini AI
- ✅ Simulador de dados de smartwatch (frequência cardíaca, saturação de O2, pressão arterial, temperatura)
- ✅ Gerenciamento de sessões de pacientes
- ✅ Coleta estruturada de informações médicas
- ✅ Geração automática de ficha de atendimento
- ✅ Suporte a CORS para integração com frontend
- ✅ Documentação interativa (Swagger/OpenAPI)

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Chave da API do Google Gemini ([obter aqui](https://ai.google.dev/))

### Passos de Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/capella-marcosfilipe/chatbot-triagem-medica-pibic25-26.git
cd chatbot-triagem-medica-pibic25-26
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da API do Google Gemini:
```
GOOGLE_API_KEY=sua_chave_aqui
```

5. **Execute o servidor:**
```bash
python main.py
```

O servidor estará disponível em `http://localhost:8001`

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Endpoints Principais

#### 1. Iniciar Atendimento
```http
POST /api/v1/start_session
Content-Type: application/json

{
  "nome_completo": "João Silva",
  "endereco": "Rua Exemplo, 123, Cidade-UF",
  "idade": 35
}
```

**Resposta:**
```json
{
  "session_id": "uuid-gerado",
  "message": "Atendimento iniciado com sucesso"
}
```

> Alias legado: `POST /api/v1/iniciar_atendimento` continua funcionando e delega para `/start_session`.

#### 2. Obter Dados do Smartwatch
```http
GET /api/v1/get_smartwatch_data/{smartwatch_id}
```

O identificador vem do dispositivo/módulo de origem dos dados fisiológicos; a rota não depende da sessão do paciente.

**Resposta:**
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

#### 3. Chat com Nemotron
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Estou com febre e dor de cabeça há 2 dias",
  "engine": "nemotron"
}
```

**Resposta:**
```json
{
  "job_id": "uuid-do-job",
  "chat_id": "uuid-da-conversa",
  "status": "pending",
  "idempotency_key": "hash-da-requisicao",
  "queue": "chat-rag-microservice"
}
```

Na primeira mensagem, `chat_id` não precisa ser enviado; o backend gera esse identificador e o retorna para as próximas mensagens.

#### 4. Status do Chat
```http
GET /api/v1/chat/status/{job_id}
```

**Resposta:**
```json
{
  "job_id": "uuid-do-job",
  "chat_id": "uuid-da-conversa",
  "status": "completed",
  "idempotency_key": "hash-da-requisicao",
  "created_at": "2026-07-07T12:00:00",
  "content": {
    "answer": "...",
    "processing_time_ms": 1420.55,
    "diagnosis_status": "ongoing"
  },
  "error": null
}
```

Quando o job ainda não tiver resposta do LLM, `content` fica ausente e `status` continua refletindo o estado do processamento.

#### 5. Retomar Conversa
```http
GET /api/v1/chat/{chat_id}
```

**Resposta:**
```json
{
  "chat_id": "uuid-da-conversa",
  "messages": [
    { "role": "user", "content": "Estou com febre" },
    { "role": "assistant", "content": "Há quanto tempo você está com febre?" }
  ]
}
```

#### 6. Obter Ficha Completa
```http
GET /api/v1/obter_ficha_completa/{session_id}
```

**Resposta:**
```json
{
  "ficha_de_atendimento": {
    "session_id": "uuid-da-sessao",
    "nome_completo": "João Silva",
    "endereco": "Rua Exemplo, 123",
    "idade": 35,
    "dados_fisiologicos": {...},
    "queixa_principal": "Febre e dor de cabeça",
    "historico_sintomas": "Sintomas iniciaram há 2 dias",
    "historico_doencas_previas": "Não informado",
    "alergias": "Não possui",
    "medicamentos_em_uso": "Não está usando",
    "nivel_urgencia": "MÉDIA",
    "especialidade_medica": "Clínica Geral",
    "orientacao_ao_medico": "Investigar possível quadro viral..."
  }
}
```

## 🔧 Configuração

### Variáveis de Ambiente

Edite o arquivo `.env` para personalizar as configurações:

```bash
# Google Gemini API
GOOGLE_API_KEY=sua_chave_da_api_gemini

# Configurações da Aplicação
APP_HOST=0.0.0.0
APP_PORT=8001
DEBUG=False

# CORS
FRONTEND_URL=http://localhost:4200
```

## 🧪 Testando a API

### Usando cURL

```bash
# Iniciar atendimento
curl -X POST http://localhost:8001/api/v1/start_session \
  -H "Content-Type: application/json" \
  -d '{"nome_completo":"João Silva","endereco":"Rua Exemplo, 123","idade":35}'

# Obter dados do smartwatch
curl http://localhost:8001/api/v1/obter_dados_smartwatch/SESSION_ID

# Chat com Nemotron
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Estou com febre","engine":"nemotron"}'
```

### Usando Python

```python
import requests

BASE_URL = "http://localhost:8001/api/v1"

# Iniciar atendimento
response = requests.post(f"{BASE_URL}/start_session", json={
    "nome_completo": "João Silva",
    "endereco": "Rua Exemplo, 123",
    "idade": 35
})
session_id = response.json()["session_id"]

# Obter dados do smartwatch
response = requests.get(f"{BASE_URL}/obter_dados_smartwatch/{session_id}")
print(response.json())

# Chat com Nemotron
response = requests.post(f"{BASE_URL}/chat", json={
  "message": "Estou com febre há 2 dias",
  "engine": "nemotron"
})
print(response.json())
```

## 🎨 Integração com Frontend

Este backend é compatível com o [frontend legado](https://github.com/capella-marcosfilipe/chatbot-triagem-medica-front).

Para conectar o frontend:

1. No arquivo `script.js` do frontend, configure o `API_BASE_URL`:
```javascript
const API_BASE_URL = "http://localhost:8001/api/v1";
```

2. Certifique-se de que o backend está rodando
3. Abra o frontend em um navegador

## 📦 Estrutura do Projeto

```
chatbot-triagem-medica-pibic25-26/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py         # Endpoints da API
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Configurações
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Modelos Pydantic
│   └── services/
│       ├── __init__.py
│       ├── gemini_service.py        # Serviço Gemini AI
│       ├── session_manager.py       # Gerenciamento de sessões
│       └── smartwatch_simulator.py  # Simulador de smartwatch
├── main.py                          # Aplicação principal FastAPI
├── requirements.txt                 # Dependências
├── .env.example                     # Exemplo de variáveis de ambiente
├── .gitignore
└── README.md
```

## 🛠️ Desenvolvimento

### Executando em modo de desenvolvimento

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Adicionando novas dependências

```bash
pip install nome-do-pacote
pip freeze > requirements.txt
```

## 🚀 Deploy

### Deploy no Render

1. Crie uma conta no [Render](https://render.com)
2. Conecte seu repositório GitHub
3. Crie um novo Web Service
4. Configure as variáveis de ambiente (GOOGLE_API_KEY)
5. O Render detectará automaticamente o `requirements.txt` e o Python

### Deploy no Heroku

```bash
# Crie um Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create seu-app-name
heroku config:set GOOGLE_API_KEY=sua_chave
git push heroku main
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- Marcos Filipe Capella

## 🔗 Links Úteis

- [Frontend Legacy](https://github.com/capella-marcosfilipe/chatbot-triagem-medica-front)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini AI](https://ai.google.dev/)
- [Pydantic](https://docs.pydantic.dev/)