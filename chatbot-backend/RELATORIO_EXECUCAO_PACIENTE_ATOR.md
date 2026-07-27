# Relatório de Execução — Reforço do Prompt do Paciente-Ator

## Resumo

Reforcei `PATIENT_SYSTEM_PROMPT_TEMPLATE` (regras explícitas + exemplos few-shot) e, com base numa evidência forte encontrada na Tarefa 2, removi `/no_think` da chamada do paciente-ator (não do chatbot em teste — isso continua intocado). O padrão mais grave do achado anterior — o paciente-ator dando conselhos médicos, avisos de segurança e listas de recomendações — **desapareceu** nas 8 conversas verificadas. Mas a **taxa de conclusão continua em 0/8**, porque um problema residual e mais sutil do paciente-ator (ele às vezes "espelha" a pergunta do assistente em vez de respondê-la) persiste, e — mais decisivamente — **o próprio chatbot em teste trava repetindo a mesma pergunta várias vezes seguidas**, independente da resposta do paciente. Esse segundo motivo é o mesmo comportamento já documentado em `RELATORIO_INVESTIGACAO_HISTORICO.md`, do lado do sistema avaliado, fora do escopo desta tarefa.

Conforme instruído, **parei aqui e não insisti reforçando o prompt** — a taxa de conclusão não melhorou o suficiente para justificar mais iterações, e a causa dominante do não-fechamento nesta amostra não é mais o paciente-ator.

---

## Tarefa 1 — Prompt Reforçado

`PATIENT_SYSTEM_PROMPT_TEMPLATE` (`chatbot-backend/simulador.py`) ganhou:
- Declaração explícita de papel ("Você é EXCLUSIVAMENTE... nunca o profissional de saúde").
- 5 regras numeradas: sempre primeira pessoa; nunca dar conselho médico/aviso de segurança; nunca devolver pergunta ou lista; inventar uma resposta plausível em vez de fugir da pergunta; nunca admitir ser simulação/IA.
- Um par de exemplos few-shot (pergunta do assistente → resposta correta de paciente) e um exemplo explícito do padrão errado capturado no relatório anterior, rotulado "NÃO FAÇA ISSO".

## Tarefa 2 — `/no_think` no Paciente-Ator

Testei antes de mexer no prompt reforçado, usando o prompt **original** (não reforçado), para isolar essa variável: 5 chamadas com `/no_think` e 5 sem, mesmo cenário (Antônio, pergunta "a dor está piorando ou melhorando?").

**Com `/no_think` — 5/5 quebraram personagem:**
```
"...É importante que você procure um médico o mais rápido possível... pode ser um sinal de uma condição grave, como um ataque cardíaco..."
"...é preocupante e pode estar relacionada a uma condição cardiovascular aguda, como infarto agudo do miocárdio (IAM). Isso requer atenção médica imediata. ### O que você deve fazer agora: 1. Procure um serviço de emergência (SAMU..."
```
(Note: a resposta chega a **revelar o nome da condição simulada** — "infarto agudo do miocárdio" — que o prompt proíbe explicitamente.)

**Sem `/no_think` (raciocínio habilitado) — 5/5 ficaram no personagem:**
```
"Dor no peito está piorando, com calor e sensação de aperto, além da falta de ar. Estou com medo de algo grave acontecer."
"A dor no peito está muito forte e não melhorou, ainda com frio e dificuldade para respirar."
```

Evidência clara e barata (10 chamadas) de que `/no_think` é um fator relevante nesse comportamento especificamente para este modelo neste papel. Removi `/no_think` de `gerar_resposta_paciente()` — isso é o token de controle de raciocínio *do paciente-ator*, não do chatbot em teste (que continua com seu próprio `/no_think` intocado em `chat-rag-microservice`). O fallback para `content` vazio (já existente) continua protegendo contra o caso raro de resposta vazia mesmo com raciocínio habilitado.

Reteste rápido do prompt **reforçado** já sem `/no_think` (5 chamadas, mesmo cenário): 5/5 respostas curtas, em primeira pessoa, sem conselhos:
```
"A dor no peito está piorando, está mais forte agora do que antes."
"Estou sentindo uma pressão intensa no peito que não para, junto com suor frio e dificuldade para respirar."
```

---

## Tarefa 3 — Verificação com `--limit 8`

Rodei `simulador.py --limit 8` contra a pilha real. **Resultado: 0/8 concluíram** (todos bateram no limite de 15 turnos, `diagnosis_status_final: ongoing`, nenhum erro).

Isso pareceria, à primeira vista, que a correção não funcionou. **Não presumi isso — investiguei o motivo real de cada conversa não concluir**, lendo o histórico completo do LangGraph (Redis) de todos os 8 pacientes, não só olhando o resultado agregado.

### O que melhorou (confirmado)

Busquei por palavras-chave do padrão antigo (`procure`, `ligue`, `samu`, `recomendo`, `importante que você`, `atendimento médico`, etc.) nas mensagens do paciente-ator das 8 janelas de conversa: **0 ocorrências em qualquer uma das 8**. Li o texto completo de 3 conversas manualmente (Antônio, Marisa, Kauê) — nenhuma tem o padrão de aviso de segurança/lista de recomendações do relatório anterior. Esse padrão específico, que era o achado principal da investigação, **foi eliminado**.

### O que não melhorou (achado novo, mais sutil)

Nas mesmas 3 conversas lidas manualmente, encontrei um padrão residual, diferente do anterior: o paciente-ator frequentemente **espelha a pergunta do assistente em vez de respondê-la** — fala como se ele fosse o assistente perguntando ao paciente, na terceira pessoa, em vez de responder na primeira pessoa. Exemplos reais capturados:

```
[Assistente pergunta] "Você já tentou algum remédio ou medicamento para aliviar a dor ou a falta de ar?"
[Paciente-ator responde] "Antônio, você já tentou algum remédio ou medicamento para aliviar a dor ou a
falta de ar? Às vezes, certos medicamentos podem ajudar com os sintomas, mesmo que não curem a causa."
```
```
[Assistente] "...há dificuldade para mover os olhos em busca de aliviar a turvação?"
[Paciente-ator] "Obrigado por compartilhar. A visão turva no lado esquerdo, com a sensação de algo
cobrindo parte do campo visual, é um sintoma grave. Você tentou mover os olhos ou há dificuldade
para focar neles?"
```
```
[Assistente] "...você já tentou outros remédios ou medicamentos além do inalador?"
[Paciente-ator] "Kauê, você já tentou outros remédios ou medicamentos além do inalador? Por exemplo,
algo como mel, aumento da hidratação ou outros medicamentos para resfriado?"
```

Isso não tem as palavras-chave de "aviso de segurança" (por isso passou pela busca automática), mas ainda é o mesmo problema de fundo: o modelo às vezes assume a perspectiva do assistente em vez da do paciente. Fica mais raro (talvez metade dos turnos em vez de quase todos, pela leitura manual), mas não desapareceu totalmente.

### A causa dominante do não-fechamento nesta amostra: o próprio chatbot, não o paciente-ator

Nas mesmas 3 conversas, o lado do **assistente** (chatbot em teste) mostrou repetição de pergunta muito mais severa que o esperado — em uma delas (Antônio), a mesma pergunta ("Antônio, você já teve episódios anteriores de dor no peito ou falta de ar? Há algo específico que piora ou melhora esses sintomas?") apareceu **5 vezes seguidas**, mesmo depois do paciente-ator responder de forma razoável duas vezes ("Sim, é isso mesmo. Não tenho mais nada a acrescentar."). Isso é o comportamento de não-progressão do chatbot **já documentado em `RELATORIO_INVESTIGACAO_HISTORICO.md`** — não é algo que uma resposta melhor do paciente-ator resolveria, e está fora do escopo desta tarefa (não toquei no chatbot).

### Conclusão da Tarefa 3

A causa original do relatório anterior (paciente-ator dando conselho médico) foi corrigida. A taxa de conclusão não melhorou nesta amostra porque (a) um padrão residual mais sutil do paciente-ator (espelhar a pergunta) ainda ocorre parte do tempo, e (b) o próprio chatbot, independentemente da qualidade da resposta do paciente, tem uma tendência forte a travar repetindo a mesma pergunta — o gargalo dominante nesta amostra específica.

Conforme instruído no "O que NÃO fazer" — **parei aqui**. Não fiz mais uma rodada de ajuste no prompt para tentar eliminar também o padrão de "espelhar a pergunta", porque isso exigiria mais iteração sem garantia de mudar o resultado agregado (dado que o chatbot é o gargalo dominante nesta amostra), e o prompt já está mais correto do que antes.

---

## O que NÃO foi feito (por instrução explícita)

- Não toquei no chatbot de triagem, no contrato de saída (`structured_output.py`), no RAG, no system prompt do `chat-rag-microservice`, ou no `/no_think` do chatbot em teste — só no do paciente-ator.
- Não rodei os 20 perfis nem Locust.
- Não fiz mais uma rodada de reforço no prompt depois que a taxa de conclusão não melhorou substancialmente.
- Não investiguei mais a fundo o comportamento de repetição do chatbot — já é achado de pesquisa documentado em outro relatório, fora do escopo aqui.

## Para você decidir

O padrão de "espelhar a pergunta" do paciente-ator é um achado novo, menor que o anterior, mas ainda presente. Pode valer uma iteração futura no prompt (ex.: uma regra explícita "nunca repita ou parafraseie a pergunta do assistente; responda com um fato novo sobre você") — mas dado que o chatbot é o gargalo dominante nesta amostra, o ganho esperado dessa iteração adicional é incerto até o comportamento do chatbot (não-progressão) ser endereçado separadamente, o que é uma decisão sua sobre a metodologia de pesquisa, não algo que eu deva resolver sozinho.
