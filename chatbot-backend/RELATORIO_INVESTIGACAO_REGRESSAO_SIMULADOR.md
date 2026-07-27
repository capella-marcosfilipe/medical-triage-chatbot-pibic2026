# Relatório de Investigação — "Regressão" no `simulador.py` (0% de Conclusão)

## Resposta curta

**A hipótese de regressão de código está descartada — confirmei isso, não presumi.** O trecho que lê `content.diagnosis_status` e decide se o loop de turnos continua ou para **não mudou** entre a versão do piloto bem-sucedido (`b357d2d`) e a atual (`git diff` colado abaixo). Reproduzi uma conversa do Antônio direto via `curl`, fora do `simulador.py`, com respostas plausíveis de paciente — **o servidor concluiu normalmente em 8 turnos**, com `specialty: Cardiologia` e `risk_level: vermelho` corretos. Isso isola definitivamente: não é o servidor, não é a lógica de decisão do loop no `simulador.py`.

**A causa real: o paciente-ator (`gerar_resposta_paciente()`) está saindo do personagem** e gerando texto de "assistente de saúde genérico" (avisos de segurança, listas de recomendações, devolvendo a pergunta do chatbot em vez de respondê-la como paciente) em praticamente todos os 20 perfis desta rodada — não só na Marisa, como no achado anterior. Como o "paciente" nunca responde de fato às perguntas clínicas do chatbot, o chatbot nunca reúne informação suficiente pra concluir, e a conversa esgota os 15 turnos em `ongoing`.

**Isso não é um bug novo nem uma regressão de código — é o mesmo fenômeno já documentado no `RELATORIO_INVESTIGACAO_ANOMALIA_PILOTO.md` para a Marisa, só que desta vez atingindo quase todos os 20 perfis em vez de 1 de 3.** Não é nada que meus commits recentes tenham introduzido (nenhum deles toca `PATIENT_SYSTEM_PROMPT_TEMPLATE` ou a lógica de decisão do loop). **Não apliquei nenhuma correção**, porque a Tarefa 0 não encontrou o bug hipotetizado — corrigir isso significaria reabrir a engenharia do prompt do paciente-ator, que é uma decisão de pesquisa sua, não um bug de engenharia.

---

## Tarefa 0 — Diagnóstico

### Passo 1 — `git diff` do trecho de decisão do loop

```
$ git diff b357d2d HEAD -- chatbot-backend/simulador.py
```

O trecho relevante (leitura de `content`, checagem de `diagnosis_status`, condição do `while`) é **idêntico** entre as duas versões:

```python
diagnosis_status = "ongoing"
...
while turno < MAX_TURNS and diagnosis_status != "diagnosis_concluded":
    ...
    content = status_payload.get("content") or {}
    resposta_bot = content.get("answer", "")
    diagnosis_status = content.get("diagnosis_status", "ongoing")
    ...
    if diagnosis_status == "diagnosis_concluded":
        especialidade_retornada = content.get("specialty")
        nivel_urgencia_obtido = content.get("risk_level")  # <- única linha nova aqui
        ...
        break
```

A única mudança dentro desse bloco desde o piloto foi a leitura de `content.get("risk_level")`, adicionada **depois** do `if diagnosis_status == "diagnosis_concluded":` — ou seja, só roda quando a condição já é verdadeira. Não pode ser a causa de o loop nunca entrar nesse `if`. **Hipótese do prompt (nome de campo errado, comparação case-sensitive diferente, exceção engolida) descartada por leitura direta do diff, não por suposição.**

### Passo 2 — Reprodução direta via `curl`, fora do `simulador.py`

Sessão nova, mesmo texto de sintomas do Antônio (infarto, com prefixo de sinais vitais), respondendo como um paciente real responderia (não através do paciente-ator quebrado):

| Turno | Paciente disse | Resposta do chatbot | `diagnosis_status` |
|---|---|---|---|
| 1 | "[vitais] Dor forte no peito irradiando para o braço esquerdo, sudorese fria e falta de ar há 20 minutos" | "Pode me contar mais sobre a dor... piorou ou melhorou?" | ongoing |
| 2 | "Começou de repente, há uns 20 minutos... a dor está piorando" | "Tem histórico de doenças cardíacas...?" | ongoing |
| 3 | "Sim, está piorando. Não tenho histórico... mas meu pai teve infarto" | "Outros sintomas como náusea, tontura...?" | ongoing |
| 4 | "Sim, tenho náusea e sensação de pressão forte no peito" | "Já teve episódios anteriores...?" | ongoing |
| 5 | "Não, nunca tinha sentido isso antes..." | "Há algo mais que eu deva saber...?" | ongoing |
| 6 | "Não, é só isso. Pode concluir?" | (repetiu a pergunta do turno 5 — comportamento de modelo já documentado, não travou nada) | ongoing |
| 7 | "Já respondi isso... conclua agora" | "...a pressão é constante ou varia com a respiração?" | ongoing |
| 8 | "É constante... a dor está piorando muito, mal consigo respirar, é uma emergência" | **"Sua situação parece grave. Recomendo atendimento de emergência imediatamente."** | **`diagnosis_concluded`** |

Resposta completa do turno 8:
```json
{"content":{"answer":"Antônio, sua situação parece grave. Recomendo que você procure atendimento de emergência imediatamente. Leve-se a um pronto-socorro ou ligue para o serviço de emergência mais próximo.","processing_time_ms":4192.01,"diagnosis_status":"diagnosis_concluded","specialty":"Cardiologia","orientation":"Paciente com dor torácica aguda, piorando, irradiando para braço esquerdo, associada a náusea, sensação de pressão no peito, taquicardia (118 bpm), hipoxemia (SpO2 91%) e histórico familiar de infarto. Requer avaliação imediata para possíveis causas cardiovasculares.","risk_level":"vermelho"}}
```

**O servidor conclui normalmente** (8 turnos, dentro do limite de 15), com `specialty` e `risk_level` corretos, quando alimentado com respostas de paciente de verdade. Confirma: nem o servidor, nem a lógica de decisão do `simulador.py` estão quebrados.

### Passo 3 — O que o paciente-ator realmente enviou na rodada real (evidência do Redis)

Como as sessões da rodada de 20 perfis ainda estavam vivas no Redis (TTL de 24h do LangGraph), examinei o histórico real de 3 perfis distintos da rodada que travou:

**Perfil 1 (Antônio)** — o assistente pergunta repetidamente "a dor no peito está piorando ou melhorando?" e o paciente-ator nunca responde isso diretamente; em vez disso, gera avisos de segurança genéricos:
```
"**Isso é crucial para determinar a gravidade da situação.**
- Se a dor **piorar ou persistir**, é **urgente procurar um médico imediatamente**...
**Enquanto isso:**
1. **Fique em repouso** e evite movimentos bruscos.
2. **Respire profundamente**..."
```
(7 mensagens de paciente na janela visível, alternando entre 2-3 variantes muito parecidas desse mesmo texto — não uma resposta de paciente a uma pergunta clínica.)

**Perfil 6 (Elza, sem sinais vitais fixos)** — mesmo padrão, formato "conselho de bem-estar":
```
"Esses sinais podem ajudar a identificar se há necessidade de avaliação médica mais urgente.
Enquanto isso, continue seguindo as orientações: hidrate-se, descanse e evite esforço.
Se os sintomas piorarem ou persistirem, consulte um médico. Espero que se sinta melhor em breve! 🌟"
```
(Aqui as 7 mensagens são todas distintas entre si — ou seja, isso não é nem o bug de idempotência antigo, confirma o que você já tinha descartado pelas latências.)

**Perfil 19 (Fábio)** — variante diferente do mesmo problema: o paciente-ator devolve a pergunta do chatbot em formato de lista, como se ele fosse o assistente:
```
"Por exemplo:
- Ela aparece logo após comer ou algumas horas depois (como à noite)?
- Alguma bebida ou alimento... piora os sintomas?"
```

Em nenhum dos 3 casos o "paciente" respondeu como um paciente respondeira — descrevendo a própria experiência. Cada um manifesta a quebra de personagem de um jeito ligeiramente diferente (aviso de segurança, conselho de bem-estar, pergunta em formato de lista), mas a raiz é a mesma: `gerar_resposta_paciente()` (o Nemotron interpretando `PATIENT_SYSTEM_PROMPT_TEMPLATE`) não está seguindo a instrução de atuação.

---

## Por que isso não apareceu (tanto) no piloto de 3 perfis?

No piloto (`--limit 3`), só a Marisa (perfil 2) mostrou esse padrão — Antônio e Kauê concluíram normalmente. Nesta rodada de 20, quase todos mostraram o padrão. Isso é consistente com uma amostra pequena (n=3) vs. grande (n=20): se a "quebra de personagem" tem uma chance razoável de acontecer em algum turno de qualquer conversa (e, uma vez que acontece, tende a se perpetuar — o histórico "contaminado" influencia os próprios turnos seguintes do paciente-ator), é esperado que 2/3 escapem por sorte numa amostra de 3, mas quase nenhum escape numa amostra de 20. Não encontrei nenhuma mudança de código entre as duas rodadas que explique um aumento sistemático da taxa — os únicos commits entre o piloto bem-sucedido e esta rodada foram o carregamento de `.env`, o fix de `content` vazio, logging, e o TTL de idempotência (nenhum deles toca `PATIENT_SYSTEM_PROMPT_TEMPLATE` ou o texto enviado ao paciente-ator). Registro isso como hipótese razoável para a diferença de taxa, não como fato confirmado — eu não tenho como isolar "sorte estatística" de "algo sutil que pode ter mudado" com uma amostra de 3 vs. 20.

---

## O que NÃO fiz (Tarefa 1 não se aplica)

A Tarefa 1 do prompt ("corrija especificamente o que a Tarefa 0 encontrar") pressupõe um bug de código — a Tarefa 0 não encontrou um. O que encontrei é o mesmo comportamento de modelo já registrado no `RELATORIO_INVESTIGACAO_ANOMALIA_PILOTO.md`, agora mais frequente. Não toquei em:

- `PATIENT_SYSTEM_PROMPT_TEMPLATE` ou qualquer parte de `gerar_resposta_paciente()` — endurecer esse prompt para forçar o modelo a "ficar no personagem" seria engenharia de prompt sobre uma variável de pesquisa, mesma linha das investigações anteriores em que fui instruído a não fazer isso sem pedido explícito.
- A lógica de decisão do loop (`while`/`diagnosis_status`) — confirmada correta, sem necessidade de mudança.
- O mecanismo de idempotência — já corrigido antes, e esta investigação confirma que ele **não** é a causa desta vez (você já tinha descartado isso pelas latências, e a evidência do Redis reforça: mensagens distintas entre si na Elza, sem colisão de chave).
- `smartwatch_simulator.py`, mecanismo de prefixo de vitais, `chat-rag-microservice`.
- Não rodei os 20 perfis nem Locust de novo.

## Para você decidir

Isso é um achado de pesquisa relevante para a metodologia: o paciente-ator sintético (não o chatbot em teste) tem uma taxa alta de "quebra de personagem" que impede a conversa de progredir, especialmente perceptível em escala. Algumas direções possíveis, sem que eu tenha tomado nenhuma decisão por você:

1. Aceitar como limitação conhecida do desenho do simulador e documentar na metodologia (mesma linha do achado de não-convergência já registrado).
2. Ajustar `PATIENT_SYSTEM_PROMPT_TEMPLATE` para reforçar mais explicitamente "responda apenas como paciente, nunca dê conselhos médicos ou de segurança" — isso mudaria o comportamento do paciente-ator, não do chatbot em teste, então é uma mudança na *ferramenta de simulação*, não no sistema sendo avaliado. Ainda assim, prefiro não fazer isso sem seu pedido explícito, já que só você sabe se isso é desejável cientificamente ou se contamina a metodologia.
3. Investigar se `/no_think` (adicionado ao paciente-ator numa correção anterior, para evitar `content: None`) torna esse comportamento mais provável do que seria com raciocínio habilitado — não testei essa hipótese especificamente.
