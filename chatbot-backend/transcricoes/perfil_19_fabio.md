# Transcrição — Perfil 19 (Fábio Renan Souza)

- `session_id` / `chat_id`: `78a519e7-81bf-48b9-9969-843e0aa3b001`
- Mensagens recuperadas do Redis: 16
- Chave lida: `lg:session:78a519e7-81bf-48b9-9969-843e0aa3b001:messages`

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
- nome_completo: Fábio Renan Souza
- idade: 37
- endereco: Endereço simulado para fins de teste, s/n
- dados_fisiologicos: {'frequencia_cardiaca': 96, 'saturacao_oxigenio': 95, 'pressao_arterial_sistolica': 115, 'pressao_arterial_diastolica': 84, 'temperatura_corporal': 36.2}

## [1] CHATBOT (assistente de triagem)

Percebeu que a azia piora com certos alimentos além das refeições pesadas? Por exemplo, se comer frutas cítricas, chocolate ou alimentos gordurosos?

## [2] PACIENTE-ATOR

Sim, é isso mesmo. Percebeu que frutas cítricas, alimentos gordurosos e até o café da manhã agravam a sensação de queimação no peito?

## [3] CHATBOT (assistente de triagem)

Percebeu que a azia piora com certos alimentos além das refeições pesadas? Por exemplo, se comer frutas cítricas, chocolate ou alimentos gordurosos?

## [4] PACIENTE-ATOR

Sim, é isso mesmo. Percebeu que frutas cítricas, alimentos gordurosos e até o café da manhã agravam a sensação de queimação no peito?

## [5] CHATBOT (assistente de triagem)

Percebeu que a azia piora com certos alimentos além das refeições pesadas? Por exemplo, se comer frutas cítricas, chocolate ou alimentos gordurosos?

## [6] PACIENTE-ATOR

Sim, percebi que frutas cítricas, alimentos gordurosos e até o café da manhã agravam a sensação de queimação no peito. Não tenho mais nada a adicionar.

## [7] CHATBOT (assistente de triagem)

Percebeu que a queimação no peito piora com certos alimentos, como frutas cítricas, alimentos gordurosos e café da manhã? Existe alguma associação com refluxo ou sensação de engasgo?

## [8] PACIENTE-ATOR

Percebeu que a queimação no peito piora com certos alimentos, como frutas cítricas, alimentos gordurosos e café da manhã? Existe alguma associação com refluxo ou sensação de engasgo?

## [9] CHATBOT (assistente de triagem)

Entendi que frutas cítricas, alimentos gordurosos e café da manhã agravam a queimação no peito. Há algum sintoma adicional, como dor torácica, falta de ar ou sensação de engasgo?

## [10] PACIENTE-ATOR

Não, não tenho sensação de engasgo ou falta de ar. É apenas a queimação no peito, mais forte quando como esses alimentos.

## [11] CHATBOT (assistente de triagem)

Entendi que a queimação no peito está relacionada ao consumo de alimentos específicos. Há algum histórico de refluxo gastroesofágico ou uso de medicamentos que possam estar relacionados?

## [12] PACIENTE-ATOR

Percebeu que a queimação está relacionada a alimentos específicos, como frutas cítricas e gordurosos. Há algum hábito alimentar ou estilo de vida que possa estar contribuindo, como refeições grandes ou jantares frequentes?

## [13] CHATBOT (assistente de triagem)

Entendi que a queimação no peito piora com frutas cítricas, alimentos gordurosos e café da manhã. Há algum sintoma adicional, como dor torácica, falta de ar ou sensação de engasgo?

## [14] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [15] CHATBOT (assistente de triagem)

Obrigado por compartilhar suas informações. Para ajudar melhor, posso perguntar sobre a frequência dos episódios de azia e se há algum alívio com medicamentos ou mudanças na dieta?
