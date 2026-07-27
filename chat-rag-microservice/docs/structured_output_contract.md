# Contrato de saída estruturada do LLM de triagem

Toda resposta do LLM de triagem, em qualquer turno da conversa, deve ser um único objeto JSON (sem cercas de código Markdown, sem texto antes ou depois) com este formato:

```json
{
  "status": "ongoing",
  "message": "texto conversacional a ser exibido ao paciente",
  "specialty": null,
  "orientation": null,
  "risk_level": null
}
```

Quando a triagem é concluída:

```json
{
  "status": "diagnosis_concluded",
  "message": "texto de encerramento a ser exibido ao paciente",
  "specialty": "Cardiologia",
  "orientation": "resumo clínico objetivo para o médico que vai atender",
  "risk_level": "vermelho"
}
```

## Campos

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `status` | `"ongoing" \| "diagnosis_concluded"` | sim | Mesmo vocabulário já usado em `diagnosis_status` no restante do sistema. |
| `message` | `string` | sim | Texto a ser exibido ao paciente. Nunca deve conter o JSON bruto nem instruções internas. |
| `specialty` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Deve ser **exatamente** uma das 12 strings da lista fechada abaixo — nunca uma variação livre. |
| `orientation` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Resumo clínico objetivo para o médico, não para o paciente. |
| `risk_level` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Cor de risco do Protocolo de Manchester, **exatamente** uma destas 5 strings, minúsculas: `vermelho`, `laranja`, `amarelo`, `verde`, `azul` — nunca uma variação livre. O modelo deve basear essa classificação nas `[REGRAS DE TRIAGEM RECUPERADAS]` do turno (campo `cor`, vindo do ChromaDB em maiúsculas — a saída deve sempre ser em minúsculas). Nota: a base de regras Manchester/Maringá indexada não tem nenhum registro com `cor = AZUL`; para quadros não urgentes sem correspondência em nenhum fluxograma recuperado, o modelo deve usar julgamento clínico geral, não RAG. |
