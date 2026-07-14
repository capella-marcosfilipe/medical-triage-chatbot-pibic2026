# Contrato de saída estruturada do LLM de triagem

Toda resposta do LLM de triagem, em qualquer turno da conversa, deve ser um único objeto JSON (sem cercas de código Markdown, sem texto antes ou depois) com este formato:

```json
{
  "status": "ongoing",
  "message": "texto conversacional a ser exibido ao paciente",
  "specialty": null,
  "orientation": null
}
```

Quando a triagem é concluída:

```json
{
  "status": "diagnosis_concluded",
  "message": "texto de encerramento a ser exibido ao paciente",
  "specialty": "Cardiologia",
  "orientation": "resumo clínico objetivo para o médico que vai atender"
}
```

## Campos

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `status` | `"ongoing" \| "diagnosis_concluded"` | sim | Mesmo vocabulário já usado em `diagnosis_status` no restante do sistema. |
| `message` | `string` | sim | Texto a ser exibido ao paciente. Nunca deve conter o JSON bruto nem instruções internas. |
| `specialty` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Deve ser **exatamente** uma das 12 strings da lista fechada abaixo — nunca uma variação livre. |
| `orientation` | `string \| null` | sim (pode ser `null`) | Só preenchido quando `status = "diagnosis_concluded"`. Resumo clínico objetivo para o médico, não para o paciente. |
