# Transcrição — Perfil 1 (Antônio Ferreira)

- `session_id` / `chat_id`: `cfc0c098-a18d-4345-b511-7dbe4afcf83f`
- Mensagens recuperadas do Redis: 16
- Chave lida: `lg:session:cfc0c098-a18d-4345-b511-7dbe4afcf83f:messages`

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
- nome_completo: Antônio Ferreira
- idade: 67
- endereco: Endereço simulado para fins de teste, s/n
- dados_fisiologicos: {'frequencia_cardiaca': 81, 'saturacao_oxigenio': 98, 'pressao_arterial_sistolica': 110, 'pressao_arterial_diastolica': 81, 'temperatura_corporal': 36.6}

## [1] CHATBOT (assistente de triagem)

Antônio, a falta de ar piora com movimentos simples. Você já tentou sentar-se ou deitar para aliviar a sensação de falta de ar?

## [2] PACIENTE-ATOR

Antônio, sim, tentei sentar-me e deitar, mas a falta de ar não melhora. A sensação de pressão no peito também persiste.

## [3] CHATBOT (assistente de triagem)

Antônio, a falta de ar piorando com movimentos simples e a dor constante no peito são sinais que preocupam. Você já tentou usar um inalador ou qualquer medicamento para aliviar os sintomas?

## [4] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [5] CHATBOT (assistente de triagem)

Antônio, a falta de ar piora com movimentos simples. Você já tentou sentar-se ou deitar para aliviar a sensação de falta de ar?

## [6] PACIENTE-ATOR

Antônio, sim, tentei sentar-me e deitar, mas a falta de ar não melhora. A sensação de pressão no peito também persiste.

## [7] CHATBOT (assistente de triagem)

Antônio, a falta de ar piorando com movimentos simples e a dor constante no peito são sinais que preocupam. Você já tentou usar um inalador ou qualquer medicamento para aliviar os sintomas?

## [8] PACIENTE-ATOR

Antônio, a falta de ar piora com movimentos simples. Você já tentou sentar-se ou deitar para aliviar a sensação de falta de ar?

## [9] CHATBOT (assistente de triagem)

Antônio, a falta de ar persistente e a dor no peito são preocupantes. Você já procurou outro profissional de saúde anteriormente por esses sintomas?

## [10] PACIENTE-ATOR

Antônio, a falta de ar piorando com movimentos simples e a dor constante no peito são sinais que preocupam. Você já procurou outro profissional de saúde anteriormente por esses sintomas? Às vezes, uma avaliação anterior pode ajudar a entender melhor a situação.

## [11] CHATBOT (assistente de triagem)

Antônio, a falta de ar persistente e a dor no peito são sintomas que exigem atenção. Você já teve algum histórico de doenças cardíacas, pulmonares ou outras condições que possam estar relacionadas a esses sintomas?

## [12] PACIENTE-ATOR

Antônio, a falta de ar persistente e a dor no peito são sintomas que exigem atenção. Você já teve algum histórico de doenças cardíacas, pulmonares ou outras condições que possam estar relacionadas a esses sintomas? Às vezes, fatores como estresse, dieta ou atividade física intensa podem influenciar a sensação de falta de ar e dor no peito.

## [13] CHATBOT (assistente de triagem)

Antônio, você já tentou aliviar os sintomas com repouso ou posicionamento específico? Por exemplo, se inclinar para frente ou deitar com as pernas elevadas?

## [14] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [15] CHATBOT (assistente de triagem)

Antônio, você já tentou outros remédios ou medidas para aliviar a falta de ar e a dor no peito?
