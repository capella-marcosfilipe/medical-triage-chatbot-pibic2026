# Relatório de Execução — Vazamento de Raciocínio Bruto na Resposta ao Paciente

## Resumo

A partir do segundo turno de uma conversa, o campo `answer` devolvido ao paciente
às vezes deixava de ser uma resposta em português e passava a ser o raciocínio
interno bruto do modelo (`reasoning_content`), em inglês, cortado no meio da
frase. Causa raiz confirmada, corrigida e verificada com chamadas reais à API
da NVIDIA — não foi assumida, foi testada.

---

## Tarefa 0 — Causa confirmada

O modelo usado (`nvidia/nvidia-nemotron-nano-9b-v2`) é um modelo de raciocínio
híbrido: ele gera cadeia de pensamento (chain-of-thought) **por padrão**,
exposta pela API em um campo separado (`message.reasoning_content`), a menos
que o system prompt contenha explicitamente o token `/no_think`.

O código antigo (`app/llm/nemotron_service.py::_build_messages`) só enviava um
token de controle (`/think`) quando `use_reasoning=True`. Como o fluxo real de
triagem sempre chama com `use_reasoning=False` (valor padrão de
`ChatRequest.use_reasoning`), **nenhum token de controle era enviado**, e o
modelo raciocinava de qualquer forma, consumindo uma fatia variável (e
crescente, conforme a conversa acumula histórico + contexto RAG) do orçamento
de `max_tokens=512` compartilhado entre raciocínio e resposta final.

Pior: em `_generate_api`, havia um fallback explícito:

```python
if not response and hasattr(message, 'reasoning_content'):
    response = message.reasoning_content
```

Ou seja, quando o raciocínio consumia tokens demais e `message.content` ficava
vazio, o código **deliberadamente devolvia o raciocínio bruto como se fosse a
resposta**. Esse texto então falhava no parse de JSON em
`parse_structured_response()`, caindo no fallback antigo, que reexibia o texto
bruto (`message=raw_text`) — e foi isso que chegou ao paciente.

### Reprodução real (não simulada) via API da NVIDIA, dentro do container

Testei diretamente contra a API real (chave configurada, `NVIDIA_API_KEY` com
70 caracteres), simulando um prompt de 2º turno igual ao produzido pelo
serviço, **sem** enviar `/think` ou `/no_think` (comportamento antigo):

```
finish_reason: length
content len: 152          (JSON cortado no meio de uma string)
reasoning_content len: 2216
```

Trecho do `reasoning_content` capturado (raciocínio em inglês, nunca deveria
ser visível ao paciente):

```
Okay, the patient is experiencing a headache in the middle of the eyes that
started today morning and is severe. They mentioned it's never happened
before. I need to continue the triage with short and safe questions...
```

Em uma variação do mesmo teste (prompt um pouco menor), `content` ficou vazio
por completo e só `reasoning_content` tinha texto — reproduzindo exatamente o
padrão do bug relatado (resposta em inglês, cortada no meio, sem JSON válido).

Repeti o mesmo teste enviando `/no_think` no system message (mesmo
`max_tokens=512`, sem nenhum outro ajuste):

```
finish_reason: stop
content len: 169
reasoning_content len: 0

content: {"status": "ongoing", "message": "Entendo, pode me informar se a dor
está associada a algum trauma, febre ou alteração visual?", "specialty": null,
"orientation": null}
```

Repeti ainda com um prompt mais realista (histórico de 2 turnos + contexto RAG
+ regras de triagem Manchester recuperadas, replicando o pior caso de tamanho
de prompt do pipeline real):

```
finish_reason: stop
usage: completion_tokens=56, prompt_tokens=548, total_tokens=604
content: JSON válido, resposta completa em português
```

**Conclusão da Tarefa 0:** a causa é a ausência do token `/no_think` quando
`use_reasoning=False`, combinada com um fallback no código que reexibia
`reasoning_content` como resposta. Não foi necessário aumentar `max_tokens` —
desativar o raciocínio já resolve com folga dentro do orçamento atual de 512
tokens, mesmo em prompts com RAG + histórico.

---

## Tarefa 1 — Correção da causa raiz

**`chat-rag-microservice/app/infrastructure/constants.py`**
Adicionado `REASONING_DISABLE_TOKEN = "/no_think"`.

**`chat-rag-microservice/app/llm/nemotron_service.py`**
- `_build_messages()`: agora **sempre** envia um token de controle
  (`/think` ou `/no_think`, nunca omite os dois), eliminando o comportamento
  padrão indesejado do modelo.
- `_generate_api()`: removido o fallback que devolvia `reasoning_content`
  como resposta. Se `content` vier vazio, a função retorna string vazia (e
  loga um `warning` com `finish_reason` para diagnóstico) — nunca mais
  substitui silenciosamente pelo raciocínio bruto.

`max_tokens` **não foi alterado** — o valor padrão (512) já é suficiente sem
raciocínio, confirmado nos testes acima.

---

## Tarefa 2 — Fallback de `parse_structured_response()` blindado

**`chat-rag-microservice/app/llm/structured_output.py`**

Antes, qualquer falha de parsing (JSON inválido, resposta vazia, etc.) caía em:

```python
return StructuredLLMOutput(status="ongoing", message=raw_text, ...)
```

Agora:

```python
_SAFE_FALLBACK_MESSAGE = (
    "Desculpe, não consegui processar sua mensagem corretamente. "
    "Pode reformular ou repetir?"
)
...
return StructuredLLMOutput(status="ongoing", message=_SAFE_FALLBACK_MESSAGE, ...)
```

O texto bruto continua sendo logado via `logger.warning(...raw_text!r...)`
para diagnóstico, mas **nunca mais é devolvido na resposta HTTP**. Isso vale
como segunda camada de defesa independente da causa raiz — mesmo que uma
causa nova e ainda não vista faça o modelo devolver texto fora do contrato
JSON, o paciente nunca verá esse texto bruto.

---

## Tarefa 3 — Teste de regressão

Adicionado `tests/test_structured_output.py::test_raciocinio_bruto_vazado_cai_no_fallback_seguro`,
usando uma versão do texto real capturado no relato do bug (raciocínio em
inglês, cortado em "...if there are red flags (like sudden onset, severe
symptoms, or new"), confirmando que cai no fallback seguro e que a palavra
"headache" não aparece na mensagem devolvida.

Os dois testes existentes que antes esperavam `message == raw_text`/`""` no
fallback (`test_json_malformado_cai_no_fallback_sem_excecao`,
`test_texto_vazio_cai_no_fallback`) foram atualizados para esperar
`_SAFE_FALLBACK_MESSAGE`, já que o contrato de fallback mudou de propósito
(Tarefa 2).

**Resultado da suíte completa** (rodada dentro do container, após rebuild da
imagem para incorporar as mudanças):

```
20 passed, 1 warning in 55.57s
```

(19 testes antigos + 1 novo teste de regressão; nenhum teste pré-existente
quebrou além dos dois ajustados intencionalmente acima.)

---

## Tarefa 4 — Verificação manual real (2 conversas de 5 turnos cada)

Stack subida com `docker compose build chat-rag-microservice
chat-rag-microservice-api-worker` + `docker compose up -d` (imagens
reconstruídas para incluir o fix), `NVIDIA_API_KEY` real configurada.
Nenhum warning de `reasoning_content`/vazamento apareceu nos logs do worker
durante os 10 turnos abaixo (`docker logs chat-rag-microservice-api-worker`).

### Conversa 1 — dor abdominal (queixa vaga → detalhamento progressivo)

**Turno 1** — `POST /api/v1/chat` `{"message": "Não estou me sentindo bem hoje"}`
```json
{"answer":"Olá, entendo que você não está se sentindo bem hoje. Para entender melhor, posso perguntar algumas coisas: Sente alguma dor ou desconforto específico? Se sim, onde está localizada?","diagnosis_status":"ongoing","specialty":null,"orientation":null}
```

**Turno 2** — `"Estou com uma dor forte na barriga, do lado direito, embaixo"`
```json
{"answer":"Obrigado por compartilhar isso. A dor no abdômen do lado direito pode ter várias causas. Pode me dizer se a dor piora ao comer, se há inchaço ou febre, ou se há outros sintomas como vômito?","diagnosis_status":"ongoing","specialty":null,"orientation":"Dor abdominal do lado direito. Avaliar características específicas (localização, associação a alimentação, febre, vômito) para orientar encaminhamento."}
```

**Turno 3** — `"Piora quando eu como, tenho enjoo mas nao vomitei, e sinto um pouco de febre"`
```json
{"answer":"Entendo que a dor piora ao comer e você tem enjoo com leve febre. Posso perguntar se a dor está associada a outros sintomas, como perda de apetite, diarreia ou dificuldade para respirar?","diagnosis_status":"ongoing","specialty":null,"orientation":"Dor abdominal inferior direita com agravamento alimentar, enjoo e leve febre. Necessita avaliação para possíveis causas gastrointestinais ou hepatobiliares."}
```

**Turno 4** — `"Sem diarreia, mas perdi o apetite e a dor comecou ha 2 dias e ta piorando"`
```json
{"answer":"Entendo que a dor piora com a ingestão de alimentos e você tem enjoo com leve febre. Você já tentou alguma alimentação específica que alivie ou agrava a dor? Há algo que você come que piora a sensação?","diagnosis_status":"ongoing","specialty":null,"orientation":"Dor abdominal direita piorando com alimentação, enjoo e leve febre. Necessário avaliar causas gastrointestinais ou inflamatórias."}
```

**Turno 5** — `"Nao percebi alimento especifico. A dor e constante e forte, nao consigo nem andar direito"`
```json
{"answer":"Entendo que a dor abdominal do lado direito piora com a ingestão de alimentos e você tem enjoo com leve febre. Como a dor é constante e forte, tornando difícil realizar atividades como andar, gostaria de saber se há outros sintomas como inchaço abdominal visível, sensibilidade ao toque ou alterações no humor?","diagnosis_status":"ongoing","specialty":null,"orientation":"Dor abdominal do lado direito com agravamento na ingestão de alimentos, enjoo, leve febre e perda de apetite. Necessita avaliação para descartar causas inflamatórias ou obstrutivas."}
```

Todos os 5 turnos em português, coerentes, sem JSON quebrado e sem texto em
inglês. `diagnosis_status` permaneceu `"ongoing"` (o modelo não convergiu para
uma conclusão em 5 turnos apesar do quadro sugestivo — comportamento de
qualidade de triagem, **não é o bug deste relatório** e não foi alterado, per
instrução explícita de não mexer no top-k do RAG).

### Conversa 2 — replay exato do caso que originou o bug relatado

**Turno 1** — `"Eu estou me sentindo enjoado e com dor de cabeça."` (mensagem
idêntica à do relato original do bug)
```json
{"answer":"Olá, estou aqui para ajudar. Para entender melhor sua situação, posso perguntar alguns detalhes. Você pode me dizer por quanto tempo você tem se sentido enjoado e com dor de cabeça?","diagnosis_status":"ongoing","specialty":null,"orientation":null}
```

**Turno 2** — `"A dor é no meio dos olhos, começou hoje de manhã, é forte, nunca senti isso antes"`
(este é o turno exato que, antes do fix, devolvia o raciocínio bruto em inglês)
```json
{"answer":"Obrigado por compartilhar. A dor nos olhos é forte e localizada no meio? Pode me confirmar se há outros sintomas associados, como visão turva, sensibilidade à luz ou secreção ocular?","diagnosis_status":"ongoing","specialty":null,"orientation":null}
```

**Turno 3** — `"Sim, estou com visão turva e um pouco de náusea, e a dor piora com luz forte"`
```json
{"answer":"Entendo que a dor nos olhos é intensa e piora com a luz. Você já tentou aliviar a visão turva com algo, como piscar ou descansar os olhos?","diagnosis_status":"ongoing","specialty":null,"orientation":null}
```

**Turno 4** — `"Nao tentei nada ainda, o descanso nao ajuda. E a dor mais forte que ja senti na vida, veio do nada"`
```json
{"answer":"Entendo que a dor é intensa e vem do nada. Você já tentou algum medicamento ou remédio para aliviar a dor nos olhos?","diagnosis_status":"ongoing","specialty":null,"orientation":null}
```

**Turno 5** — `"Nao tomei nenhum remedio ainda. Acho que preciso de ajuda urgente, essa dor esta insuportavel"`
```json
{"answer":"Entendo que a dor é muito forte e está afetando sua visão. Você já tentou aplicar uma compressa fria ou cobrir os olhos para ver se a dor ou a visão melhoram?","diagnosis_status":"ongoing","specialty":null,"orientation":"Dor ocular intensa, visão turva e náusea com agravamento por luz, sem histórico prévio. Requer avaliação imediata para descartar causas como glaucoma agudo, enxaqueca com aura, ou outras condições neurológicas."}
```

Todos os 5 turnos em português, coerentes. O turno 2 — o ponto exato onde o
bug relatado ocorria — voltou limpo em todas as repetições feitas durante a
sessão de correção.

---

## O que não foi alterado (fora de escopo, por instrução explícita)

- Reestruturação do grafo LangGraph — não tocada.
- Top-k do retrieval Manchester — não tocado (mesmo notando, como achado
  secundário não corrigido aqui, que o modelo às vezes demora a convergir
  para `diagnosis_concluded` mesmo diante de sinais de alerta claros).
- `simulador.py` em escala — não executado; só as verificações manuais acima.

## Observação para acompanhamento futuro (não é uma ação pendente deste bug)

O comportamento de convergência da triagem (quantos turnos até
`diagnosis_concluded`) é uma questão de qualidade de prompt/RAG, separada do
vazamento de raciocínio corrigido aqui. Se quiser, posso investigar isso como
uma tarefa própria depois.
