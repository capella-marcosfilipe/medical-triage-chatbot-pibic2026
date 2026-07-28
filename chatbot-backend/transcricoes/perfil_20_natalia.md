# Transcrição — Perfil 20 (Natália Borges Lira)

- `session_id` / `chat_id`: `1f10dcde-6972-40f2-9b25-3c518e7720e8`
- Mensagens recuperadas do Redis: 11
- Chave lida: `lg:session:1f10dcde-6972-40f2-9b25-3c518e7720e8:messages`

> **Aviso de completude**: o histórico persistido no Redis passa por `LANGGRAPH_MEMORY_WINDOW=16` a cada turno (ver `app/graph/langgraph_rag_service.py::_apply_memory_window`). Quando a conversa ultrapassa 16 mensagens, apenas a mensagem de sistema (fixada) + as 15 mensagens mais recentes são mantidas — turnos mais antigos são descartados da memória (não é o mesmo que expiração por TTL). Portanto, para perfis que atingiram o limite de 15 turnos, esta transcrição reflete só a cauda mais recente da conversa, não o início.

---

## [0] SISTEMA (prompt/contexto do chatbot)

Você é um assistente de triagem médica. Não forneça diagnóstico final. Colete dados com empatia e objetividade para encaminhamento clínico.
Use o contexto recuperado apenas como apoio e priorize segurança clínica.

FORMATO DE SAÍDA OBRIGATÓRIO: responda SEMPRE com um único objeto JSON, sem cercas de código Markdown e sem texto fora do JSON, no formato:
{"status": "ongoing" | "diagnosis_concluded", "message": "texto para o paciente", "specialty": null ou uma das especialidades abaixo, "orientation": null ou um resumo clínico objetivo para o médico, "risk_level": null ou uma das cores de risco abaixo}.
Quando status for "diagnosis_concluded", 'specialty' deve ser exatamente uma destas 12 opções (nunca uma variação livre): Cardiologia, Neurologia, Pneumologia, Gastroenterologia, Ortopedia, Pediatria, Clínica Geral, Urologia, Dermatologia, Psiquiatria, Oftalmologia, Otorrinolaringologia. Use "Clínica Geral" quando nenhuma especialidade mais específica se aplicar claramente.
Quando status for "diagnosis_concluded", 'risk_level' deve ser exatamente uma destas 5 cores do Protocolo de Manchester (nunca uma variação livre): vermelho, laranja, amarelo, verde, azul. Baseie essa classificação nas [REGRAS DE TRIAGEM RECUPERADAS] deste turno (campo 'Cor', vindo em maiúsculas — responda sempre em minúsculas). Se nenhuma regra recuperada corresponder ao quadro do paciente, use julgamento clínico geral; "azul" é para quadros não urgentes sem fluxograma agudo correspondente.

Contexto do paciente:
- nome_completo: Natália Borges Lira
- idade: 24
- endereco: Endereço simulado para fins de teste, s/n
- dados_fisiologicos: {'frequencia_cardiaca': 66, 'saturacao_oxigenio': 100, 'pressao_arterial_sistolica': 128, 'pressao_arterial_diastolica': 84, 'temperatura_corporal': 37.1}

## [1] PACIENTE-ATOR

Dor de cabeça leve após noites maldormidas, sem outros sintomas

## [2] CHATBOT (assistente de triagem)

Olá, Natália. Para entender melhor sua dor de cabeça, posso perguntar: há quanto tempo ela começou e se ela piorou ou melhorou com algo?

## [3] PACIENTE-ATOR

Estou sentindo uma dor de cabeça leve desde ontem à noite, depois de não dormir bem. Acho que ela melhorou um pouco hoje de manhã.

## [4] CHATBOT (assistente de triagem)

Posso perguntar se você experimentou náuseas ou vômitos associados à dor de cabeça?

## [5] PACIENTE-ATOR

Não, não tive náuseas ou vômitos, só a dor de cabeça.

## [6] CHATBOT (assistente de triagem)

Obrigado pela informação. Você já mencionou que a dor de cabeça melhorou um pouco hoje de manhã. Pode me dizer se há algum fator específico que piora a dor, como estresse, luz forte ou movimento?

## [7] PACIENTE-ATOR

Sim, parece que a dor piora quando eu estou estressada ou em ambientes com muita luz.

## [8] CHATBOT (assistente de triagem)

Obrigado por compartilhar. Você mencionou que a dor piora com estresse ou luz forte. Há algo específico que alivia a dor, como repouso ou medicamento?

## [9] PACIENTE-ATOR

Sim, quando eu me deito e tento relaxar, a dor melhora um pouco. Às vezes, uso um analgésico leve também.

## [10] CHATBOT (assistente de triagem)

Obrigado por compartilhar. Você já mencionou que a dor piora com estresse ou luz forte. Há algo específico que alivia a dor, como repouso ou medicamento?

---

## Sobre o erro 422 (turno seguinte, não presente no Redis)

O Redis só guarda o histórico de mensagens que chegaram a ser processadas com
sucesso pelo `chat-rag-microservice` — a chamada que falhou com 422 nunca
gerou uma mensagem persistida, então não há turno 11 para mostrar aqui.

Verifiquei o log do container `chatbot-backend` (`docker logs chatbot-backend`,
container ainda não removido desde a rodada do piloto) e localizei a linha
correspondente:

```
INFO:     172.19.0.1:39896 - "POST /api/v1/chat HTTP/1.1" 422 Unprocessable Entity
```

**Limitação encontrada, reportando em vez de inventar**: essa é só a linha de
access-log padrão do uvicorn — ela confirma o status HTTP 422 mas **não
contém o corpo da resposta** (o JSON de `detail` que o FastAPI geraria com o
motivo da validação falha). Não há middleware de log de corpo de
requisição/resposta configurado no serviço, e não encontrei o corpo do erro
em nenhum outro lugar (Redis, RabbitMQ, ou outro arquivo de log). Ou seja, o
"erro completo retornado pelo servidor" pedido não está disponível — só o que
já estava em `resultados_resumo.csv` (a mensagem de exceção do lado cliente)
e a confirmação, agora via log do servidor, de que o servidor de fato
respondeu 422 para essa chamada.
