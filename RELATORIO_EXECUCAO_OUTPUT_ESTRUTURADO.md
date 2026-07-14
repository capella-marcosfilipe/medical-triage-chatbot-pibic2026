# Relatório de Execução — Output Estruturado do Nemotron

Execução do prompt `prompt-claude-code-output-estruturado.md`. 8 commits, um por tarefa, sem coautoria (`git log 2381d72..e28f71f` cobre as Tarefas 1-6; a Tarefa 0 não gerou commit próprio, é só investigação). **Nada foi pushado para o remoto.**

## Tarefa 0 — Investigação do estado atual (achado principal desta execução)

1. **`chat-rag-microservice/app/graph/nodes/generation.py` continua um placeholder** (`return state`) — e mais que isso: **todo o módulo `app/graph/{workflow.py,nodes/}` é código morto**. `build_chat_graph()` (`workflow.py`) monta um grafo `START → END` sem nenhum node, e nada no repositório chama essa função (confirmei via grep). Não é só "ainda não implementado" — é um caminho que não está conectado a nada.
2. **A chamada real ao LLM acontece em outro lugar completamente diferente**: `app/presentation/chat.py` (`POST /chat`) → `LangGraphRAGService` (`app/graph/langgraph_rag_service.py` — nome parecido com o módulo morto do item 1, mas é uma classe separada, com seu próprio grafo trivial `persist` só para checkpointing) → fila RabbitMQ → `app/worker/api_worker.py`/`gpu_worker.py` → `app/worker/strategy.py` → `app/llm/nemotron_service.py` → API da NVIDIA. Apliquei a correção **neste caminho real**, não no stub. Isso está documentado tanto no relatório quanto em `docs/structured_output_contract.md`.
3. **O system prompt já existe** (ao contrário do que eu esperava antes de investigar): vive em `LangGraphRAGService.register_user_message`, injetado como `SystemMessage` no primeiro turno da sessão. Ele **não** era passado como mensagem `system` de verdade para a API da NVIDIA — `LangGraphRAGService.build_augmented_prompt` achata toda a memória (incluindo o bloco de sistema) num único texto `[SYSTEM]/[PACIENTE]/[ASSISTENTE]` que vira o conteúdo de uma única mensagem `user` (`nemotron_service._build_messages` não usa `role: "system"` para nada além do modo `/think`). Antes desta correção, o prompt não instruía **nenhum** formato de saída.
4. **Achado bônus, sem necessidade de mudança**: `ChatRequest.patient_context` (nome, idade, endereço, dados fisiológicos) chega corretamente e é usado — `register_user_message` inclui o contexto do paciente no bloco de sistema. Não é um dado descartado, como eu cheguei a suspeitar antes de ler o código.
5. `app/domain/response.py` (`ChatResponse`) e `chatbot-backend/app/models/async_schemas.py` (`NLPJobContent`) confirmados exatamente como descritos no prompt original.

## Tarefa 1 — Contrato de saída estruturada

- Documentado em `chat-rag-microservice/docs/structured_output_contract.md`: contrato JSON `{status, message, specialty, orientation}`, tabela de campos, lista fechada das 12 especialidades (mesmas de `pacientes_sinteticos.json`), e uma nota explicando o achado da Tarefa 0 sobre o node morto.
- System prompt atualizado em `LangGraphRAGService.register_user_message` (não em `generation.py` — ver Tarefa 0) com o formato obrigatório e a lista fechada de especialidades.
- **Decisão a revisar**: como o "system prompt" hoje vira texto dentro de uma mensagem `user` (achado da Tarefa 0), não criei uma mensagem `role: "system"` de verdade na chamada à API — só estendi o texto que já é injetado dessa forma. Mudar a arquitetura de mensagens está fora do escopo desta correção focada.

## Tarefa 2 — Parsing e sanitização

- `app/llm/structured_output.py`: `parse_structured_response()` remove cercas Markdown, tenta `json.loads`, valida `status` (`ongoing`/`diagnosis_concluded`), `message` (string não vazia) e `specialty` (deve estar na lista fechada de 12 — se não estiver, é descartado com `logger.warning`, não repassado). Qualquer falha cai no fallback `status="ongoing", message=<texto bruto>, specialty=None, orientation=None`, sempre com `logger.warning` (nunca silenciosamente).
- `ChatResponse` (`app/domain/response.py`) ganhou `status`, `message`, `specialty`, `orientation`, **mantendo** `response`/`mode`/`latency_ms`.
- **Decisão a revisar**: mantive o campo `response` (em vez de só ter `message`) porque `LangGraphRAGService.sync_assistant_from_job` (chamado em `presentation/chat.py`) lê `result.result.response` para persistir a fala do assistente na memória da conversa — se eu removesse `response`, quebraria essa sincronização. `response` agora espelha `message` (o texto já sanitizado, nunca o JSON bruto).
- Conectado em `app/worker/base_worker.py._process_with_retry`, logo após `generate_response()` retornar o texto bruto do LLM.

## Tarefa 3 — Propagação no `chatbot-backend`

- `NLPJobContent` ganhou `specialty`/`orientation` (Optional[str]), mantendo `answer`/`processing_time_ms`/`diagnosis_status`.
- Nova função `_resolve_diagnosis_content(response_payload)`: prefere `status`/`specialty`/`orientation` estruturados vindos do chat-rag-microservice; só cai em `_infer_diagnosis_status(answer)` (a heurística antiga) quando o payload não traz esses campos — defesa em profundidade para uma versão antiga do microserviço rodando durante a transição.
- `_infer_diagnosis_status` **não foi removida**, só isolada com um comentário deixando claro que agora é fallback, não caminho principal. Seus testes originais (`test_diagnosis_status.py`) continuam existindo e passando, porque a função continua viva.

## Tarefa 4 — Frontend

- `NLPJobContent` (frontend) ganhou `specialty?`/`orientation?`.
- `NemotronChatService`: removi o antigo `finalAnswer` (texto bruto) e adicionei `finalSpecialty`/`finalOrientation`, populados a partir dos campos estruturados quando `diagnosis_status` vira `diagnosis_concluded`.
- `final-display-page`: não exibe mais `content.answer` inteiro como "Orientação ao médico". Agora tem uma seção "Especialidade recomendada" com destaque visual (badge colorido) e uma seção "Orientação ao médico" separada, cada uma com sua própria mensagem de fallback ("não disponível para esta sessão") quando o campo vem `null`/`undefined`.

## Tarefa 5 — `simulador.py`

- Removi `extrair_especialidade()` e a constante `ESPECIALIDADES_CONHECIDAS` (a extração por substring não é mais necessária).
- `especialidade_retornada` agora vem direto de `content.get("specialty")`.
- Adicionei `especialidade_nula_apesar_de_concluido` ao log (default `False`, vira `True` quando `status == "diagnosis_concluded"` mas `specialty` vem `None`) — sinaliza falha de parsing no microserviço, dado relevante para a análise de qualidade da triagem, não um bug do script.

## Tarefa 6 — Testes

- **chat-rag-microservice** (novo `pytest.ini` + `tests/test_structured_output.py`, 13 testes): JSON limpo `ongoing` e `diagnosis_concluded`, cercas Markdown (```json e ``` genérico) removidas antes do parse, JSON malformado/faltando chave/status inválido/lista em vez de objeto — todos caindo no fallback sem exceção —, texto vazio, especialidade fora da lista fechada descartada, e as 12 especialidades válidas aceitas uma a uma.
- **chatbot-backend** (novo `tests/test_resolve_diagnosis_content.py`, 4 testes): prioriza campos estruturados (`ongoing` e `diagnosis_concluded`), cai no fallback quando `status` estruturado está ausente (payload de versão antiga) ou é um valor inesperado. `test_diagnosis_status.py` (14 testes de `_infer_diagnosis_status`) **mantido sem alterações** — não reescrevi/substituí esses testes porque a função continua sendo o fallback real, não é código morto (ver Tarefa 3). Esse é um desvio deliberado do texto literal da Tarefa 6 item 1, que pedia para "reescrever" esses testes — decidi que isolar em vez de reescrever é o correto dado que a função permanece em uso.
- **Frontend**: `nemotron-chat.service.spec.ts` atualizado (troca `finalAnswer` por `finalSpecialty`/`finalOrientation`, novo teste para o caso de vir `null` do backend). Novo `final-display-page.spec.ts` confirma especialidade e orientação em elementos separados e que o texto bruto do LLM não aparece mais na tela.
- **Suíte completa, tudo passando**: 23 testes Vitest (`ng test`), 18 pytest em `chatbot-backend`, 13 pytest em `chat-rag-microservice`. `ng build` de produção limpo.

## Limitação explícita: sem teste real contra o Nemotron

Não havia `NVIDIA_API_KEY` nem RabbitMQ/Redis/chat-rag-microservice completo rodando neste ambiente (mesma limitação já registrada no relatório anterior). Por isso:

- Toda a lógica de `parse_structured_response()` foi validada **só com strings JSON sintéticas** nos testes automatizados (Tarefa 6), nunca contra uma resposta real do Nemotron.
- Não fiz nenhuma chamada real ao LLM para confirmar que o modelo de fato obedece ao novo formato JSON quando instruído pelo system prompt atualizado — isso só pode ser validado rodando a pilha completa com uma chave de API real, o que fica para você.
- Não simulei silenciosamente uma resposta do Nemotron para fingir uma validação end-to-end — as mudanças em `langgraph_rag_service.py`, `base_worker.py` e `structured_output.py` foram verificadas via `python -c "import ..."` (sem erro de import/sintaxe) e via a suíte de testes unitários, não via execução real do pipeline completo.

## O que eu não fiz, conforme pedido explicitamente

- Não mexi no campo `mode` (GPU/API).
- Não implementei WebSocket.
- Não rodei `simulador.py` nem `locustfile.py` em escala.
- Não criei/editei `METODOLOGIA_SIMULACAO.md` nem tomei decisão de critério de pesquisa.

## Outra pendência observada (não relacionada a esta tarefa)

O commit anterior do `RELATORIO_EXECUCAO_CLAUDE_CODE.md` (Dias 7-12) foi desfeito por um `git reset` fora desta sessão — o arquivo continua no disco, só ficou "untracked" de novo. Não mexi nisso; avisei você no meio da execução e deixo para sua decisão se quer recommitá-lo.
