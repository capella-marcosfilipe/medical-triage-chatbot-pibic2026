# Relatório de Investigação — Anomalia de Latência no Piloto (Paciente 2)

## Resposta curta

**Causa confirmada com evidência direta (histórico do LangGraph + chaves reais do Redis), não é adivinhação.** A queda de latência a partir do turno 9 não é bug de janela de memória nem colisão acidental de `idempotency_key` — é o **cache de idempotência do worker** (`chat-rag-microservice/app/worker/base_worker.py`) funcionando exatamente como projetado, só que disparado por um **comportamento do paciente-ator** (não do chatbot em teste): a partir de certo ponto da conversa da Marisa, `gerar_resposta_paciente()` passou a gerar a mesma mensagem, ipsis litteris, em vários turnos. Como o `idempotency_key` é derivado só do conteúdo da mensagem (não do número do turno), mensagens repetidas geram a mesma chave — e o worker devolve uma resposta antiga em cache em vez de chamar o Nemotron de novo.

Isso tem duas causas distintas, e são de naturezas diferentes:

1. **Gatilho — comportamento de modelo** (paciente-ator "quebrando personagem"): não é bug, é achado de pesquisa, mesmo tratamento das investigações anteriores.
2. **Mecanismo que transforma isso num problema — gap real de engenharia**: o cache de idempotência do worker não diferencia "o cliente reenviou a mesma requisição por timeout" de "o paciente disse a mesma frase de novo, minutos depois, numa conversa legítima". Isso pode acontecer com **qualquer paciente real**, não só em simulação — proponho correção abaixo, **não apliquei**.

---

## Tarefa 0 — Reprodução e Diagnóstico

### Passo 1 — CSV confirma a anomalia relatada

```
Paciente 2 (Marisa), chat_status por turno (resultados_chamadas.csv):
turno 1: 2073.53ms   turno 6: 3611.71ms   turno 11: 24.39ms
turno 2: 3599.04ms   turno 7: 3613.03ms   turno 12: 22.27ms
turno 3: 4114.02ms   turno 8: 3613.37ms   turno 13: 22.98ms
turno 4: 3601.61ms   turno 9: 24.75ms     turno 14: 26.45ms
turno 5: 3608.82ms   turno 10: 22.92ms    turno 15: 24.72ms
```

`chat_enqueue` (turnos 1-15) ficou estável em 49-70ms o tempo todo — a latência não "migrou" para o enqueue, ela desapareceu do lado do processamento.

### Passo 2 — `log_simulacao.json` não tinha o conteúdo das mensagens

Confirmado: o log JSON só grava `chamadas_http` (durações) e o resumo final — `historico_llm` (mensagens enviadas/recebidas por turno) nunca foi persistido nele. Isso não impediu a investigação porque o piloto rodou há ~15 minutos e os dados relevantes ainda estavam vivos no Redis (TTLs de 24h).

### Passo 3 — Histórico real do LangGraph (Redis) para a sessão da Marisa

```
session_id = 53dd1ccb-b09d-4a39-a7f4-16f677bd03bb
redis-cli GET "lg:session:53dd1ccb-b09d-4a39-a7f4-16f677bd03bb:messages"
```

A janela de memória (16 mensagens, sistema fixado) cobre aproximadamente os turnos finais (8-15). As mensagens de **paciente** (role `user`, texto que `simulador.py` enviou) nessa janela são só **2 strings distintas, repetidas várias vezes, byte a byte idênticas**:

- Variante A (356 caracteres, aparece 5x): `"**Lembre-se:**  \n- **Procure ajuda médica imediatamente** (ligue para o 192, 911 ou outro número de emergência no seu país).  \n- **Anote o horário exato** em que os sintomas começaram, se possível.  \n\nUm profissional de saúde precisa avaliá-lo pessoalmente. Estou aqui para orientar, mas não posso substituir o atendimento médico direto. Fique seguro(a)! 🙏"`
- Variante B (416 caracteres, aparece 2x): a mesma variante A com um prefixo extra ("Isso pode ajudar a avaliar a situação com mais precisão.").

Ou seja: em vez de descrever sintomas como um paciente (conforme o system prompt de `PATIENT_SYSTEM_PROMPT_TEMPLATE`), o paciente-ator passou a gerar um **aviso de segurança genérico estilo "procure ajuda médica"**, repetido quase sempre igual. As respostas do **assistente** (chatbot em teste) na mesma janela também colapsaram para só 2 variantes repetidas — mas isso é consequência do passo seguinte, não causa.

### Passo 4 — Confirmação direta no Redis: chave de idempotência do worker está lá, a do endpoint não

`_build_idempotency_key(chat_id, engine, message)` em `chatbot-backend/app/api/v1/endpoints.py:64` é `sha256(f"{chat_id}:{engine}:{message}")`. `chat_id` é constante (= `session_id`) e `engine` é sempre `"nemotron"` durante toda a conversa — então a chave depende só do texto de `message`. Calculei a chave para as duas variantes acima com o `chat_id` real da Marisa:

```
variante A (356 chars) → 70225985af9a8d0f318722dc8820d4cca7390b954cf932fd7b52b694db4c5b7b
variante B (416 chars) → cfbee220ccb26aeb48e6a0c47c32b4754b5a3922bd07098e90cc2a2596afe0fe
```

Verifiquei as duas chaves possíveis no Redis real:

```
$ redis-cli EXISTS "idempotency:worker:70225985af9a..." → 1   (existe)
$ redis-cli EXISTS "idempotency:worker:cfbee220ccb..."  → 1   (existe)
$ redis-cli EXISTS "idempotency:chat:70225985af9a..."   → 0   (NÃO existe)
$ redis-cli TTL "idempotency:worker:70225985af9a..."    → 85301s (~23.7h, bate com IDEMPOTENCY_TTL=86400 setado ~19min antes)
```

Isso isola precisamente **onde** o curto-circuito acontece: **no worker** (`chat-rag-microservice/app/worker/base_worker.py:102-116`, `idempotency.get_worker_cached_result(idempotency_key)`), não no decorator do endpoint (`app/presentation/chat.py:71`, `@idempotency.idempotent("chat")`, que usa a chave `idempotency:chat:*` e não tinha entrada). É por isso que `register_user_message` (que grava a mensagem do paciente no LangGraph) **continuou rodando normalmente a cada turno** — cada turno gerou um `job_id` novo de verdade — só que o **worker**, ao processar esse job novo, encontrou uma resposta em cache para aquele `idempotency_key` e devolveu ela na hora, sem chamar o Nemotron:

```json
// conteúdo real cacheado sob idempotency:worker:70225985af9a...
{
  "response": "Olá, Marisa. Os sintomas que você descreveu, como fraqueza súbita no lado direito, fala embolada e desvio de rosto, são preocupantes. ...",
  "latency_ms": 3577.67,
  "specialty": "Neurologia",
  "risk_level": "vermelho",
  ...
}
```

O `latency_ms: 3577.67` gravado dentro da própria resposta cacheada confirma que ela foi gerada de verdade **uma vez** (chamada real ao Nemotron, ~3.6s, batendo com os turnos 1-8), e depois reaproveitada em cada turno subsequente que repetiu a mesma mensagem — cada reaproveitamento levando só os ~22-26ms de round-trip Redis, não os ~3.6s originais.

### Passo 5 — Comparação com o paciente 3 (Kauê), que não mostrou a anomalia

```
session_id = 17c756d4-98fa-4097-9870-5e41244b25ef
Mensagens do paciente (role user) na janela: 7 totais, 7 distintas (0 repetição)
Mensagens do assistente na janela: 8 totais, 4 distintas (alguma repetição de pergunta, já documentada como comportamento de modelo)
```

Diferença crucial: o paciente-ator do Kauê **nunca repetiu a própria mensagem** dentro da janela visível — cada turno tem um texto diferente, então nenhum `idempotency_key` colidiu, então o worker nunca encontrou cache, então todos os 15 turnos do Kauê chamaram o Nemotron de verdade (latência consistente ~2000-3600ms do início ao fim, conforme já reportado). Isso confirma que a anomalia é específica de quando o *conteúdo enviado pelo simulador* se repete — não uma característica geral do sistema, do perfil de AVC, ou dos sinais vitais fixos.

---

## Causa raiz — resumo da cadeia completa

1. **[Comportamento de modelo, não bug]** Em algum ponto da conversa da Marisa (antes do turno 9, fora da janela de 16 mensagens visível no Redis), `gerar_resposta_paciente()` — a chamada separada ao Nemotron que interpreta o paciente — parou de descrever sintomas e passou a gerar um aviso de segurança genérico ("procure ajuda médica imediatamente..."), repetindo esse texto quase palavra por palavra em turnos subsequentes.
2. **[Consequência mecânica, esperada]** `chat_id` e `engine` são constantes durante toda a conversa; como `idempotency_key = sha256(chat_id:engine:message)`, mensagens de paciente idênticas geram a mesma chave.
3. **[Gap de engenharia real]** O worker (`base_worker.py:102-116`) trata qualquer `idempotency_key` repetida — mesmo minutos depois, dentro de uma conversa em andamento — como uma requisição duplicada (ex.: retry de rede) e devolve a resposta cacheada de até 24h atrás (`IDEMPOTENCY_TTL = 86400`, `app/infrastructure/settings.py:43`) sem chamar o modelo de novo.

O item 1 é o gatilho específico desta execução (documentar como achado, não corrigir — mesma diretriz das investigações anteriores). O item 3 é o que eu considero **um bug real e específico**: o mecanismo de idempotência foi desenhado para proteger contra reenvio de uma *mesma tentativa de requisição* (ex.: timeout de rede fazendo o cliente reenviar o mesmo POST), mas hoje ele também trata como duplicata qualquer mensagem cujo *conteúdo* coincida com uma mensagem anterior da mesma conversa — o que pode acontecer com um paciente real dizendo a mesma frase duas vezes (“sim, ainda dói”, “não sei”, etc.), não só com este artefato do simulador. Um paciente real nessa situação receberia uma resposta desatualizada e travada em cache por até 24h, sem o modelo processar o que ele disse de fato.

---

## Proposta de correção (NÃO aplicada — aguardando sua decisão)

Não mexi em nada. Três opções, da mais simples/segura à mais estrutural:

**Opção A — Encurtar o TTL do cache de idempotência do worker** (`IDEMPOTENCY_TTL`, hoje 86400s/24h, usado tanto em `cache_response` quanto em `cache_worker_result` em `app/jobs/idempotency.py:38,67`). Um TTL de, por exemplo, 30-60 segundos ainda protegeria contra o caso real de uso (cliente reenviando a mesma requisição por timeout, que acontece em segundos) sem afetar conversas legítimas onde o mesmo texto pode reaparecer minutos depois. É a mudança de menor risco — um único valor de configuração, não mexe em lógica. Exigiria decidir se o TTL do endpoint (`idempotency:chat:*`) e do worker (`idempotency:worker:*`) devem ter o mesmo valor ou ser separados (hoje compartilham a mesma constante).

**Opção B — Remover o cache de idempotência do nível do worker**, mantendo só o do endpoint (`@idempotency.idempotent("chat")`), que já protege contra o cenário mais comum de duplicata (cliente reenvia o POST antes de receber a resposta do primeiro). O cache do worker parece redundante com esse — mas eu não tenho certeza de qual cenário específico motivou adicioná-lo separadamente (ex.: proteção contra reprocessamento se uma mensagem RabbitMQ for reentregue por algum motivo), então essa opção merece uma checagem sua antes de eu mexer.

**Opção C — Tornar a chave de idempotência independente de conteúdo repetido**, incluindo algo que mude a cada tentativa legítima de envio (ex.: um identificador de tentativa gerado pelo cliente, não derivado do texto da mensagem). Mais correta arquiteturalmente, mas é a mudança mais estrutural — mexe no formato do `idempotency_key` ponta a ponta (`chatbot-backend` → `chat-rag-microservice`), então tem mais superfície de risco antes do piloto.

**Minha recomendação, se quiser que eu aplique algo:** Opção A. É a menor mudança, resolve o problema prático (paciente real repetindo uma frase não deveria travar em cache por 24h) sem tocar em nenhuma lógica de roteamento/fila/LangGraph — só um valor de TTL menor especificamente para o cache do worker.

---

## O que NÃO foi feito (por instrução explícita)

- Não corrigi nada nesta execução — só diagnostiquei, com evidência direta (histórico real do Redis + chaves de idempotência confirmadas, não inferência).
- Não rodei os 20 perfis nem Locust.
- Não mexi no paciente 3 (Kauê) nem tentei "consertar" a não-convergência dele — está fora desta investigação, já documentada como achado de pesquisa separado.
- Não investiguei por que o paciente-ator da Marisa especificamente quebrou personagem para esse texto de aviso de segurança (hipótese razoável: o modelo reage à combinação de sintomas de AVC + idade + urgência com uma resposta de segurança treinada, mas eu não confirmei isso — fica como uma pergunta em aberto, não uma afirmação).
