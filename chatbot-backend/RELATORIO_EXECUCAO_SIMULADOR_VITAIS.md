# Relatório de Execução — Sinais Vitais Fixos no `simulador.py`

## Contexto

`pacientes_sinteticos.json` já tinha, para os 5 perfis vermelho/laranja (ids 1-5),
uma chave `dados_fisiologicos_esperados` com sinais vitais fixos por condição,
definidos pelo pesquisador. Esta tarefa conectou esse dado, já existente, ao
fluxo de simulação em `simulador.py` — sem alterar valores clínicos, sem mexer
em `smartwatch_simulator.py` nem no endpoint `/get_smartwatch_data/{id}` de
produção.

## O que foi descoberto antes de codar

Antes desta mudança, o valor retornado por `GET /get_smartwatch_data/{id}` em
`simulador.py` era buscado (a latência era medida) mas **nunca era usado em
lugar nenhum** — nem no payload do `/chat`, nem em nenhum outro lugar do
script. Investigando o `chatbot-backend`, o mesmo vale em produção:
`session_manager.add_smartwatch_data()` existe mas não é chamada por nenhum
endpoint, então `session.dados_fisiologicos` nunca é preenchido e o
`patient_context` enviado ao `chat-rag-microservice` nunca carrega dados
fisiológicos — mesmo o `chat-rag-microservice` já sabendo formatar um
`patient_context` (`app/graph/langgraph_rag_service.py:169-178`) em texto para
o prompt do Nemotron.

Isso é uma lacuna de produção pré-existente, fora do escopo deste prompt (que
proíbe explicitamente tocar em `smartwatch_simulator.py` e no endpoint). Não
havia, portanto, nenhum caminho já funcional para "sinais vitais entrarem no
contexto da conversa com o Nemotron" sem alterar código de produção.

## Decisão de implementação

Como o `ChatNemotronRequest` do `/chat` só aceita `message`, `engine`,
`chat_id` (o `patient_context` estruturado nunca chega ao request do
cliente), a única forma mecânica de fazer os sinais vitais fixos "entrarem no
contexto" mexendo só em `simulador.py` foi **prefixar a mensagem do primeiro
turno enviada ao `/chat`** com uma nota curta no formato:

```
[Dados do smartwatch: FC 118 bpm, SpO2 91%, PA 96/62 mmHg, Temp 36.3°C] Dor forte no peito irradiando para o braço esquerdo, sudorese fria e falta de ar há 20 minutos
```

Esse prefixo:

- só é adicionado no **turno 1** de cada conversa;
- só é adicionado quando o perfil tem `dados_fisiologicos_esperados` (os
  outros 15 perfis continuam exatamente como antes, sem nenhum dado
  fisiológico entrando na mensagem);
- **não** entra no histórico usado para gerar as próximas falas do
  paciente-ator simulado (`historico_llm`) — o paciente-ator continua
  "vendo" e reagindo só aos sintomas verbais, não aos números do smartwatch.

O endpoint `/get_smartwatch_data/{id}` continua sendo chamado normalmente
para os 20 perfis (métrica de latência íntegra no log); para os 5 perfis com
dados fixos, o valor aleatório retornado é descartado.

## Mudanças em `simulador.py`

1. Função nova `formatar_contexto_vitais(dados_fisiologicos: dict) -> str`,
   que formata o dict de sinais vitais no texto de prefixo acima.
2. Em `simular_paciente`: leitura de `perfil.get("dados_fisiologicos_esperados")`
   e cálculo de `sinais_vitais_fixos` (booleano) logo no início.
3. Campo `sinais_vitais_fixos` adicionado ao log por paciente.
4. Prefixo de vitais aplicado ao `message` do `/chat` apenas no turno 1,
   apenas quando `sinais_vitais_fixos` é `True`.

## Smoke-test (`--limit 5`)

Não foi usado `simulador.py --limit 5` diretamente porque, sem
`NVIDIA_API_KEY` válida no ambiente local, o job de chat trava no
`chat-rag-microservice` até o timeout de 30s por turno — o que tornaria o
smoke-test lento sem agregar nenhuma confiança extra sobre o que estava sendo
testado (a montagem do payload, que acontece inteiramente no lado do cliente,
antes de qualquer resposta do servidor).

Em vez disso, subiu-se `chatbot-backend` + `rabbitmq` + `redis` +
`chat-rag-microservice` via `docker compose up -d`, e um script auxiliar
(fora do repositório, em `/tmp`) chamou `simulador.simular_paciente(...)`
diretamente para os 5 perfis, com um hook do `httpx` capturando o corpo real
de cada requisição `POST /chat` antes do envio. Para os 5 perfis, o `message`
capturado batia exatamente com `formatar_contexto_vitais(dados_fisiologicos_esperados)`
seguido do texto de `sintomas` original — confirmado por asserção automática
no script, ex.:

```
perfil 1: prefixo_correto=True
  mensagem enviada: '[Dados do smartwatch: FC 118 bpm, SpO2 91%, PA 96/62 mmHg, Temp 36.3°C] Dor forte no peito irradiando para o braço esquerdo, sudorese fria e falta de ar há 20 minutos'
```

Os 5 perfis reportaram `sinais_vitais_fixos=True` no log, como esperado. A
conversa em si não foi completada até `diagnosis_concluded` (sem
`NVIDIA_API_KEY` real, o turno 1 expira em ~30s aguardando o
`chat-rag-microservice`) — dentro do que o prompt permitiu explicitamente
("não precisa completar a conversa até o fim"). Os containers de teste foram
derrubados (`docker compose down`) ao final.

## O que não foi feito (fora de escopo, por instrução explícita)

- Nenhum valor de `dados_fisiologicos_esperados` foi alterado.
- `smartwatch_simulator.py` e o endpoint `/get_smartwatch_data/{id}` de
  produção não foram tocados — o comportamento aleatório em produção
  continua idêntico.
- A lacuna de produção descrita acima (`add_smartwatch_data` nunca chamada)
  não foi corrigida — fica registrada aqui como achado, não como bug deste
  script.
- Simulação completa dos 20 perfis não foi executada.
