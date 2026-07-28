# Transcrição — Perfil 6 (Elza Guimarães)

- `session_id` / `chat_id`: `ec0637b4-d312-4c3d-8542-f6ebf05e50fa`
- Mensagens recuperadas do Redis: 16
- Chave lida: `lg:session:ec0637b4-d312-4c3d-8542-f6ebf05e50fa:messages`

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
- nome_completo: Elza Guimarães
- idade: 71
- endereco: Endereço simulado para fins de teste, s/n
- dados_fisiologicos: {'frequencia_cardiaca': 85, 'saturacao_oxigenio': 97, 'pressao_arterial_sistolica': 115, 'pressao_arterial_diastolica': 74, 'temperatura_corporal': 36.2}

## [1] CHATBOT (assistente de triagem)

Elza, você mencionou que a dificuldade respiratória ocorre apenas ao tossir. Pode me confirmar se há algum inchaço no pescoço ou garganta, ou se a tosse está acompanhada de dor intensa?

## [2] PACIENTE-ATOR

A tosse não tem dor intensa, mas às vezes dói um pouco ao tossir forte. Não percebo inchaço no pescoço ou garganta, mas sinto que a garganta fica mais irritada depois da tosse.

## [3] CHATBOT (assistente de triagem)

Elza, você mencionou dificuldade respiratória ao tossir, mas não há chiado ou ruído anormal. Pode me confirmar se há inchaço no pescoço ou garganta, ou se a tosse está acompanhada de dor intensa?

## [4] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [5] CHATBOT (assistente de triagem)

Elza, você mencionou dificuldade respiratória ao tossir, mas não há chiado ou inchaço. Pode me confirmar se há histórico de doenças respiratórias prévias, como asma ou bronquite crônica?

## [6] PACIENTE-ATOR

Não, Elza. Não tenho histórico de doenças respiratórias antes disso.

## [7] CHATBOT (assistente de triagem)

Elza, você mencionou dificuldade respiratória apenas ao tossir, sem chiado ou inchaço. Pode me confirmar se há algum histórico de infecções respiratórias recentes, como gripe ou resfriado, nos últimos meses?

## [8] PACIENTE-ATOR

Elza, você não mencionou histórico de infecções respiratórias recentes. Pode me dizer se há algum contato com pessoas doentes ou viagens recentes que possam estar relacionadas aos sintomas?

## [9] CHATBOT (assistente de triagem)

Elza, você mencionou que a tosse pode causar dor leve. Pode me dizer se há algum alívio com medicamentos, como antitussivos, ou se a tosse piora em horários específicos?

## [10] PACIENTE-ATOR

Elza, você mencionou que a tosse pode causar dor leve. Pode me dizer se há algum alívio com medicamentos, como antitussivos, ou se a tosse piora em horários específicos?  

Também, como a dificuldade respiratória ocorre apenas ao tossir,

## [11] CHATBOT (assistente de triagem)

Elza, você mencionou que a dificuldade respiratória ocorre apenas ao tossir. Pode me confirmar se há algum inchaço no pescoço ou garganta, ou se a tosse está acompanhada de secreção, sangue ou corpo estranho?

## [12] PACIENTE-ATOR

Elza, você mencionou dificuldade respiratória ao tossir, mas não há chiado ou inchaço. Pode me confirmar se há secreção, sangue ou corpo estranho na tosse?  

Também, como a dificuldade respiratória ocorre sempre ao tossir, pode

## [13] CHATBOT (assistente de triagem)

Elza, você mencionou que a tosse pode causar dor leve. Pode me dizer se há algum alívio com medicamentos, como antitussivos, ou se a tosse piora em horários específicos?

## [14] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [15] CHATBOT (assistente de triagem)

Elza, você mencionou dificuldade respiratória ao tossir, mas não há chiado ou inchaço. Pode me confirmar se há histórico de doenças respiratórias prévias, como asma ou bronquite crônica?
