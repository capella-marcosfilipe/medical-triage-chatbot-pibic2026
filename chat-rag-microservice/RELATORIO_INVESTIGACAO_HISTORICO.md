# Relatório de Investigação — Histórico de Conversa Está Completo?

## Pergunta

O histórico completo da conversa está sendo incluído no prompt enviado ao
Nemotron a cada turno, ou está incompleto/truncado?

## Resposta curta

**Para o cenário exato relatado (8 turnos), o histórico estava completo.**
A repetição da pergunta sobre "ambiente escuro" nos turnos 5/6/8 não é
causada por perda de dados — é comportamento do modelo, não um bug de
engenharia. Conforme instruído, não toquei em system prompt, `/think` ou
qualquer parâmetro de qualidade por causa disso.

**Só que a mesma investigação encontrou um bug real e distinto**, fora do
alcance dos 8 turnos do relato original: a partir da 9ª mensagem do
paciente em diante (17+ mensagens acumuladas), a mensagem de sistema — que
carrega o contrato de saída JSON e a lista fechada de especialidades — era
**silenciosamente descartada** do prompt pela janela de memória. Esse é um
bug técnico identificável no código (não característica do modelo), então
corrigi especificamente essa causa, sem tocar em mais nada.

---

## Tarefa 0 — Metodologia

Reproduzi contra a API real da NVIDIA (mesma stack, `NVIDIA_API_KEY`
configurada) uma conversa de dor de cabeça, sem `/start_session` (só
`/chat`, isolando a questão de histórico de `patient_context`), mencionando
explicitamente "quarto escuro" no turno 3 — igual ao relato.

Para capturar o **texto exato do prompt** enviado ao modelo em cada turno
(não a resposta, a entrada), usei duas abordagens complementares:

1. Um script Python dentro do container `chat-rag-microservice` que importa
   `LangGraphRAGService` "do zero" e chama `build_augmented_prompt(session_id, query)`
   diretamente — esse método lê o histórico persistido no Redis (mesmo
   mecanismo de "rehydrate" usado pelo processo real quando reinicia), então
   reproduz fielmente o que o servidor real monta para o próximo turno.
2. Turnos reais via `curl` contra `chatbot-backend` → `chat-rag-microservice`,
   com polling até `status: completed`, confirmando que a resposta do modelo
   também reflete esse mesmo prompt.

## Evidência — turno 4 (prompt completo, colado como está)

```
[SYSTEM]
Você é um assistente de triagem médica. Não forneça diagnóstico final. Colete dados com empatia e objetividade para encaminhamento clínico.
Use o contexto recuperado apenas como apoio e priorize segurança clínica.

FORMATO DE SAÍDA OBRIGATÓRIO: responda SEMPRE com um único objeto JSON, sem cercas de código Markdown e sem texto fora do JSON, no formato:
{"status": "ongoing" | "diagnosis_concluded", "message": "texto para o paciente", "specialty": null ou uma das especialidades abaixo, "orientation": null ou um resumo clínico objetivo para o médico}.
Quando status for "diagnosis_concluded", 'specialty' deve ser exatamente uma destas 12 opções (nunca uma variação livre): Cardiologia, Neurologia, Pneumologia, Gastroenterologia, Ortopedia, Pediatria, Clínica Geral, Urologia, Dermatologia, Psiquiatria, Oftalmologia, Otorrinolaringologia. Use "Clínica Geral" quando nenhuma especialidade mais específica se aplicar claramente.

[PACIENTE]
Estou com dor de cabeça.

[ASSISTENTE]
Olá, posso entender que uma dor de cabeça pode ser preocupante. Para ajudar melhor, poderia me dizer quando ela começou e qual é a intensidade dela em uma escala de 1 a 10?

[PACIENTE]
Começou hoje de manhã, intensidade uns 7 de 10

[ASSISTENTE]
Obrigado por compartilhar. A dor de cabeça começou hoje de manhã e tem intensidade de 7/10. Poderia me dizer se ela está localizada em alguma região específica da cabeça (como testa, testa frontal, têmporas) ou se está associada a outros sintomas, como febre, náusea, visão turva ou alterações na fala?

[PACIENTE]
É na testa e nos olhos, tenho nausea e sensibilidade a luz. Fico melhor quando deito num quarto escuro e em silencio

[ASSISTENTE]
Entendi. Você mencionou náusea e sensibilidade a luz. Há outros sintomas como febre, dores no corpo ou alterações no humor? E quanto ao uso de medicamentos ou alergias?

[RAG_CONTEXT]

Fonte 1: Dados fisiologicos de smartwatch sao apoio e nao substituem exame clinico. Divergencias entre sintomas graves e dados normais exigem cautela e investigacao adicional.

[REGRAS DE TRIAGEM RECUPERADAS]
(...5 regras Manchester recuperadas...)

Continue a triagem com perguntas curtas e seguras. Se não houver dados suficientes, peça mais detalhes.
```

A frase do turno 3 ("Fico melhor quando deito num quarto escuro e em
silencio") está presente, palavra por palavra, no prompt do turno 4. O
mesmo se confirmou nos prompts capturados para os turnos 6 e 8: todas as
trocas anteriores (paciente e assistente) apareciam completas, na ordem
correta, com a mensagem de sistema no topo.

Repeti a conversa via `curl` real (8 turnos completos, respostas do modelo
coladas abaixo) para confirmar que o comportamento observado bate com o
prompt capturado:

- Turno 5 (equivalente ao do relato): modelo perguntou sobre histórico de
  crises/fatores desencadeantes — **não repetiu** a pergunta sobre ambiente
  escuro nesta reprodução específica.
- Turno 7: paciente reclamou explicitamente ("Ja falei que fico melhor no
  escuro, voce ja perguntou coisas parecidas antes") — o modelo **não
  reconheceu a reclamação** nem se desculpou, simplesmente avançou para
  outra pergunta. O dado (quarto escuro) estava no prompt (confirmado acima),
  mas o modelo não o usou para evitar a pergunta redundante nem para validar
  a queixa do paciente sobre repetição.
- Em nenhum dos 8 turnos a conversa chegou a `diagnosis_concluded`, apesar
  de um quadro compatível com enxaqueca (cefaleia + fotofobia + náusea +
  melhora no escuro + piora com movimento).

**Conclusão para o cenário de 8 turnos: dado presente, comportamento do
modelo.** Não é uma questão de engenharia de dados corrigível no código —
é uma característica do modelo de 9B parâmetros sob esse formato de prompt
(transcrição rotulada `[PACIENTE]`/`[ASSISTENTE]` dentro de uma única
mensagem `user`, sem usar roles nativos de conversa da API). Fica com você
decidir se isso é um achado de pesquisa a documentar ou algo a investigar
mais — não tentei "consertar" via ajuste de prompt, conforme instruído.

---

## Bug real encontrado (fora do range dos 8 turnos do relato, mas na mesma investigação)

Ao continuar a investigação além do 8º turno para checar o comportamento
da janela de memória em conversas mais longas, encontrei uma perda de dado
real e identificável no código.

### Causa

`app/graph/langgraph_rag_service.py` aplicava a janela de memória
(`LANGGRAPH_MEMORY_WINDOW = 16`) com um corte simples:

```python
memory_window = messages[-settings.LANGGRAPH_MEMORY_WINDOW :]
```

em `build_augmented_prompt`, e o mesmo padrão em `_persist_history`. Essa
lista é `[SystemMessage, Human, AI, Human, AI, ...]` — a mensagem de
sistema (contrato de saída JSON + lista fechada de especialidades) é
sempre o **primeiro** elemento. Um corte `[-window:]` trata essa mensagem
como qualquer outra: uma vez que o total de mensagens ultrapassa 16 (ou
seja, a partir da 9ª mensagem do paciente — system + 8 pares = 17), a
mensagem de sistema é a primeira a cair fora da janela, silenciosamente,
sem erro nem log.

### Reprodução real (antes do fix)

Rodei os mesmos 8 turnos e capturei o prompt que seria montado para um
hipotético turno 9 (17 mensagens acumuladas: system + 8 pares). O bloco
`[SYSTEM]` **não aparecia** — o prompt começava direto em:

```
[PACIENTE]
Estou com dor de cabeça.

[ASSISTENTE]
...
```

Ou seja, a partir daí, o modelo deixaria de receber o contrato de formato
JSON e a lista fechada de 12 especialidades — um problema real para
conversas que passam de ~8 turnos (o que já ocorre neste próprio relato,
que não converge em 8 turnos).

### Correção aplicada

Adicionado `LangGraphRAGService._apply_memory_window()` (staticmethod puro,
sem efeitos colaterais), que fixa a mensagem de sistema como âncora e só
aplica a janela deslizante ao restante:

```python
@staticmethod
def _apply_memory_window(messages: list[BaseMessage]) -> list[BaseMessage]:
    window = settings.LANGGRAPH_MEMORY_WINDOW
    if len(messages) <= window:
        return messages
    has_system = isinstance(messages[0], SystemMessage)
    head = messages[:1] if has_system else []
    tail_size = window - len(head)
    return head + messages[-tail_size:]
```

Usado nos dois pontos que antes faziam o corte manual
(`build_augmented_prompt` e `_persist_history`). Não mexe em nenhum texto
do system prompt, apenas garante que ele nunca seja descartado pela janela.

### Verificação após o fix

Rebuild da imagem (`docker compose build chat-rag-microservice
chat-rag-microservice-api-worker`), nova conversa real de 8 turnos do zero
(sessão nova, para não herdar o histórico já truncado que tinha ficado
persistido no Redis pela versão antiga do código), e recaptura do prompt
do turno 9:

```
[SYSTEM]
Você é um assistente de triagem médica. Não forneça diagnóstico final. ...
FORMATO DE SAÍDA OBRIGATÓRIO: ...

[ASSISTENTE]
Olá, posso entender que você está com dor de cabeça. ...
```

A mensagem de sistema volta a aparecer, mesmo com 17 mensagens acumuladas
(a mensagem do paciente do turno 1 é que sai da janela agora, como
esperado — a janela continua com 16 mensagens no total, só que a de
sistema é sempre uma delas).

### Testes

Suíte completa rodada dentro do container após rebuild: **25 passed**
(20 anteriores + 5 novos, em `tests/test_langgraph_memory_window.py`,
cobrindo: janela abaixo do limite, no limite exato, acima do limite com e
sem mensagem de sistema, e lista vazia).

---

## O que não foi feito (fora de escopo, por instrução explícita)

- Não ajustei o system prompt para tentar fazer o modelo "lembrar melhor"
  ou concluir mais rápido — isso mexeria na variável que a pesquisa está
  avaliando.
- Não reativei `/think`.
- Não toquei em `simulador.py`, no grafo LangGraph, ou no top-k do RAG.
- Não rodei simulação em escala — só as verificações manuais deste
  relatório.

## Para você decidir

O achado de que o modelo não usa/reconhece informação já fornecida (mesmo
estando no prompt) e não converge para `diagnosis_concluded` em conversas
de 7-8+ turnos é um dado de pesquisa, não um bug. Pode valer a pena registrar
isso como limitação conhecida do modelo de 9B parâmetros sob esse formato
de prompt (transcrição concatenada em uma única mensagem `user`, sem roles
nativos multi-turno da API) na sua metodologia — mas essa é uma decisão sua.
