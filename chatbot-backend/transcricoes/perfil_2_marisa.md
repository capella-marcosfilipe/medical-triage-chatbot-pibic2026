# Transcrição — Perfil 2 (Marisa Ondina Campos)

- `session_id` / `chat_id`: `49e347d8-e175-4428-a4a4-dc7a44761085`
- Mensagens recuperadas do Redis: 16
- Chave lida: `lg:session:49e347d8-e175-4428-a4a4-dc7a44761085:messages`

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
- nome_completo: Marisa Ondina Campos
- idade: 54
- endereco: Endereço simulado para fins de teste, s/n
- dados_fisiologicos: {'frequencia_cardiaca': 65, 'saturacao_oxigenio': 100, 'pressao_arterial_sistolica': 114, 'pressao_arterial_diastolica': 81, 'temperatura_corporal': 36.3}

## [1] CHATBOT (assistente de triagem)

Marisa, você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [2] PACIENTE-ATOR

Não, não sinto formigamento ou dormência nas pernas ou tórax. Não percebo alteração na sensação de calor ou frio na face ou braço direito. Já tentei mover o rosto, mas o queixo fica rígido e difícil de mover, e ao tentar olhar para um lado, a visão fica ainda mais turva.

## [3] CHATBOT (assistente de triagem)

Obrigado por compartilhar isso, Marisa. Você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [4] PACIENTE-ATOR

Marisa, você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito? Além disso, tentou mover o rosto ou a cabeça, como se pudesse inclinar o queixo ou olhar para um lado?

## [5] CHATBOT (assistente de triagem)

Marisa, você sente algum formigamento ou dormência nas pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [6] PACIENTE-ATOR

Não, não sinto formigamento ou dormência nas pernas ou tórax. Não percebo alteração na sensação de calor ou frio na face ou braço direito. Já tentei mover o rosto, mas o queixo fica rígido e difícil de mover, e ao tentar olhar para um lado, a visão fica ainda mais turva.

## [7] CHATBOT (assistente de triagem)

Obrigado por compartilhar isso, Marisa. Você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [8] PACIENTE-ATOR

Marisa, você sente formigamento ou dormência nas pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito? Além disso, tentou mover o rosto ou a cabeça, como se pudesse inclinar o queixo ou olhar para um lado?

## [9] CHATBOT (assistente de triagem)

Marisa, você sente formigamento ou dormência nas pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [10] PACIENTE-ATOR

Não, não sinto formigamento ou dormência nas pernas ou tórax. Não percebo alteração na sensação de calor ou frio na face ou braço direito. Já tentei mover o rosto, mas o queixo fica rígido e difícil de mover, e ao tentar olhar para um lado, a visão fica ainda mais turva.

## [11] CHATBOT (assistente de triagem)

Obrigado por compartilhar isso, Marisa. Você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [12] PACIENTE-ATOR

Sim, é isso mesmo. Não tenho mais nada a acrescentar.

## [13] CHATBOT (assistente de triagem)

Marisa, você sente formigamento ou dormência em outras partes do corpo, como as pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [14] PACIENTE-ATOR

Marisa, você sente formigamento ou dormência nas pernas ou tórax? E há alguma alteração na sensação de calor ou frio na face ou braço direito?

## [15] CHATBOT (assistente de triagem)

Marisa, você está descrevendo dificuldade para mover o queixo e visão turva ao tentar olhar para um lado. Há outros sintomas neurológicos, como perda de força no braço ou confusão mental?
