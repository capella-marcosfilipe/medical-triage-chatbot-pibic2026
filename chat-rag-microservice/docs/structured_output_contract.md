# Contrato de saída estruturada do LLM de triagem

Toda resposta do LLM de triagem, em qualquer turno da conversa, deve ser um único objeto JSON (sem cercas de código Markdown, sem texto antes ou depois) com este formato:

```json
{
  "status": "ongoing",
  "message": "texto conversacional a ser exibido ao paciente",
  "specialty": null,
  "orientation": null
}
```

Quando a triagem é concluída:

```json
{
  "status": "diagnosis_concluded",
  "message": "texto de encerramento a ser exibido ao paciente",
  "specialty": "Cardiologia",
  "orientation": "resumo clínico objetivo para o médico que vai atender"
}
```

## Campos

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `status` | `"ongoing" \| "diagnosis_concluded"` | sim | Mesmo vocabulário já usado em `diagnosis_status` no restante do sistema. |
| `message` | `string` | sim | Texto a ser exibido ao paciente. Nunca deve conter o JSON bruto nem instruções internas. |
| `specialty` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Deve ser **exatamente** uma das 12 strings da lista fechada abaixo — nunca uma variação livre. |
| `orientation` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Resumo clínico objetivo para o médico, não para o paciente. |

## Lista fechada de especialidades

A mesma lista de 12 especialidades usada em `chatbot-backend/pacientes_sinteticos.json` (Dia 10), para que a comparação com `especialidade_esperada` no dataset sintético seja uma comparação exata de string:

Cardiologia, Neurologia, Pneumologia, Gastroenterologia, Ortopedia, Pediatria, Clínica Geral, Urologia, Dermatologia, Psiquiatria, Oftalmologia, Otorrinolaringologia.

`Clínica Geral` também serve de escolha padrão quando nenhuma especialidade mais específica se aplica claramente.

## Onde isso é aplicado

- **System prompt**: `chat-rag-microservice/app/graph/langgraph_rag_service.py`, método `register_user_message` — o prompt de sistema instrui o modelo a seguir este contrato em toda resposta.
- **Parsing/sanitização**: `chat-rag-microservice/app/llm/structured_output.py` — remove cercas Markdown acidentais, tenta `json.loads`, e cai num fallback seguro (`status="ongoing"`, `message=<texto bruto>`, `specialty=None`, `orientation=None`, com `logger.warning`) se o parsing falhar por qualquer motivo (JSON inválido, campos faltando, `specialty` fora da lista fechada, `status` com valor inesperado).
- **Consumo**: `chatbot-backend/app/models/async_schemas.py` (`NLPJobContent.specialty`/`.orientation`), `chatbot-frontend` (`final-display-page`) e `simulador.py` passam a ler os campos estruturados diretamente, em vez de inferir a partir de texto livre.

## Nota importante sobre onde a chamada ao LLM realmente acontece

Antes desta correção, havia um módulo `app/graph/nodes/generation.py` (+ `app/graph/workflow.py`) que parecia o ponto de integração do LLM, mas era (e continua sendo) um placeholder morto — nada no código chama `build_chat_graph()`/`generate_reply()`. A chamada real acontece via `app/presentation/chat.py` → `LangGraphRAGService` (este mesmo arquivo) → fila RabbitMQ → `app/worker/api_worker.py`/`gpu_worker.py` → `app/worker/strategy.py` → `app/llm/nemotron_service.py`. Esta correção foi aplicada nesse caminho real, não no stub. Ver `RELATORIO_EXECUCAO_OUTPUT_ESTRUTURADO.md` para mais detalhes.
