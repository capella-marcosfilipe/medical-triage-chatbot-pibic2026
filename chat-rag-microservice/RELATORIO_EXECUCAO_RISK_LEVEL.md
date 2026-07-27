# Relatório de Execução — `risk_level` no Contrato de Saída Estruturada

## Resumo

`pacientes_sinteticos.json` já tinha `nivel_urgencia_esperado` nos 20 perfis,
mas não existia nenhum campo "obtido" em lugar nenhum do sistema para
compará-lo — confirmado antes deste prompt. Adicionado `risk_level` ao
contrato JSON do LLM (`docs/structured_output_contract.md` + system prompt
em `LangGraphRAGService`), com parsing/validação contra a lista fechada de 5
cores, propagação por todo o pipeline (`chat-rag-microservice` →
`chatbot-backend` → `simulador.py` → CSV), testes, e verificação manual com
duas conversas reais até `diagnosis_concluded` (uma grave, uma leve), ambas
com `risk_level` clinicamente coerente.

**Achado relevante durante a Tarefa 1** (não estava no escopo original, mas
muda a instrução do system prompt): a base de regras Manchester/Maringá
indexada no ChromaDB (415 registros) não tem **nenhum** registro com
`cor = AZUL` — só `VERMELHO`, `LARANJA`, `AMARELO`, `VERDE`. Isso significa
que, para o tier "azul" (quadros não urgentes), o RAG nunca vai recuperar
uma regra de apoio; o modelo precisa classificar por julgamento geral, sem
evidência retornada. A instrução no system prompt já reflete isso
explicitamente (ver Tarefa 1 abaixo) em vez de assumir cobertura completa.

---

## Tarefa 1 — Contrato JSON Estendido

**`app/infrastructure/constants.py`**: nova constante
`NIVEIS_URGENCIA_CONHECIDOS = ("vermelho", "laranja", "amarelo", "verde", "azul")`,
mesmo padrão de `ESPECIALIDADES_CONHECIDAS`. Minúsculas deliberadamente —
as regras recuperadas do ChromaDB guardam `cor` em maiúsculas
(`"VERMELHO"`), então o system prompt instrui o modelo a sempre responder
em minúsculas independente da caixa mostrada no contexto recuperado.

**`docs/structured_output_contract.md`**: `risk_level` adicionado aos dois
exemplos JSON e à tabela de campos, com a nota sobre a ausência de `AZUL`
na base indexada.

**`app/graph/langgraph_rag_service.py` (`register_user_message`)**: system
prompt estendido — `risk_level` no formato de saída obrigatório, instrução
de basear a classificação nas `[REGRAS DE TRIAGEM RECUPERADAS]` do turno
(campo `Cor`), e a nota específica sobre `"azul"` não ter fluxograma
retornável pelo RAG, exigindo julgamento clínico geral nesse caso.

---

## Tarefa 2 — Parsing e Validação

**`app/llm/structured_output.py`**: `StructuredLLMOutput.risk_level: str | None`.
`parse_structured_response()` valida `risk_level` contra
`NIVEIS_URGENCIA_CONHECIDOS` — fora da lista fechada (ex.: `"VERMELHO"`
maiúsculo) é descartado com `logger.warning`, mesmo padrão defensivo já
usado para `specialty`. `_fallback()` retorna `risk_level=None`.

**`app/domain/response.py`**: `ChatResponse.risk_level: Optional[str] = None`.

**`app/worker/base_worker.py`**: `ChatResponse(..., risk_level=parsed.risk_level)`.

**`chatbot-backend/app/models/async_schemas.py`**: `NLPJobContent.risk_level: Optional[str] = None`.

**`chatbot-backend/app/api/v1/endpoints.py`**: `_resolve_diagnosis_content()`
passou de tupla de 3 para 4 elementos
(`status, specialty, orientation, risk_level`), lendo `risk_level` do
payload estruturado do microsserviço; o `content = NLPJobContent(...)` no
`GET /chat/status/{job_id}` agora passa `risk_level=risk_level`. Ambos os
pontos de fallback (payload sem campos estruturados, `status` inválido)
retornam `risk_level=None`, mesmo padrão de `specialty`/`orientation`.

---

## Tarefa 3 — CSV do `simulador.py`

**`chatbot-backend/simulador.py`**: `nivel_urgencia_obtido` capturado de
`content.get("risk_level")` no mesmo ponto onde `especialidade_retornada`
já é lida (só quando `diagnosis_status == "diagnosis_concluded"`).
`nivel_urgencia_bateu` compara (case-insensitive, mesmo padrão de
`especialidade_bateu`) contra `nivel_urgencia_esperado` do perfil — que
também passou a entrar no `log` (não estava lá antes, só
`especialidade_esperada` estava). Três colunas novas em
`_CAMPOS_CSV_RESUMO`: `nivel_urgencia_esperado`, `nivel_urgencia_obtido`,
`nivel_urgencia_bateu`.

---

## Tarefa 4 — Testes

**`chat-rag-microservice`** (rebuild + `pytest` no container):
`test_todos_os_5_niveis_de_urgencia_sao_aceitos` (cada uma das 5 cores
aceita), `test_nivel_urgencia_fora_da_lista_fechada_e_descartado`
(`"VERMELHO"` maiúsculo é descartado, `specialty`/`orientation`
continuam passando normalmente). Testes existentes atualizados para
also assert `risk_level is None` nos casos de fallback/malformado, e
`risk_level` nos dois exemplos de JSON limpo (ongoing/concluído).
Resultado: **27 passed** (25 anteriores + 2 novos).

**`chatbot-backend`** (`pytest` local, `requirements-dev.txt`):
`test_resolve_diagnosis_content.py` atualizado para a tupla de 4
elementos, com `risk_level` testado nos 4 cenários (campos estruturados
presentes, ongoing, fallback sem campos estruturados, fallback com status
inválido). Resultado: **23 passed**.

Confirmei que os testes de regressão do vazamento de raciocínio
(`test_raciocinio_bruto_vazado_cai_no_fallback_seguro`) e da janela de
memória (`test_langgraph_memory_window.py`) continuam passando — nenhum
dos dois bugs anteriores foi reaberto.

---

## Tarefa 5 — Verificação Manual (2 conversas reais)

Stack real (`docker compose`, rebuild de `chat-rag-microservice`,
`chat-rag-microservice-api-worker` e `chatbot-backend`), `NVIDIA_API_KEY`
real, via `curl` direto no `chatbot-backend` (`/api/v1/start_session` →
`/api/v1/chat` → `/api/v1/chat/status/{job_id}`, polling manual).

### Conversa 1 — Caso grave (réplica da queixa do Antônio: dor no peito, braço, sudorese)

`session_id = 9ecfa575-696c-4ff4-b6be-067c2c070f0a`. 7 turnos até concluir.

**Turno 1** — `"Estou com uma dor forte no peito, irradiando para o braço esquerdo, sudorese fria e falta de ar, começou há 20 minutos"`
```json
{"job_id":"fd10dfbe-f213-4b24-ba49-5adcecda9147","chat_id":"9ecfa575-696c-4ff4-b6be-067c2c070f0a","status":"completed","idempotency_key":"e9248403ac23e5cf3ef5484052fe371b628faa9d92457f16a5c5ddf6a4454467","created_at":"2026-07-27T16:19:30.874493","content":{"answer":"Olá, Antônio. Estou aqui para entender melhor sua situação. Pode me dizer se a dor no peito piorou ou melhorou desde que começou?","processing_time_ms":1951.2,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null},"error":null}
```

**Turno 2** — `"A dor continua forte, não melhorou. Sinto também como um peso no peito e um pouco de tontura"`
```json
{"content":{"answer":"Antônio, você mencionou tontura. Pode me dizer se essa sensação está relacionada à dor no peito ou se ocorre independentemente?","processing_time_ms":1956.05,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```

**Turno 3** — `"Acho que está relacionada, vem junto com a dor. Também estou suando frio e me sentindo muito mal"`
```json
{"content":{"answer":"Antônio, você mencionou tontura associada à dor no peito. Pode me confirmar se a tontura ocorre sempre junto com a dor ou também em outros momentos?","processing_time_ms":2136.18,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```

**Turno 4** — `"Sim, sempre junto com a dor. Não tenho histórico de problemas cardíacos, mas meu pai teve infarto. Não tenho alergias nem uso medicamentos"`
```json
{"content":{"answer":"Antônio, você mencionou tontura associada à dor no peito. Pode me confirmar se a tontura ocorre sempre junto com a dor ou também em outros momentos?","processing_time_ms":2123.2,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```
*(o modelo repetiu a pergunta do turno anterior ipsis litteris, apesar de já respondida — mesmo tipo de comportamento de não-progressão já documentado em `RELATORIO_INVESTIGACAO_HISTORICO.md`; não é causado por perda de histórico nem por este conserto, e não foi investigado de novo aqui por estar fora de escopo.)*

**Turno 5** — `"A dor está piorando e agora estou com muita falta de ar, mal consigo falar. Por favor, preciso de ajuda urgente"`
```json
{"content":{"answer":"Antônio, você mencionou que a dor está piorando e agora tem muita falta de ar, dificultando a fala. Isso é muito preocupante. Pode me confirmar se você está com alguma dificuldade para respirar ou se sente com falta de ar intensa?","processing_time_ms":2435.24,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```

**Turno 6** — `"Sim, falta de ar intensa, meus lábios estão ficando arroxeados. Por favor conclua a triagem, é uma emergência"`
```json
{"content":{"answer":"Antônio, você mencionou que os lábios estão ficando arroxeados e a falta de ar é intensa. Isso é muito grave. Pode me confirmar se há inchaço nos lábios ou língua, ou se há algum som estranho ao respirar?","processing_time_ms":3333.34,"diagnosis_status":"ongoing","specialty":null,"orientation":"Dor torácica irradiada para o braço esquerdo, falta de ar intensa, sudorese fria, tontura associada e piora da dor. Sinais de possível comprometimento cardiovascular ou respiratório.","risk_level":null}}
```
*(`orientation` já veio preenchido aqui, com `status` ainda `"ongoing"` e `risk_level` ainda `null` — ver observação abaixo.)*

**Turno 7** — `"Não tenho inchaço, mas ouço um chiado ao respirar. Por favor, conclua a triagem agora e me diga para qual especialidade devo ser encaminhado"`
```json
{"content":{"answer":"Antônio, com base em seus sintomas de dor torácica intensa irradiando para o braço esquerdo, sudorese fria, falta de ar intensa, tontura e chiado respiratório, recomendo que você acesse um serviço de emergência imediatamente. Estamos preocupados com possíveis causas como infarto agudo do miocárdio ou embolia pulmonar.","processing_time_ms":3785.37,"diagnosis_status":"diagnosis_concluded","specialty":"Cardiologia","orientation":"Dor torácica irradiada, falta de ar intensa, sinais de estresse cardiovascular e histórico familiar de infarto. Necessidade de avaliação cardiológica urgente.","risk_level":"vermelho"}}
```

**Resultado: `specialty = "Cardiologia"`, `risk_level = "vermelho"` — ambos batem com `especialidade_esperada`/`nivel_urgencia_esperado` do perfil real do Antônio em `pacientes_sinteticos.json`.**

### Conversa 2 — Caso leve (dor de garganta leve, sem febre)

`session_id = d4369f78-4452-4118-9b8a-630608ed8756`. 5 turnos até concluir.

**Turno 1** — `"Estou com uma dor de garganta leve há 2 dias, meio irritada, sem febre"`
```json
{"content":{"answer":"Obrigado por compartilhar suas informações. Para ajudar melhor, posso perguntar sobre a intensidade da dor de garganta e se há outros sintomas associados, como dificuldade para engolir, voz rouca ou febre?","processing_time_ms":3233.83,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```

**Turno 2** — `"A dor é leve, uns 2 de 10. Não tenho dificuldade para engolir, voz normal, sem febre. Só um incômodo leve mesmo"`
```json
{"content":{"answer":"Entendi, obrigado. A dor é leve e sem febre. Você já tentou algum remédio ou medidas caseiras, como gargarejo com água salgada ou repouso vocal?","processing_time_ms":2259.1,"diagnosis_status":"ongoing","specialty":null,"orientation":null,"risk_level":null}}
```

**Turno 3** — `"Ainda não tentei nada, só está começando. Não tenho outros sintomas, não tenho alergias nem uso medicamentos. Pode concluir a triagem?"`
```json
{"content":{"answer":"Obrigado por informar. Como a dor de garganta é leve e sem febre, posso perguntar se há algum histórico de infecções respiratórias recentes ou contato com pessoas doentes?","processing_time_ms":3013.35,"diagnosis_status":"ongoing","specialty":null,"orientation":"Dor de garganta leve, sem febre ou sintomas associados. Necessita de avaliação para descartar causas infecciosas ou alérgicas.","risk_level":"verde"}}
```

**Turno 4** — `"Não, nenhum contato recente com pessoas doentes e não tive infecção respiratória recente. Pode concluir e me dizer para qual especialidade encaminhar?"`
```json
{"content":{"answer":"Obrigado por responder. Como a dor de garganta é leve e sem febre, e não há histórico de infecções recentes ou contato com pessoas doentes, posso sugerir que você monitore os sintomas. Se a dor aumentar, surgirem novos sintomas ou persistir por mais de alguns dias, recomendo procurar um médico. Para agora, não é necessário encaminhar para uma especialidade específica.","processing_time_ms":3644.28,"diagnosis_status":"ongoing","specialty":"Clínica Geral","orientation":"Dor de garganta leve sem febre ou sintomas associados. Sem sinais de complicações. Recomenda-se monitoramento e consulta a um médico geral para avaliação inicial.","risk_level":"azul"}}
```
*(`specialty` e `risk_level` já preenchidos com `status` ainda `"ongoing"` — mesma observação do turno 6 da conversa 1. Note também que `risk_level` mudou de `"azul"` aqui para `"verde"` no turno seguinte — o modelo não foi perfeitamente consistente entre turnos, mas ambos os valores são membros válidos da lista fechada e ambos plausíveis clinicamente para o quadro.)*

**Turno 5** — `"Entendido, obrigado. Pode marcar a triagem como concluída agora, por favor"`
```json
{"content":{"answer":"Sua dor de garganta é leve e sem febre. Recomenda-se monitorar os sintomas. Se piorar ou persistir, consulte um médico.","processing_time_ms":2732.18,"diagnosis_status":"diagnosis_concluded","specialty":"Clínica Geral","orientation":"Monitorar sintomas. Se a dor aumentar, surgirem novos sintomas ou persistir por mais de alguns dias, recomenda-se procurar um médico.","risk_level":"verde"}}
```

**Resultado: `specialty = "Clínica Geral"`, `risk_level = "verde"` — clinicamente coerente com o quadro leve descrito (perfil sintético equivalente na base tem `nivel_urgencia_esperado` entre `"verde"`/`"azul"` para queixas leves comparáveis).**

### Observação (não é bug, não corrigida — decisão sua se vale investigar depois do piloto)

Em ambas as conversas, `specialty`/`orientation`/`risk_level` às vezes vieram
preenchidos em turnos com `status = "ongoing"` (turno 6 da conversa 1,
turnos 3 e 4 da conversa 2), quando o contrato documenta que esses campos
só deveriam vir preenchidos quando `status = "diagnosis_concluded"`. O
parser (`parse_structured_response`) nunca força esse acoplamento — só
valida cada campo isoladamente (tipo + lista fechada quando presente),
igual já fazia antes desta tarefa para `specialty`/`orientation`. Não é
uma regressão introduzida por `risk_level`: é o mesmo comportamento de
modelo já existente para os outros dois campos, agora só mais visível
porque `risk_level` é um terceiro campo sujeito a ele. Não mexi no parser
para forçar esse acoplamento — não estava no escopo pedido
("não reabra o parsing de specialty/orientation além do necessário para
adicionar risk_level ao lado").

---

## O que NÃO foi feito (fora de escopo, por instrução explícita)

- Não mexi em `smartwatch_simulator.py`, no mecanismo de prefixo de vitais
  dos 5 casos graves, nem em `simulador.py` além da Tarefa 3.
- Não reabri o parsing de `specialty`/`orientation` além do necessário
  para adicionar `risk_level` ao lado (inclusive o acoplamento
  `status`/campos-preenchidos discutido acima, que já existia antes).
- Não rodei a simulação completa dos 20 perfis nem Locust — só a
  verificação manual da Tarefa 5.
- Não investiguei de novo a não-progressão do modelo em turnos repetidos
  (turno 4 da conversa 1) — já documentada como comportamento de modelo em
  `RELATORIO_INVESTIGACAO_HISTORICO.md`.
